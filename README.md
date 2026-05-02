# MagicHand - AI-Powered Gesture Control System

**Transform your hand movements into precise computer control using advanced computer vision and machine learning.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🌟 Overview

MagicHand is a sophisticated gesture recognition application that enables hands-free computer control through real-time hand tracking. Built with MediaPipe's state-of-the-art hand landmark detection and optimized for performance, it provides a seamless alternative to traditional mouse and keyboard input.

### Key Capabilities
- **Real-time Hand Tracking**: Sub-50ms latency using MediaPipe's optimized models
- **Multi-Modal Control**: Navigation, Presentation, and Calibration modes
- **Mobile Camera Support**: Use smartphone cameras via WiFi streaming
- **Personalized Calibration**: Adaptive hand range mapping for ergonomic control
- **Production-Ready**: Packaged as standalone Windows executable with installer
- **Machine Learning Integration**: Random Forest classifier for advanced gesture recognition

## 🚀 Quick Start

### Using the Pre-built Installer (Recommended)
1. Download `MagicHandSetup.exe` from the releases
2. Run the installer and follow the setup wizard
3. Launch MagicHand from your desktop or Start menu
4. Select your camera source and start controlling!

### Running from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd gesture_control

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## 🎮 How It Works

### Core Architecture
MagicHand employs a multi-threaded producer-consumer architecture for optimal performance:

- **Camera Thread**: Continuous frame capture with frame dropping for smooth operation
- **Processing Thread**: MediaPipe inference and gesture analysis
- **Main Thread**: UI updates and low-latency input simulation using Windows ctypes

### Gesture Recognition Pipeline
1. **Hand Detection**: MediaPipe Hand Landmarker identifies 21 hand landmarks in real-time
2. **Coordinate Mapping**: ROI interpolation maps hand positions to screen coordinates
3. **Motion Smoothing**: Exponential Moving Average (EMA) filter eliminates cursor jitter
4. **Gesture Classification**: Heuristic rules + optional ML model for complex gestures
5. **Action Dispatch**: Mode-specific gesture-to-action mapping with input simulation

## 🎯 Control Modes

### Navigation Mode
Full mouse replacement with intuitive gestures:
- **Hand Movement**: Smooth cursor control
- **Thumb + Index Pinch**: Left click
- **Thumb + Middle Pinch**: Right click
- **Thumb + Pinky Pinch**: Vertical scrolling
- **Three-Finger Pinch**: Freeze cursor
- **Swipe Gestures**: Browser navigation (with ML model)

### Presentation Mode
Optimized for slide control:
- **Index + Middle Pinch**: Next slide
- **Thumb + Index Pinch**: Previous slide
- **Swipe Left/Right**: Slide navigation
- **Cooldown Protection**: Prevents accidental rapid switching

### Calibration Mode
Personalized setup wizard:
- Define your comfortable hand movement range
- Map to full screen coordinates
- Persistent settings saved to `calibration.json`

## 📱 Mobile Camera Support

Transform your smartphone into a high-quality webcam:

1. Select "Mobile Camera" in the app
2. Scan the displayed QR code with your phone
3. Allow camera access in your mobile browser
4. Start streaming for enhanced tracking flexibility

**Requirements**: Same WiFi network, modern mobile browser

## 🧠 Machine Learning Integration

### Current Implementation
- **Random Forest Classifier**: Trained on MediaPipe landmark features
- **Gesture Classes**: SwipeLeft, SwipeRight, Palm, Fist, etc.
- **Real-time Inference**: Integrated into gesture pipeline

### Advanced NN Architecture (Available)
The project includes specifications for a CNN+LSTM model:
- **CNN Feature Extractor**: 4-layer convnet with global average pooling
- **LSTM Temporal Modeling**: Bidirectional sequence learning
- **Real-time Optimization**: TensorFlow Lite conversion with quantization

## 🛠️ Technical Implementation

