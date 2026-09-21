#!/usr/bin/env python3
"""
Comprehensive test suite for the Voice Generation Application.
Tests audio conversion, validation, storage with consent, and generation logic.
"""

import sys
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock


def test_audio_validation():
    """Test audio file validation."""
    from voice_gen.audio import validate_audio_file
    
    print("\nTesting audio file validation...")
    print("-" * 40)
    
    # Test non-existent file
    result = validate_audio_file("/nonexistent/file.mp3")
    assert not result["valid"], "Non-existent file should be invalid"
    assert "not found" in result["error"].lower()
    print("✓ Non-existent file detected as invalid")
    
    # Test empty file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
    
    try:
        result = validate_audio_file(temp_path)
        assert not result["valid"], "Empty file should be invalid"
        print("✓ Empty file detected as invalid")
    finally:
        os.unlink(temp_path)
    
    # Test valid small file (create a dummy WAV header)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        temp_path = f.name
        # Write minimal WAV header (44 bytes) + some data
        wav_header = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVEfmt ' + b'\x10\x00\x00\x00'
        f.write(wav_header + b'\x00' * 100)
    
    try:
        result = validate_audio_file(temp_path)
        # May or may not be valid depending on duration detection, but should not error
        print("✓ Valid file validation completed without error")
    finally:
        os.unlink(temp_path)
    
    return True


def test_consent_requirement():
    """Test that consent is required before saving a voice."""
    from voice_gen.storage import save_voice
    
    print("\nTesting consent requirement...")
    print("-" * 40)
    
    # Create temp audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
        f.write(b'dummy audio data')
    
    try:
        # Try to save without consent - should fail
        try:
            save_voice("TestVoice", temp_path, consent_confirmed=False)
            assert False, "Should have raised ValueError for missing consent"
        except ValueError as e:
            assert "consent" in str(e).lower()
            print("✓ Consent required before saving")
        
        # Save with consent - should succeed
        result = save_voice("TestVoice", temp_path, consent_confirmed=True)
        assert result["success"], "Should save successfully with consent"
        print("✓ Voice saved successfully with consent")
        
    finally:
        os.unlink(temp_path)
        # Clean up stored voice
        from voice_gen.storage import delete_voice
        delete_voice("TestVoice")
    
    return True


def test_duplicate_detection():
    """Test that duplicate files are detected and reused."""
    from voice_gen.storage import save_voice, list_voices
    
    print("\nTesting duplicate file detection...")
    print("-" * 40)
    
    # Create temp audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
        f.write(b'duplicate test data')
    
    try:
        # Save same file twice - should detect duplicate by hash
        result1 = save_voice("DupTest", temp_path, consent_confirmed=True)
        
        # Second save with different name but same content
        result2 = save_voice("DupTest2", temp_path, consent_confirmed=True)
        
        # Both should have the same stored path (duplicate detected)
        assert result1["stored_path"] == result2["stored_path"], \
            "Duplicate files should be detected and reused"
        print("✓ Duplicate file detected by SHA-256 hash")
        
    finally:
        os.unlink(temp_path)
        # Clean up
        from voice_gen.storage import delete_voice
        voices = list_voices()
        for v in voices:
            if "DupTest" in v["display_name"]:
                delete_voice(v["display_name"])
    
    return True


def test_voice_lifecycle():
    """Test full voice lifecycle: save, list, get, delete."""
    from voice_gen.storage import save_voice, list_voices, get_voice, delete_voice
    
    print("\nTesting voice lifecycle...")
    print("-" * 40)
    
    # Create temp audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
        f.write(b'lifecycle test data')
    
    try:
        # Save voice
        result = save_voice("LifecycleTest", temp_path, consent_confirmed=True)
        assert result["success"]
        print("✓ Voice saved")
        
        # List voices - should include our new voice
        voices = list_voices()
        found = any(v["display_name"] == "LifecycleTest" for v in voices)
        assert found, "Saved voice should appear in list"
        print("✓ Voice appears in list")
        
        # Get voice by name
        voice = get_voice("LifecycleTest")
        assert os.path.exists(voice["audio_path"])
        print("✓ Voice retrieved by name")
        
        # Delete voice
        deleted = delete_voice("LifecycleTest")
        assert deleted, "Voice should be deletable"
        print("✓ Voice deleted")
        
        # Verify deletion
        try:
            get_voice("LifecycleTest")
            assert False, "Deleted voice should not be retrievable"
        except ValueError:
            print("✓ Deleted voice no longer retrievable")
            
    finally:
        os.unlink(temp_path)
    
    return True


def test_cuda_detection():
    """Test CUDA availability detection."""
    from voice_gen.generation import is_cuda_available
    
    print("\nTesting CUDA detection...")
    print("-" * 40)
    
    # Should return a boolean without error
    result = is_cuda_available()
    assert isinstance(result, bool), "is_cuda_available should return bool"
    print(f"✓ CUDA available: {result}")
    
    return True


def test_generation_validation():
    """Test generation input validation."""
    from voice_gen.generation import generate_voice
    
    print("\nTesting generation input validation...")
    print("-" * 40)
    
    # Create a temp reference file for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        ref_path = f.name
        f.write(b'test audio')
    
    try:
        # Test empty text - should fail before checking file existence
        try:
            generate_voice("", ref_path, "/tmp/out.wav")
            assert False, "Should raise ValueError for empty text"
        except ValueError as e:
            assert "empty" in str(e).lower()
            print("✓ Empty text detected")
        
        # Test missing reference file
        try:
            generate_voice("Hello", "/nonexistent/ref.mp3", "/tmp/out.wav")
            assert False, "Should raise FileNotFoundError for missing reference"
        except FileNotFoundError as e:
            print("✓ Missing reference file detected")
            
    finally:
        os.unlink(ref_path)
    
    return True


def test_cli_interface():
    """Test CLI argument parsing."""
    import subprocess
    
    print("\nTesting CLI interface...")
    print("-" * 40)
    
    # Test help output
    result = subprocess.run(
        [sys.executable, "voice_gen/cli.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"
    assert "save" in result.stdout.lower()
    print("✓ CLI help displays correctly")
    
    # Test list command (should work even with no voices)
    result = subprocess.run(
        [sys.executable, "voice_gen/cli.py", "list"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"CLI list failed: {result.stderr}"
    print("✓ CLI list command works")
    
    return True


def main():
    """Run all tests."""
    print("Voice Generation Application - Test Suite")
    print("=" * 40)
    
    # Set up temp storage directory for tests
    test_storage = tempfile.mkdtemp()
    os.environ["REFERENCE_VOICES_DIR"] = test_storage
    
    try:
        tests = [
            test_audio_validation,
            test_consent_requirement,
            test_duplicate_detection,
            test_voice_lifecycle,
            test_cuda_detection,
            test_generation_validation,
            test_cli_interface
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"Error running {test.__name__}: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)
        
        if all(results):
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed.")
            return 1
            
    finally:
        # Clean up temp storage
        shutil.rmtree(test_storage, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())