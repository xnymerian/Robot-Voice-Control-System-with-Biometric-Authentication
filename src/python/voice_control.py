"""
Voice Control System for Robot
===============================
Main voice control module that combines voice authentication with
speech recognition to control a robot via voice commands.

Features:
- Biometric voice authentication using Resemblyzer
- Speech recognition using Vosk (offline)
- Noise filtering to reduce false positives
- UDP command transmission to robot
"""

import sounddevice as sd
from resemblyzer import VoiceEncoder, preprocess_wav
from vosk import Model, KaldiRecognizer
import numpy as np
import socket
import json
import sys
import os
from typing import Optional, Tuple

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== CONFIGURATION ====================
ROBOT_IP = "192.168.1.120"
ROBOT_PORT = 5001
MODEL_PATH = os.path.join(PROJECT_ROOT, "model")
SIGNATURE_FILE = os.path.join(PROJECT_ROOT, "owner_voice_signature.npy")

# Audio device settings
AUDIO_DEVICE_ID = 0  # Set to your microphone device ID (0 = default)

# Security and sensitivity settings
SIMILARITY_THRESHOLD = 0.75  # Voice authentication threshold
RECORDING_DURATION = 3  # Recording duration in seconds
NOISE_THRESHOLD = 0.02  # RMS threshold for noise filtering
# 0.01 = Very sensitive (captures whispers, may capture noise)
# 0.05 = Medium (normal speech)
# 0.10 = Low sensitivity (requires loud speech)
# Adjust to 0.03-0.04 if environment is noisy

# Audio settings
SAMPLE_RATE = 16000

# Command mappings (Turkish to robot commands)
COMMAND_MAPPINGS = {
    "kalk": 'K',      # Stand up
    "ayağa": 'K',     # Stand up (alternative)
    "otur": 'O',      # Sit down
    "yat": 'O',       # Lie down
    "ileri": 'I',     # Move forward
    "yürü": 'I',      # Walk
    "dur": '0',       # Stop
    "bekle": '0',     # Wait
    "selam": 'H',     # Hello/Greeting
}


def load_voice_signature(filepath: str) -> np.ndarray:
    """
    Load the owner's voice signature.
    
    Args:
        filepath: Path to signature file
        
    Returns:
        Voice signature vector
        
    Raises:
        SystemExit: If signature file doesn't exist
    """
    if not os.path.exists(filepath):
        print(f"ERROR: '{filepath}' not found.")
        print("Please run voice_enrollment.py first to create your voice signature.")
        sys.exit(1)
    return np.load(filepath)


def calculate_rms(audio_data: np.ndarray) -> float:
    """
    Calculate Root Mean Square (RMS) of audio signal.
    Used for noise filtering.
    
    Args:
        audio_data: Audio signal as numpy array
        
    Returns:
        RMS value
    """
    return np.sqrt(np.mean(audio_data**2))


def send_command(sock: socket.socket, command: str, robot_ip: str, robot_port: int) -> None:
    """
    Send command to robot via UDP.
    
    Args:
        sock: UDP socket
        command: Single character command
        robot_ip: Robot IP address
        robot_port: Robot port number
    """
    try:
        sock.sendto(command.encode(), (robot_ip, robot_port))
        print(f"COMMAND SENT: {command}")
    except Exception as e:
        print(f"Error sending command: {e}")


def authenticate_voice(audio_data: np.ndarray, encoder: VoiceEncoder, 
                      owner_signature: np.ndarray, threshold: float) -> Tuple[bool, float]:
    """
    Authenticate voice by comparing against owner signature.
    
    Args:
        audio_data: Raw audio data
        encoder: VoiceEncoder instance
        owner_signature: Owner's voice signature
        threshold: Similarity threshold
        
    Returns:
        Tuple of (is_authenticated, similarity_score)
    """
    try:
        processed_audio = preprocess_wav(audio_data)
    except Exception:
        return False, 0.0
    
    try:
        current_signature = encoder.embed_utterance(processed_audio)
        similarity = np.inner(owner_signature, current_signature)
        return similarity >= threshold, similarity
    except Exception:
        return False, 0.0


