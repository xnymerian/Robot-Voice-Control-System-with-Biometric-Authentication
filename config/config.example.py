"""
Configuration Example File
==========================
Copy this file to config.py and modify the values according to your setup.
"""

# Robot Network Configuration
ROBOT_IP = "192.168.1.120"
ROBOT_PORT = 5001

# Audio Device Configuration
AUDIO_DEVICE_ID = 0  # 0 = default microphone
# To find your microphone device ID, run:
# python -c "import sounddevice; print(sounddevice.query_devices())"

# Security Settings
SIMILARITY_THRESHOLD = 0.75  # Voice authentication threshold (0.0-1.0)
# Higher values = more strict authentication
# Lower values = more lenient authentication

# Audio Processing Settings
RECORDING_DURATION = 3  # Recording duration in seconds
NOISE_THRESHOLD = 0.02  # RMS threshold for noise filtering
# 0.01 = Very sensitive (captures whispers, may capture noise)
# 0.05 = Medium (normal speech)
# 0.10 = Low sensitivity (requires loud speech)
# 0.03-0.04 = Recommended for noisy environments

# Model Paths
MODEL_PATH = "model"  # Path to Vosk model directory
SIGNATURE_FILE = "owner_voice_signature.npy"  # Voice signature file

# Sample Rate (typically 16000 for Resemblyzer and Vosk)
SAMPLE_RATE = 16000

