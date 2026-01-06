# Robot Voice Control System with Biometric Authentication

A secure, offline voice control system for robots that combines biometric voice authentication with speech recognition. This system uses Resemblyzer for voice authentication and Vosk for offline speech recognition, ensuring privacy and security without requiring internet connectivity.

## Features

- **Biometric Voice Authentication**: Uses Resemblyzer to verify the owner's voice before executing commands
- **Offline Speech Recognition**: Powered by Vosk, works completely offline without internet connection
- **Noise Filtering**: Intelligent noise filtering to reduce false positives
- **Robot Control**: Sends commands to robot via UDP protocol
- **Multi-language Support**: Currently supports Turkish language model (can be extended)

## Architecture

The system consists of three main components:

1. **Voice Enrollment** (`src/python/voice_enrollment.py`): Records and saves the owner's voice signature
2. **Voice Authenticator** (`src/python/voice_authenticator.py`): Tests voice recognition (for validation)
3. **Voice Control** (`src/python/voice_control.py`): Main system that authenticates voice and executes robot commands


## Requirements

- Python 3.7+
- Vosk Turkish language model (included in `model/` directory)
- Microphone with proper audio drivers
- Network connection to robot (UDP)
- C++ compiler (for C++ components, optional)


The system will:
1. Listen for audio input
2. Filter out noise and silence
3. Authenticate the voice against the enrolled signature
4. Recognize speech commands
5. Send commands to the robot via UDP


## Configuration

### Option 1: Edit Configuration in Code

Edit the configuration section in `src/python/voice_control.py`:

```python
# Robot network settings
ROBOT_IP = "192.168.1.120"
ROBOT_PORT = 5001

# Audio device settings
AUDIO_DEVICE_ID = 0  # 0 = default microphone

# Security settings
SIMILARITY_THRESHOLD = 0.75  # Voice match threshold (0.0-1.0)
NOISE_THRESHOLD = 0.02       # RMS threshold for noise filtering
RECORDING_DURATION = 3       # Recording duration in seconds
```

### Option 2: Use Configuration File (Recommended)

1. Copy the example configuration file:
   ```bash
   cp config/config.example.py config/config.py
   ```

2. Edit `config/config.py` with your settings

3. Modify `src/python/voice_control.py` to import from `config/config.py` (optional enhancement)

### Adjusting Sensitivity

- **Very sensitive** (captures whispers): `NOISE_THRESHOLD = 0.01`
- **Medium** (normal speech): `NOISE_THRESHOLD = 0.05`
- **Low sensitivity** (requires loud speech): `NOISE_THRESHOLD = 0.10`
- **Noisy environment**: `NOISE_THRESHOLD = 0.03` or `0.04`

## Supported Commands

The system recognizes the following Turkish voice commands:

| Command | Robot Action | UDP Code |
|---------|-------------|----------|
| "kalk" / "ayağa" | Stand up | `K` |
| "otur" / "yat" | Sit down | `O` |
| "ileri" / "yürü" | Move forward | `I` |
| "dur" / "bekle" | Stop | `0` |
| "selam" | Greeting | `H` |

## C++ Components

The project also includes C++ components for robot control:

- `src/cpp/robot_main.cpp`: Robot motion controller that receives UDP commands
- `src/cpp/main.cpp`: Alternative C++ implementation with Vosk integration

### Building C++ Components

```bash
cd src/cpp
# Requires Vosk C++ API and PortAudio
g++ -o robot_controller robot_main.cpp -I../../include -lvosk -lportaudio
```