def recognize_speech(audio_data: np.ndarray, model: Model, sample_rate: int) -> Optional[str]:
    """
    Recognize speech from audio using Vosk.
    
    Args:
        audio_data: Raw audio data (float32, normalized)
        model: Vosk model instance
        sample_rate: Audio sample rate
        
    Returns:
        Recognized text or None if recognition failed
    """
    # Convert to int16 format required by Vosk
    audio_int16 = (audio_data * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.AcceptWaveform(audio_bytes)
    result = json.loads(recognizer.FinalResult())
    
    return result.get('text', '').strip() or None


def process_command(text: str, sock: socket.socket, robot_ip: str, robot_port: int) -> None:
    """
    Process recognized command and send to robot.
    
    Args:
        text: Recognized text
        sock: UDP socket
        robot_ip: Robot IP address
        robot_port: Robot port number
    """
    text_lower = text.lower()
    
    for keyword, command in COMMAND_MAPPINGS.items():
        if keyword in text_lower:
            send_command(sock, command, robot_ip, robot_port)
            return
    
    print("Command not recognized.")


def main():
    """Main voice control loop."""
    print("Loading Biometric Security System...")
    
    # Load voice signature
    owner_signature = load_voice_signature(SIGNATURE_FILE)
    
    # Initialize voice encoder
    print("-> Loading Resemblyzer (Voice Signature Engine)...")
    try:
        encoder = VoiceEncoder()
    except Exception as e:
        print(f"Error loading encoder: {e}")
        sys.exit(1)
    
    # Initialize Vosk model
    print("-> Loading Vosk (Speech Recognition Engine)...")
    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        print(f"Error loading Vosk model: {e}")
        print(f"Make sure '{MODEL_PATH}' directory exists and contains a valid Vosk model.")
        sys.exit(1)
    
    # Initialize UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("\n" + "=" * 50)
    print("FULL SECURITY MODE (Noise Filter Enabled)")
    print(f"Microphone: Device ID {AUDIO_DEVICE_ID}")
    print(f"Noise Threshold: {NOISE_THRESHOLD}")
    print(f"Similarity Threshold: {SIMILARITY_THRESHOLD}")
    print("=" * 50)
    
    try:
        while True:
            print("\nListening...", end=" ", flush=True)
            
            # Step 1: Record audio
            try:
                recording = sd.rec(int(RECORDING_DURATION * SAMPLE_RATE),
                                  samplerate=SAMPLE_RATE,
                                  channels=1,
                                  device=AUDIO_DEVICE_ID)
                sd.wait()
            except Exception as e:
                print(f"\nMICROPHONE ERROR: {e}")
                break
            
            recording = np.squeeze(recording)
            
            # Step 1.5: Noise filtering
            rms = calculate_rms(recording)
            if rms < NOISE_THRESHOLD:
                print(f"(Silence/Noise - Level: {rms:.4f})")
                continue
            
            print(f"Audio Detected ({rms:.4f}) -> Starting Analysis...")
            
            # Step 2: Voice authentication
            is_authenticated, similarity = authenticate_voice(
                recording, encoder, owner_signature, SIMILARITY_THRESHOLD
            )
            
            print(f"Identity Score: {similarity:.2f}")
            
            if not is_authenticated:
                print("DENIED: Unauthorized voice.")
                continue
            
            # Step 3: Speech recognition
            print("AUTHORIZED. Recognizing command...")
            recognized_text = recognize_speech(recording, model, SAMPLE_RATE)
            
            if recognized_text:
                print(f"COMMAND: '{recognized_text}'")
                process_command(recognized_text, sock, ROBOT_IP, ROBOT_PORT)
            else:
                print("Speech could not be converted to text.")
                
    except KeyboardInterrupt:
        print("\nSystem shutdown complete.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()

