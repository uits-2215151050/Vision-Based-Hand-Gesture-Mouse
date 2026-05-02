// MagicHand Mobile Camera App
class MagicHandCamera {
    constructor() {
        this.video = document.getElementById('videoElement');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.overlay = document.getElementById('overlay');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = this.statusIndicator.querySelector('.status-text');

        // Controls
        this.cameraSelect = document.getElementById('cameraSelect');
        this.qualitySelect = document.getElementById('qualitySelect');
        this.fpsSelect = document.getElementById('fpsSelect');
        this.startButton = document.getElementById('startButton');
        this.stopButton = document.getElementById('stopButton');

        // Stats
        this.fpsValue = document.getElementById('fpsValue');
        this.latencyValue = document.getElementById('latencyValue');
        this.sentValue = document.getElementById('sentValue');

        // State
        this.stream = null;
        this.streaming = false;
        this.frameCount = 0;
        this.lastFrameTime = Date.now();
        this.serverUrl = this.getServerUrl();

        this.init();
    }

    getServerUrl() {
        // Get server URL from query params or use current host
        const params = new URLSearchParams(window.location.search);
        const serverIp = params.get('server') || window.location.hostname;
        const serverPort = params.get('port') || '5000';
        return `http://${serverIp}:${serverPort}`;
    }

    async init() {
        // Setup event listeners
        this.startButton.addEventListener('click', () => this.start());
        this.stopButton.addEventListener('click', () => this.stop());
        this.cameraSelect.addEventListener('change', () => this.switchCamera());
        this.qualitySelect.addEventListener('change', () => this.switchCamera());

        // Switch Camera Button
        document.getElementById('switchCamBtn').addEventListener('click', () => this.toggleCamera());

        // Enumerate cameras
        await this.enumerateCameras();

        // Prevent screen sleep
        this.preventSleep();
    }

    async enumerateCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');

            this.cameraSelect.innerHTML = '';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${index + 1}`;
                this.cameraSelect.appendChild(option);
            });

            if (videoDevices.length === 0) {
                this.cameraSelect.innerHTML = '<option>No cameras found</option>';
            }
        } catch (error) {
            console.error('Error enumerating cameras:', error);
            this.cameraSelect.innerHTML = '<option>Error detecting cameras</option>';
        }
    }

    getConstraints() {
        const quality = this.qualitySelect.value;
        const fps = parseInt(this.fpsSelect.value);

        const resolutions = {
            'qvga': { width: 320, height: 240 },
            'vga': { width: 640, height: 480 },
            'hd': { width: 1280, height: 720 },
            'fhd': { width: 1920, height: 1080 }
        };

        const resolution = resolutions[quality];

        return {
            video: {
                deviceId: this.cameraSelect.value ? { exact: this.cameraSelect.value } : undefined,
                width: { ideal: resolution.width },
                height: { ideal: resolution.height },
                frameRate: { ideal: fps },
                facingMode: 'environment' // Prefer back camera
            },
            audio: false
        };
    }

    async start() {
        try {
            // Get camera stream
            this.stream = await navigator.mediaDevices.getUserMedia(this.getConstraints());
            this.video.srcObject = this.stream;

            // Wait for video to be ready
            await new Promise(resolve => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    resolve();
                };
            });

            // Setup canvas
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;

            // Hide overlay
            this.overlay.classList.add('hidden');

            // Update UI
            this.startButton.style.display = 'none';
            this.stopButton.style.display = 'flex';
            this.updateStatus('connected', 'Streaming');

            // Start streaming
            this.streaming = true;
            this.streamLoop();

        } catch (error) {
            console.error('Error starting camera:', error);
            alert('Failed to access camera. Please check permissions.');
            this.updateStatus('disconnected', 'Error');
        }
    }

    async stop() {
        this.streaming = false;

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.video.srcObject = null;
        this.overlay.classList.remove('hidden');

        // Update UI
        this.startButton.style.display = 'flex';
        this.stopButton.style.display = 'none';
        this.updateStatus('disconnected', 'Disconnected');

        // Reset stats
        this.fpsValue.textContent = '0';
        this.latencyValue.textContent = '0ms';
    }

    async switchCamera() {
        if (this.streaming) {
            await this.stop();
            await this.start();
        }
    }

    async toggleCamera() {
        const select = this.cameraSelect;
        if (select.options.length <= 1) return;

        let newIndex = select.selectedIndex + 1;
        if (newIndex >= select.options.length) {
            newIndex = 0;
        }

        select.selectedIndex = newIndex;
        await this.switchCamera();
    }

    async streamLoop() {
        const fps = parseInt(this.fpsSelect.value);
        const frameInterval = 1000 / fps;

        while (this.streaming) {
            const startTime = Date.now();

            try {
                // Capture frame
                this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

                // Quality setting based on resolution
                let jpegQuality = 0.8;
                const qualitySetting = this.qualitySelect.value;
                if (qualitySetting === 'qvga') jpegQuality = 0.5;
                if (qualitySetting === 'vga') jpegQuality = 0.6;

                // Convert to JPEG blob
                const blob = await new Promise(resolve => {
                    this.canvas.toBlob(resolve, 'image/jpeg', jpegQuality);
                });

                // Send to server
                const sendStart = Date.now();
                await this.sendFrame(blob);
                const latency = Date.now() - sendStart;

                // Update stats
                this.frameCount++;
                this.updateStats(latency);

            } catch (error) {
                console.error('Error streaming frame:', error);
                this.updateStatus('error', 'Connection Lost');

                // Try to reconnect after 2 seconds
                await new Promise(resolve => setTimeout(resolve, 2000));
                this.updateStatus('connected', 'Reconnecting...');
            }

            // Maintain frame rate
            const elapsed = Date.now() - startTime;
            const delay = Math.max(0, frameInterval - elapsed);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    async sendFrame(blob) {
        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');

        const response = await fetch(`${this.serverUrl}/upload_frame`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
    }

    updateStats(latency) {
        const now = Date.now();
        const timeDiff = (now - this.lastFrameTime) / 1000;

        if (timeDiff >= 1) {
            const fps = Math.round(this.frameCount / timeDiff);
            this.fpsValue.textContent = fps;
            this.frameCount = 0;
            this.lastFrameTime = now;
        }

        this.latencyValue.textContent = `${latency}ms`;
        this.sentValue.textContent = this.formatBytes(this.frameCount * 50000); // Approximate
    }

    updateStatus(status, text) {
        this.statusIndicator.className = `status-indicator ${status}`;
        this.statusText.textContent = text;
    }

    formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    preventSleep() {
        // Request wake lock to prevent screen from sleeping
        if ('wakeLock' in navigator) {
            navigator.wakeLock.request('screen').catch(err => {
                console.warn('Wake lock failed:', err);
            });
        }
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new MagicHandCamera();
    });
} else {
    new MagicHandCamera();
}
