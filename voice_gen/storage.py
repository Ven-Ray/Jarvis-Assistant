"""
Voice storage module.
Handles saving, listing, retrieving, and deleting reference voices with consent tracking.
"""

import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path


def get_storage_dir():
    """Get the reference voices storage directory."""
    return os.environ.get("REFERENCE_VOICES_DIR", "reference_voices")


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def save_voice(
    display_name: str,
    original_file_path: str,
    consent_confirmed: bool = False,
    language: str = "en",
    ai_disclosure_enabled: bool = True
) -> dict:
    """
    Save a reference voice with metadata.
    
    Args:
        display_name: User-friendly name for the voice (e.g., "Jarvis")
        original_file_path: Path to the original audio file
        consent_confirmed: Whether user confirmed consent (must be True)
        language: Language code of the recording
        ai_disclosure_enabled: Whether AI-generated disclosure is enabled
        
    Returns:
        Dictionary with saved voice information
        
    Raises:
        ValueError: If consent not confirmed or validation fails
        FileNotFoundError: If original file doesn't exist
    """
    if not consent_confirmed:
        raise ValueError(
            "Consent must be explicitly confirmed before saving a reference voice. "
            "Please confirm: 'I confirm that I own this recording or have permission "
            "from the speaker to clone and generate speech with this voice.'"
        )
    
    if not os.path.exists(original_file_path):
        raise FileNotFoundError(f"Original audio file not found: {original_file_path}")
    
    storage_dir = get_storage_dir()
    os.makedirs(storage_dir, exist_ok=True)
    
    # Calculate hash of original file
    file_hash = calculate_sha256(original_file_path)
    
    # Determine stored filename
    base_name = display_name.replace(" ", "_")
    extension = os.path.splitext(original_file_path)[1] or ".mp3"
    
    # Check for existing identical file (same hash) across ALL stored files
    existing_files = list(Path(storage_dir).glob(f"*{extension}"))
    
    stored_filename = None
    for existing in existing_files:
        try:
            if calculate_sha256(str(existing)) == file_hash:
                stored_filename = existing.name
                break
        except Exception:
            continue
    
    # If no identical file, create new unique name
    if not stored_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stored_filename = f"{base_name}_{timestamp}{extension}"
        
        # Check for name collision and increment if needed
        counter = 1
        while os.path.exists(os.path.join(storage_dir, stored_filename)):
            stored_filename = f"{base_name}_{timestamp}_{counter}{extension}"
            counter += 1
    
    # Copy (not move) the original file
    stored_path = os.path.join(storage_dir, stored_filename)
    shutil.copy2(original_file_path, stored_path)
    
    # Create metadata
    metadata = {
        "display_name": display_name,
        "original_filename": os.path.basename(original_file_path),
        "stored_filename": stored_filename,
        "language": language,
        "consent_confirmed": True,  # Only set to true if user explicitly confirmed
        "creation_timestamp": datetime.now().isoformat(),
        "sha256_hash": file_hash,
        "ai_disclosure_enabled": ai_disclosure_enabled
    }
    
    # Save metadata as JSON alongside audio file
    metadata_path = os.path.join(storage_dir, f"{stored_filename}.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        "success": True,
        "display_name": display_name,
        "stored_path": stored_path,
        "metadata_path": metadata_path,
        "sha256_hash": file_hash
    }


def list_voices() -> list:
    """List all saved reference voices."""
    storage_dir = get_storage_dir()
    
    if not os.path.exists(storage_dir):
        return []
    
    voices = []
    
    # Find all metadata JSON files
    for metadata_file in Path(storage_dir).glob("*.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verify the audio file still exists
            audio_path = os.path.join(storage_dir, metadata.get("stored_filename", ""))
            if os.path.exists(audio_path):
                voices.append({
                    "display_name": metadata.get("display_name", "Unknown"),
                    "stored_filename": metadata.get("stored_filename", ""),
                    "language": metadata.get("language", "en"),
                    "creation_timestamp": metadata.get("creation_timestamp", ""),
                    "sha256_hash": metadata.get("sha256_hash", "")
                })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return voices


def get_voice(display_name: str) -> dict:
    """
    Retrieve a saved voice by display name.
    
    Args:
        display_name: Name of the voice to retrieve
        
    Returns:
        Dictionary with voice information and paths
        
    Raises:
        ValueError: If voice not found
    """
    voices = list_voices()
    
    for voice in voices:
        if voice["display_name"].lower() == display_name.lower():
            storage_dir = get_storage_dir()
            
            # Load full metadata
            metadata_path = os.path.join(storage_dir, f"{voice['stored_filename']}.json")
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return {
                "display_name": metadata.get("display_name"),
                "audio_path": os.path.join(storage_dir, voice["stored_filename"]),
                "metadata": metadata
            }
    
    raise ValueError(f"Voice '{display_name}' not found. Available voices: {[v['display_name'] for v in voices]}")


def delete_voice(display_name: str) -> bool:
    """
    Delete a saved reference voice and its metadata.
    
    Args:
        display_name: Name of the voice to delete
        
    Returns:
        True if deleted, False if not found
    """
    try:
        voice = get_voice(display_name)
        
        # Delete audio file
        os.remove(voice["audio_path"])
        
        # Delete metadata file
        storage_dir = get_storage_dir()
        metadata_path = os.path.join(storage_dir, f"{voice['metadata']['stored_filename']}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        return True
        
    except ValueError:
        return False


def select_voice(display_name: str) -> str:
    """
    Select a voice for use in generation.
    
    Args:
        display_name: Name of the voice to select
        
    Returns:
        Path to the selected voice's audio file
    """
    voice = get_voice(display_name)
    return voice["audio_path"]