### Performance Optimizations
- **Zero-Copy Pipeline**: Direct NumPy array to MediaPipe Image conversion
- **Multi-Threading**: Producer-consumer pattern prevents UI freezing
- **Low-Level Input**: ctypes User32.dll calls for minimal latency
- **Memory Management**: Proper image reference handling prevents crashes

### Key Algorithms
- **EMA Smoothing**: α=0.15 for optimal cursor stability
- **ROI Interpolation**: Linear mapping with boundary clamping
- **Velocity-Based Swipes**: Temporal analysis with cooldown protection

### Build System
- **PyInstaller**: Single-executable packaging
- **Inno Setup**: Professional Windows installer
- **Automated Build**: `build.py` script with icon generation

## 📊 Dataset & Training

### Included Dataset
- **6 Gesture Classes**: LeftClick, Palm, PointerFreeze, ScrollDown, ScrollUp, SwipeLeft, SwipeRight
- **16 Sequences per Class**: Captured with data collection GUI
- **MediaPipe Landmarks**: 42 features (x,y coordinates) per frame

### Training Pipeline
```bash
python training/train_model.py  # Trains Random Forest on landmarks
```

## 🏗️ Project Structure

```
gesture_control/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── calibration.json        # User calibration settings
├── hand_landmarker.task    # MediaPipe model file
├── build.py               # Build automation script
├── MagicHand.spec         # PyInstaller configuration
├── installer.iss          # Inno Setup script
├── version_info.txt       # Version metadata
│
├── core/                  # Core business logic
│   ├── gesture_engine.py  # Hand tracking & gesture detection
│   ├── input_controller.py # Input simulation
│   ├── mode_manager.py    # Mode switching logic
│   └── action_dispatcher.py # Gesture-to-action mapping
│
├── gui/                   # User interface
│   ├── main_window.py     # Main application window
│   ├── data_collector_window.py # Dataset collection tool
│   └── __init__.py
│
├── camera/                # Camera management
│   ├── camera.py          # Local & network camera support
│   ├── camera_server.py  # Flask server for mobile streaming
│   └── __init__.py
│
├── training/              # ML model training
│   ├── train_model.py     # Random Forest training
│   ├── gesture_model.py   # Model loading utilities
│   ├── gesture_rf_model.joblib # Trained model
│   └── data_collector.py  # Dataset collection
│
├── utils/                 # Utilities
│   ├── calibration_manager.py # Calibration persistence
│   ├── fast_smoothing.py  # EMA smoothing implementation
│   └── util.py            # Helper functions
│
├── dataset/               # Training data
│   ├── LeftClick/         # Gesture sequence folders
│   ├── Palm/
│   └── ...
│
├── webapp/                # Mobile camera interface
│   ├── index.html         # Mobile web app
│   ├── style.css          # Responsive styling
│   └── app.js             # MJPEG streaming logic
│
└── all about project/     # Documentation
    ├── project_summary.md
    ├── technical_summary.md
    ├── NN_implement.md
    ├── production.md
    ├── USER_GUIDE.md
    └── README.md
```

## 📋 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.8+ (for source builds)
- **RAM**: 4GB minimum, 8GB recommended
- **Camera**: Webcam with 640x480 resolution minimum
- **Network**: WiFi connection (for mobile camera)

## 🤝 Contributing

This project demonstrates advanced computer vision, real-time systems, and ML integration. Key areas for contribution:

- **Performance Optimization**: Further latency reductions
- **Cross-Platform Support**: Linux/Mac compatibility
- **Advanced ML Models**: CNN+LSTM implementation
- **Additional Gestures**: Expand gesture vocabulary
- **Accessibility Features**: Enhanced usability options

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **MediaPipe**: Google's hand tracking technology
- **OpenCV**: Computer vision foundation
- **CustomTkinter**: Modern GUI framework
- **Scikit-learn**: Machine learning utilities

---

**Built with ❤️ for hands-free computing innovation**</content>
<parameter name="filePath">d:\Capstone\gesture_control\README.md
