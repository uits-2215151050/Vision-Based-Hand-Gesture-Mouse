"""
MagicHand Camera Server
Serves the mobile webapp and receives MJPEG frames from mobile devices
"""

import os
from flask import Flask, request, send_from_directory, jsonify
import threading
import socket
import qrcode
from io import BytesIO
import base64
import time

class CameraServer:
    def __init__(self, port=5000):
        # Get absolute path to webapp folder
        self.webapp_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webapp'))
        self.app = Flask(__name__, static_folder=self.webapp_folder)
        self.port = port
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_timestamp = 0
        self.server_thread = None
        self.running = False
        self.frame_count = 0  # Track total frames received
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Serve the mobile webapp"""
            return send_from_directory(self.webapp_folder, 'index.html')
        
        @self.app.route('/<path:path>')
        def serve_static(path):
            """Serve static files"""
            return send_from_directory(self.webapp_folder, path)
        
        @self.app.route('/upload_frame', methods=['POST'])
        def upload_frame():
            """Receive frame from mobile device"""
            try:
                if 'frame' not in request.files:
                    print("[Camera Server] ERROR: No frame in request")
                    return jsonify({'error': 'No frame provided'}), 400
                
                frame_file = request.files['frame']
                frame_data = frame_file.read()
                
                # Store frame with timestamp
                with self.frame_lock:
                    self.latest_frame = frame_data
                    self.frame_timestamp = time.time()
                    self.frame_count += 1
                    
                    # Log every 30 frames to avoid spam
                    if self.frame_count % 30 == 0:
                        print(f"[Camera Server] Received {self.frame_count} frames, latest size: {len(frame_data)} bytes")
                
                return jsonify({'status': 'ok'}), 200
            
            except Exception as e:
                print(f"[Camera Server] ERROR uploading frame: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status')
        def status():
            """Get server status"""
            with self.frame_lock:
                has_frame = self.latest_frame is not None
                age = time.time() - self.frame_timestamp if has_frame else 0
            
            return jsonify({
                'running': True,
                'has_frame': has_frame,
                'frame_age': age,
                'frame_count': self.frame_count
            })
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def generate_qr_code(self, connection_mode='wifi'):
        """Generate QR code for mobile connection
        
        Args:
            connection_mode: 'wifi' for local network, 'usb' for USB/ADB forwarding
        """
        if connection_mode == 'usb':
            url = f"http://localhost:{self.port}"
        else:
            ip = self.get_local_ip()
            url = f"http://{ip}:{self.port}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64, url
    
    def get_latest_frame(self):
        """Get the latest frame from mobile device"""
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            
            # Check if frame is too old (>2 seconds)
            age = time.time() - self.frame_timestamp
            if age > 2.0:
                return None
            
            return self.latest_frame
    
    def start(self):
        """Start the server in a background thread"""
        if self.running:
            print("[Camera Server] Already running")
            return
        
        ip = self.get_local_ip()
        print(f"[Camera Server] Starting server on {ip}:{self.port}")
        print(f"[Camera Server] Mobile devices should connect to: http://{ip}:{self.port}")
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
    
    def _run_server(self):
        """Run Flask server"""
        # Disable Flask logging
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        print(f"[Camera Server] Flask server starting on 0.0.0.0:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
    
    def stop(self):
        """Stop the server"""
        self.running = False
        # Note: Flask doesn't have a clean shutdown method
        # The thread will terminate when the app exits

# Singleton instance
_server_instance = None

def get_server(port=5000):
    """Get or create server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = CameraServer(port)
    return _server_instance
