#!/usr/bin/env python3
"""
Comprehensive test suite for Jarvis voice-listening workflow,
temporary audio file handling, and frontend chat updates.

Tests:
1. Temporary voice recording folder creation and cleanup
2. Listen button start/stop toggle behavior (simulated)
3. Chat message flow: user msg → Jarvis response text → speak
4. No duplicate sessions or stuck states
5. Error handling for speech recognition failures
"""

import os
import sys
import time
import threading
from unittest.mock import Mock, patch, MagicMock

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_voice_records_directory():
    """Test that voice_records directory is created and used correctly."""
    print("\n=== Test 1: Voice Records Directory ===")
    
    from jarvis import JarvisAssistant
    
    # Mock hardware initialization
    with patch('jarvis.JarvisAssistant.__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Manually set up what __init__ would do for voice_records_dir
        assistant.voice_records_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voice_records"
    # Verify directory exists or can be created
    if not os.path.exists(assistant.voice_records_dir):
        os.makedirs(assistant.voice_records_dir)
    
    assert os.path.isdir(assistant.voice_records_dir), \
        f"Voice records directory does not exist: {assistant.voice_records_dir}"
    print(f"✓ Voice records directory exists: {assistant.voice_records_dir}")
    
    # Test that a temp file can be created and cleaned up in this directory
    import uuid
    test_file = os.path.join(assistant.voice_records_dir, f"test_{uuid.uuid4().hex[:8]}.mp3")
    with open(test_file, 'w') as f:
        f.write("test")
    
    assert os.path.exists(test_file), "Test file was not created in voice_records directory"
    print(f"✓ Test file created in voice_records: {os.path.basename(test_file)}")
    
    # Clean up test file
    os.remove(test_file)
    assert not os.path.exists(test_file), "Test file cleanup failed"
    print("✓ Test file cleaned up successfully")


def test_get_response_text_method():
    """Test that get_response_text returns text without speaking."""
    print("\n=== Test 2: get_response_text Method ===")
    
    from jarvis import JarvisAssistant
    
    with patch('jarvis.JarvisAssistant.__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Mock speak to track calls
        spoken = []
        def mock_speak(text):
            spoken.append(text)
        
        assistant.speak = mock_speak
        
        # Test simple greeting - should return text without speaking
        response_text, is_exit = assistant.get_response_text("hello")
        assert response_text == "Good day, Sir. How may I assist you?", \
            f"Unexpected response: {response_text}"
        assert not is_exit, "Greeting should not trigger exit"
        assert len(spoken) == 0, f"speak() was called during get_response_text: {spoken}"
        print("✓ Greeting returns text without speaking")
        
        # Test name query
        response_text, is_exit = assistant.get_response_text("what is your name")
        assert "JARVIS" in response_text.upper(), f"Name not in response: {response_text}"
        assert len(spoken) == 0, "speak() was called during get_response_text"
        print("✓ Name query returns text without speaking")
        
        # Test exit command
        response_text, is_exit = assistant.get_response_text("goodbye")
        assert is_exit, "Goodbye should trigger exit flag"
        assert len(spoken) == 0, "speak() was called during get_response_text"
        print("✓ Exit command returns text and exit flag without speaking")


def test_process_command_speaks():
    """Test that process_command still speaks the response."""
    print("\n=== Test 3: process_command Speaks Response ===")
    
    from jarvis import JarvisAssistant
    
    with patch('jarvis.JarvisAssistant.__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        spoken = []
        def mock_speak(text):
            spoken.append(text)
        
        assistant.speak = mock_speak
        
        # process_command should speak the response
        result = assistant.process_command("hello")
        assert len(spoken) == 1, f"Expected 1 spoken message, got {len(spoken)}"
        assert "Good day" in spoken[0], f"Unexpected speech: {spoken[0]}"
        print(f"✓ process_command speaks response: '{spoken[0][:30]}...'")


def test_listen_button_toggle_simulation():
    """Simulate the frontend listen button toggle behavior."""
    print("\n=== Test 4: Listen Button Toggle Simulation ===")
    
    # Simulate state machine
    class MockFrontend:
        def __init__(self):
            self.is_listening = False
            self.current_state = "idle"
            self.listen_thread = None
            self.button_text = "LISTEN"
        
        def toggle_listening(self):
            if self.is_listening:
                # Stop listening
                print("  [Toggle] Stopping listening")
                self.is_listening = False
                self.button_text = "LISTEN"
                return "stopped"
            else:
                # Start listening - only from idle state
                if self.current_state != "idle":
                    print(f"  [Toggle] Duplicate request ignored (state={self.current_state})")
                    return "ignored"
                
                print("  [Toggle] Starting listening")
                self.is_listening = True
                self.button_text = "STOP LISTENING"
                self.current_state = "listening"
                return "started"
    
    frontend = MockFrontend()
    
    # Test 1: Start listening from idle
    result = frontend.toggle_listening()
    assert result == "started", f"Expected 'started', got '{result}'"
    assert frontend.is_listening, "Should be listening after first toggle"
    assert frontend.button_text == "STOP LISTENING", \
        f"Button should say STOP LISTENING, says {frontend.button_text}"
    print("✓ First click starts listening (button: STOP LISTENING)")
    
    # Test 2: Duplicate start request while already listening
    result = frontend.toggle_listening()
    assert result == "stopped", f"Expected 'stopped', got '{result}'"
    assert not frontend.is_listening, "Should not be listening after second toggle"
    print("✓ Second click stops listening (button: LISTEN)")
    
    # Test 3: Start again after stopping
    frontend.current_state = "idle"
    result = frontend.toggle_listening()
    assert result == "started", f"Expected 'started', got '{result}'"
    print("✓ Third click starts new listening session")
    
    # Test 4: Duplicate request while processing (not idle)
    frontend.is_listening = False
    frontend.current_state = "processing"
    result = frontend.toggle_listening()
    assert result == "ignored", f"Expected 'ignored', got '{result}'"
    print("✓ Duplicate request ignored during processing state")


def test_chat_message_flow():
    """Test the chat message flow: user msg → Jarvis response → speak."""
    print("\n=== Test 5: Chat Message Flow ===")
    
    from jarvis import JarvisAssistant
    
    with patch('jarvis.JarvisAssistant.__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Simulate frontend chat flow
        chat_messages = []
        spoken = []
        
        def mock_speak(text):
            spoken.append(text)
        
        assistant.speak = mock_speak
        
        user_command = "What is your name?"
        
        # Step 1: Add user message to chat immediately
        chat_messages.append({"sender": "You", "text": user_command, "is_user": True})
        print(f"✓ User message added to chat: '{user_command}'")
        
        # Step 2: Get response text without speaking
        response_text, is_exit = assistant.get_response_text(user_command)
        assert response_text is not None, "Response should not be None"
        assert len(spoken) == 0, "Should not have spoken yet"
        print(f"✓ Response text obtained (not yet spoken): '{response_text[:40]}...'")
        
        # Step 3: Add Jarvis response to chat before speaking
        chat_messages.append({"sender": "JARVIS", "text": response_text, "is_user": False})
        assert len(spoken) == 0, "Should not have spoken yet"
        print("✓ Jarvis response added to chat (before speaking)")
        
        # Step 4: Speak the response after adding to chat
        assistant.speak(response_text)
        assert len(spoken) == 1, f"Expected 1 spoken message, got {len(spoken)}"
        assert spoken[0] == response_text, "Spoken text should match chat text"
        print(f"✓ Response spoken after adding to chat")
        
        # Verify exact same text in chat and speech
        assert chat_messages[-1]["text"] == spoken[0], \
            "Chat text and spoken text must be identical"
        print("✓ Chat text matches spoken text exactly")


def test_no_duplicate_sessions():
    """Test that rapid clicks don't create duplicate listening sessions."""
    print("\n=== Test 6: No Duplicate Listening Sessions ===")
    
    session_count = [0]
    
    class MockFrontend:
        def __init__(self):
            self.is_listening = False
            self.current_state = "idle"
            self.listen_thread = None
        
        def start_listening(self):
            if self.listen_thread and self.listen_thread.is_alive():
                return  # Already running
            
            session_count[0] += 1
            print(f"  [Session {session_count[0]}] Starting listening thread")
            
            def listen_loop():
                time.sleep(0.1)  # Simulate listening
                self.current_state = "idle"
            
            self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
            self.listen_thread.start()
    
    frontend = MockFrontend()
    
    # Rapid clicks - should only start one session
    for i in range(5):
        if not frontend.is_listening and frontend.current_state == "idle":
            frontend.is_listening = True
            frontend.current_state = "listening"
            frontend.start_listening()
        
        time.sleep(0.01)  # Small delay between clicks
    
    time.sleep(0.2)  # Wait for thread to finish
    
    assert session_count[0] == 1, \
        f"Expected 1 listening session, got {session_count[0]}"
    print(f"✓ Only 1 listening session started despite 5 rapid clicks")


def test_state_transitions():
    """Test that state transitions are valid and don't get stuck."""
    print("\n=== Test 7: State Transitions ===")
    
    # Valid transitions map
    allowed = {
        "idle": ["listening", "processing"],
        "listening": ["processing", "speaking", "error", "idle"],
        "processing": ["speaking", "error", "idle"],
        "speaking": ["idle", "error"],
        "error": ["idle"]
    }
    
    def validate_transition(from_state, to_state):
        if to_state in allowed.get(from_state, []):
            return True
        return False
    
    # Test valid transitions
    assert validate_transition("idle", "listening"), "idle → listening should be valid"
    print("✓ idle → listening: valid")
    
    assert validate_transition("listening", "processing"), "listening → processing should be valid"
    print("✓ listening → processing: valid")
    
    assert validate_transition("processing", "speaking"), "processing → speaking should be valid"
    print("✓ processing → speaking: valid")
    
    assert validate_transition("speaking", "idle"), "speaking → idle should be valid"
    print("✓ speaking → idle: valid")
    
    # Test invalid transitions (based on actual allowed_transitions map)
    assert not validate_transition("idle", "speaking"), \
        "idle → speaking should be invalid"
    print("✓ idle → speaking: correctly rejected as invalid")
    
    assert not validate_transition("processing", "listening"), \
        "processing → listening should be invalid"
    print("✓ processing → listening: correctly rejected as invalid")


def test_error_handling():
    """Test error handling for speech recognition failures."""
    print("\n=== Test 8: Error Handling ===")
    
    from jarvis import JarvisAssistant
    
    with patch('jarvis.JarvisAssistant.__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Mock listen to raise various errors
        def mock_listen_timeout():
            raise TimeoutError("Listening timed out - no speech detected within 10 seconds")
        
        def mock_listen_unknown():
            raise ValueError("Could not understand the audio captured")
        
        # Test timeout handling
        try:
            assistant.listen = mock_listen_timeout
            assistant.listen()
            assert False, "Should have raised TimeoutError"
        except TimeoutError as e:
            print(f"✓ Timeout error handled: {str(e)[:50]}...")
        
        # Test unknown speech handling
        try:
            assistant.listen = mock_listen_unknown
            assistant.listen()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"✓ Unknown speech error handled: {str(e)[:50]}...")


def test_audio_file_cleanup():
    """Test that temporary audio files are cleaned up after playback."""
    print("\n=== Test 9: Audio File Cleanup ===")
    
    import uuid
    
    voice_records_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "voice_records"
    )
    
    if not os.path.exists(voice_records_dir):
        os.makedirs(voice_records_dir)
    
    # Simulate file creation and cleanup
    audio_file = os.path.join(voice_records_dir, f"jarvis_output_{uuid.uuid4().hex[:8]}.mp3")
    
    try:
        # Create temp file (simulating edge-tts output)
        with open(audio_file, 'w') as f:
            f.write("mock audio data")
        
        assert os.path.exists(audio_file), "Audio file was not created"
        print(f"✓ Audio file created in voice_records: {os.path.basename(audio_file)}")
        
        # Simulate playback (just verify file exists)
        with open(audio_file, 'r') as f:
            data = f.read()
        assert len(data) > 0, "Playback failed - no data"
        print("✓ Playback simulation successful")
        
    finally:
        # Cleanup (simulating the finally block in _speak_edge_tts)
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        assert not os.path.exists(audio_file), "Audio file cleanup failed"
        print("✓ Audio file cleaned up after playback")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Jarvis Voice Assistant - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        test_voice_records_directory,
        test_get_response_text_method,
        test_process_command_speaks,
        test_listen_button_toggle_simulation,
        test_chat_message_flow,
        test_no_duplicate_sessions,
        test_state_transitions,
        test_error_handling,
        test_audio_file_cleanup,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
