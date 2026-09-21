"""
Voice Generation Application
Accepts reference audio, stores it with consent, and generates speech using Coqui TTS XTTS v2.
"""

from .audio import validate_audio_file, analyze_audio_quality
from .storage import save_voice, list_voices, get_voice, delete_voice, select_voice
from .generation import generate_voice, is_cuda_available

__version__ = "1.0.0"