# Broadcast Audio System

A proof-of-concept broadcast audio system for automatic camera switching based on real-time audio analysis. This system captures audio from a USB multitrack device, detects active microphones, and makes intelligent decisions about which camera to use.

## Features

### Audio Acquisition and Processing
- **USB Audio Capture**: Supports USB multitrack audio devices via PyAudio
- **Real-time Analysis**: Frame-by-frame audio processing for detecting sound levels
- **Volume-based Activity Detection**: Configurable thresholds for microphone activity
- **Multi-channel Support**: Monitor up to 16 microphone channels simultaneously

### Decision-Making Logic
The system handles three main scenarios:
1. **Single Speaker**: Automatically cuts to the corresponding camera
2. **No Speakers**: Defaults to a wide shot or idle camera after timeout
3. **Multiple Speakers**: Prioritizes based on configurable rules (first active or last active)

### Web Configuration Interface
- **Dashboard (`/`)**: Real-time display of system status, microphone activity, and current camera
- **Settings (`/settings`)**: Configure thresholds, camera mappings, and decision parameters
- **REST API**: Programmatic access to system status and configuration

## Installation

### Prerequisites
- Python 3.7+
- USB audio device (or run in simulation mode)
- PortAudio library (for PyAudio)

On Raspberry Pi or Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
```

### Setup
1. Clone the repository:
```bash
git clone https://github.com/AntonGyde/broadcast-audio-system-.git
cd broadcast-audio-system-
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Start the system with default settings:
```bash
python main.py
```

The web interface will be available at `http://localhost:5000`

### Command Line Options
```bash
python main.py --help
```

Options:
- `--config CONFIG`: Path to configuration file (default: config.json)
- `--host HOST`: Web interface host (default: 0.0.0.0)
- `--port PORT`: Web interface port (default: 5000)
- `--no-audio`: Run in simulation mode without audio device

### Simulation Mode
For testing without a USB audio device:
```bash
python main.py --no-audio
```

## Configuration

Settings are stored in `config.json` and can be modified through the web interface or directly in the file.

### Audio Settings
- `sample_rate`: Audio sampling rate (default: 44100 Hz)
- `chunk_size`: Buffer size in frames (default: 1024)
- `channels`: Number of microphone channels (default: 4)
- `device_index`: Specific audio device index (null = default device)

### Detection Thresholds
- `volume_threshold`: Minimum RMS volume to detect activity (default: 500)
- `min_active_frames`: Consecutive frames required before considering mic active (default: 3)

### Camera Configuration
- `default_camera`: Camera to use when no activity (default: "wide_shot")
- `camera_mappings`: Map each microphone channel to a camera name

### Decision Logic
- `priority_mode`: How to handle multiple active speakers
  - `first_active`: Use lowest microphone index
  - `last_active`: Maintain current camera if still active
- `idle_timeout_seconds`: Seconds before switching to default camera (default: 2)

## Web Interface

### Dashboard
The main dashboard displays:
- Current active camera
- Real-time microphone activity levels
- Audio device information
- System status and configuration

### Settings Page
Allows you to modify:
- Volume detection thresholds
- Default camera selection
- Priority mode for multiple speakers
- Idle timeout duration
- Audio hardware settings

### API Endpoints

**GET /api/status**
Returns current system status including audio analysis and camera decisions.

**POST /api/threshold**
Update volume threshold:
```json
{
  "volume_threshold": 500
}
```

**POST /api/camera**
Update default camera:
```json
{
  "default_camera": "wide_shot"
}
```

## Architecture

### Components

**audio_processor.py**
- Handles PyAudio initialization and stream management
- Processes audio frames and calculates RMS volume per channel
- Detects active microphones based on thresholds

**decision_logic.py**
- Implements camera switching logic
- Manages state for current camera and activity history
- Handles timeout for idle scenarios

**app.py**
- Flask web application
- Provides dashboard and settings interface
- REST API for status and configuration

**main.py**
- System coordinator
- Runs audio processing in background thread
- Integrates all components

## Limitations (Proof-of-Concept)

This is an initial proof-of-concept. The following are **not yet implemented**:
- Error handling for USB device disconnection
- Persistent logging
- Advanced audio analysis (frequency, direction)
- Physical camera control integration
- Video streaming integration
- User authentication
- Production-grade error recovery

## Development

### Project Structure
```
broadcast-audio-system-/
├── audio_processor.py      # Audio capture and analysis
├── decision_logic.py       # Camera switching logic
├── app.py                  # Flask web interface
├── main.py                 # Main entry point
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── templates/
│   ├── index.html         # Dashboard template
│   └── settings.html      # Settings template
└── README.md              # This file
```

### Key Libraries
- **PyAudio**: USB audio device access on Raspberry Pi
- **Flask**: Lightweight web interface framework
- **NumPy**: Efficient audio signal processing

## License

This is a proof-of-concept project for educational and development purposes.

## Contributing

This is an initial implementation. Contributions for error handling, additional features, and production hardening are welcome!