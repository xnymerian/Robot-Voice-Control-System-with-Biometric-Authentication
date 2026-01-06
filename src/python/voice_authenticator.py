"""
Voice Authentication Module
===========================
Tests voice recognition by comparing recorded audio against the owner's
voice signature. Used for testing and validation purposes.
"""

import sounddevice as sd
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import sys
import os

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuration
SAMPLE_RATE = 16000
RECORDING_DURATION = 3  # Duration for each test recording
SIGNATURE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "owner_voice_signature.npy")
SIMILARITY_THRESHOLD = 0.75  # Threshold for voice match


def load_owner_signature(filepath: str) -> np.ndarray:
    """
    Load the owner's voice signature from disk.
    
    Args:
        filepath: Path to the signature file
        
    Returns:
        Voice signature vector
        
    Raises:
        FileNotFoundError: If signature file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"ERROR: '{filepath}' not found! "
            "Please run voice_enrollment.py first to create your voice signature."
        )
    return np.load(filepath)


def record_audio(duration: int, sample_rate: int) -> np.ndarray:
    """
    Record audio from the default microphone.
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Recorded audio data as numpy array
    """
    recording = sd.rec(int(duration * sample_rate), 
                      samplerate=sample_rate, 
                      channels=1)
    sd.wait()
    return np.squeeze(recording)


def calculate_similarity(signature1: np.ndarray, signature2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two voice signatures.
    
    Args:
        signature1: First voice signature vector
        signature2: Second voice signature vector
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    return np.inner(signature1, signature2)


def main():
    """Main authentication test function."""
    print("=" * 50)
    print("Voice Authentication Test System")
    print("=" * 50)
    
    # Load encoder
    try:
        encoder = VoiceEncoder()
    except Exception as e:
        print(f"Error loading encoder: {e}")
        sys.exit(1)
    
    # Load owner signature
    try:
        owner_signature = load_owner_signature(SIGNATURE_FILE)
        print(f"Owner signature loaded from '{SIGNATURE_FILE}'")
    except FileNotFoundError as e:
        print(f"{e}")
        sys.exit(1)
    
    print(f"Listening started! (Press Ctrl+C to exit)")
    print(f"Similarity threshold: {SIMILARITY_THRESHOLD}")
    print("-" * 50)
    
    try:
        while True:
            print("Listening...", end=" ", flush=True)
            
            # Record audio
            audio_data = record_audio(RECORDING_DURATION, SAMPLE_RATE)
            
            # Process audio
            try:
                processed_audio = preprocess_wav(audio_data)
            except Exception as e:
                print(f"Audio processing error: {e}")
                continue
            
            # Extract signature
            try:
                current_signature = encoder.embed_utterance(processed_audio)
            except Exception as e:
                print(f"Signature extraction error: {e}")
                continue
            
            # Calculate similarity
            similarity = calculate_similarity(owner_signature, current_signature)
            print(f"Similarity Score: {similarity:.2f}")
            
            # Decision
            if similarity >= SIMILARITY_THRESHOLD:
                print("OWNER DETECTED!")
            else:
                print("Unauthorized voice")
            
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\nSystem shutdown complete.")


if __name__ == "__main__":
    main()

