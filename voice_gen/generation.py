"""
Voice generation engine using Coqui TTS XTTS v2.
Handles text-to-speech synthesis with reference voice cloning.
"""

import os
import tempfile


def is_cuda_available() -> bool:
    """Check if CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def generate_voice(
    text: str,
    reference_audio_path: str,
    output_path: str = "output.wav",
    language: str = "en"
) -> str:
    """
    Generate speech using Coqui TTS XTTS v2 with voice cloning.
    
    Args:
        text: Text to synthesize
        reference_audio_path: Path to reference audio file for voice cloning
        output_path: Path for the generated audio output
        language: Language code (en, es, fr, de, it, pt, pl, hu, ro, ru, ja, zh-cn, ko)
        
    Returns:
        Path to the generated audio file
        
    Raises:
        FileNotFoundError: If reference audio doesn't exist
        RuntimeError: If generation fails or TTS library not available
    """
    if not os.path.exists(reference_audio_path):
        raise FileNotFoundError(f"Reference audio file not found: {reference_audio_path}")
    
    # Validate text
    if not text or len(text.strip()) == 0:
        raise ValueError("Text to synthesize cannot be empty")
    
    try:
        from TTS.api import TTS
        
        # Determine device (CUDA if available, CPU otherwise)
        device = "cuda" if is_cuda_available() else "cpu"
        
        print(f"Loading XTTS v2 model on {device}...")
        
        # Load the model
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
        
        # Generate speech with voice cloning
        print(f"Generating speech for: '{text[:50]}...'")
        
        tts.tts_to_file(
            text=text,
            speaker_wav=reference_audio_path,
            language=language,
            output_path=output_path
        )
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"Generation completed but output file not found: {output_path}")
        
        print(f"Speech generated successfully: {output_path}")
        return output_path
        
    except ImportError as e:
        raise RuntimeError(
            "Coqui TTS library not installed. Install with: pip install TTS"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Voice generation failed: {e}") from e