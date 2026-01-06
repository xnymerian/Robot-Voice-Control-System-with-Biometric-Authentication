"""
Voice Enrollment Module
=======================
Records and saves the owner's voice signature for biometric authentication.
This module is used to create the initial voice profile that will be used
for authentication in the voice control system.
"""

import sounddevice as sd
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import os
import sys

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuration
SAMPLE_RATE = 16000  # Resemblyzer typically uses 16kHz
RECORDING_DURATION = 30  # Duration in seconds for voice enrollment
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "owner_voice_signature.npy")


def record_voice(duration: int, sample_rate: int) -> np.ndarray:
    """
    Record audio from the default microphone.
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Recorded audio data as numpy array
    """
    print(f"Recording {duration} seconds of audio...")
    print("Please speak clearly (e.g., 'I am the owner, listen to my commands').")
    print("RECORDING STARTED!")
    
    try:
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1)
        sd.wait()
        recording = np.squeeze(recording)
        print("Recording completed. Processing...")
        return recording
    except Exception as e:
        print(f"Error during recording: {e}")
        sys.exit(1)


def extract_voice_signature(audio_data: np.ndarray, encoder: VoiceEncoder) -> np.ndarray:
    """
    Extract voice signature (embedding) from audio data.
    
    Args:
        audio_data: Raw audio data as numpy array
        encoder: VoiceEncoder instance for processing
        
    Returns:
        Voice signature vector as numpy array
    """
    try:
        # Preprocess audio (noise reduction, normalization, etc.)
        processed_audio = preprocess_wav(audio_data)
        
        # Extract voice signature vector
        voice_signature = encoder.embed_utterance(processed_audio)
        return voice_signature
    except Exception as e:
        print(f"Error processing audio: {e}")
        sys.exit(1)


def save_signature(signature: np.ndarray, filepath: str) -> None:
    """
    Save voice signature to disk.
    
    Args:
        signature: Voice signature vector
        filepath: Path to save the signature file
    """
    try:
        np.save(filepath, signature)
        print(f"Voice signature saved to '{filepath}'")
    except Exception as e:
        print(f"Error saving signature: {e}")
        sys.exit(1)


def main():
    """Main enrollment function."""
    print("=" * 50)
    print("Voice Enrollment System")
    print("=" * 50)
    print("Loading voice encoder model...")
    print("(This may take a moment on first run)")
    
    try:
        encoder = VoiceEncoder()
    except Exception as e:
        print(f"Error loading encoder: {e}")
        sys.exit(1)
    
    # Record voice
    audio_data = record_voice(RECORDING_DURATION, SAMPLE_RATE)
    
    # Extract signature
    signature = extract_voice_signature(audio_data, encoder)
    
    # Save signature
    save_signature(signature, OUTPUT_FILE)
    
    print("=" * 50)
    print("ENROLLMENT SUCCESSFUL!")
    print(f"Your voice signature has been saved to '{OUTPUT_FILE}'")
    print("You can now use the voice control system.")
    print("=" * 50)


if __name__ == "__main__":
    main()

