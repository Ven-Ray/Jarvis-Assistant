"""
Audio conversion and validation module.
Handles format conversion, file validation, and quality analysis.
"""

import os
import subprocess
from pathlib import Path


def validate_audio_file(file_path: str, max_size_mb: int = 50) -> dict:
    """
    Validate that an audio file exists, is readable, and meets size requirements.
    
    Args:
        file_path: Path to audio file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        Dictionary with validation results:
        - valid: bool
        - error: str (if invalid)
        - size_bytes: int
        - duration_seconds: float (if determinable)
    """
    result = {
        "valid": False,
        "error": None,
        "size_bytes": 0,
        "duration_seconds": None
    }
    
    # Check file exists
    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result
    
    # Check readable
    try:
        with open(file_path, 'rb') as f:
            pass
    except PermissionError:
        result["error"] = f"Cannot read file: {file_path}"
        return result
    
    # Check size
    try:
        size_bytes = os.path.getsize(file_path)
        result["size_bytes"] = size_bytes
        
        if size_bytes > max_size_mb * 1024 * 1024:
            result["error"] = f"File too large ({size_bytes / (1024*1024):.1f} MB). Maximum is {max_size_mb} MB."
            return result
        
        if size_bytes == 0:
            result["error"] = "File is empty"
            return result
            
    except OSError as e:
        result["error"] = f"Cannot determine file size: {e}"
        return result
    
    # Try to get duration using ffprobe or pydub
    try:
        duration = _get_duration(file_path)
        if duration is not None:
            result["duration_seconds"] = duration
            
            if duration < 1.0:
                result["error"] = "Audio too short (less than 1 second)"
                return result
                
            if duration > 3600:
                result["error"] = "Audio too long (more than 1 hour)"
                return result
    except Exception as e:
        # Duration check is optional
        pass
    
    result["valid"] = True
    return result


def _get_duration(file_path: str):
    """Get audio duration in seconds using ffprobe or pydub."""
    # Try ffprobe first
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fall back to pydub
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception:
        return None


def analyze_audio_quality(file_path: str) -> dict:
    """
    Analyze audio quality and provide warnings about potential issues.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with analysis results:
        - warnings: list of warning strings
        - has_speech: bool (if determinable)
        - speech_duration_seconds: float (if determinable)
    """
    result = {
        "warnings": [],
        "has_speech": None,
        "speech_duration_seconds": None
    }
    
    # Check for excessive silence using pydub if available
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_silence
        
        audio = AudioSegment.from_file(file_path)
        
        # Detect silent sections
        silent_sections = detect_silence(
            audio, 
            min_silence_len=500,  # 500ms minimum silence
            silence_thresh=-40,   # -40 dBFS threshold
            chunk_size=100
        )
        
        total_duration_ms = len(audio)
        silent_duration_ms = sum(end - start for start, end in silent_sections)
        speech_duration_ms = total_duration_ms - silent_duration_ms
        
        result["speech_duration_seconds"] = speech_duration_ms / 1000.0
        result["has_speech"] = speech_duration_ms > 0
        
        # Warn about excessive silence (>50% of audio is silent)
        if total_duration_ms > 0 and (silent_duration_ms / total_duration_ms) > 0.5:
            result["warnings"].append(
                "Audio contains more than 50% silence. Consider trimming."
            )
        
        # Warn about very short speech segments
        if speech_duration_ms < 3000:
            result["warnings"].append(
                "Very little speech detected (less than 3 seconds). "
                "Longer recordings produce better voice cloning results."
            )
            
    except ImportError:
        pass
    
    # Warn about stereo audio (should be mono for best results)
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        
        if audio.channels > 1:
            result["warnings"].append(
                "Audio is stereo. Mono recordings typically produce better voice cloning."
            )
            
    except Exception:
        pass
    
    return result