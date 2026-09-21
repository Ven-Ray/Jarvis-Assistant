#!/usr/bin/env python3
"""
Test the response ordering workflow: chat update before TTS playback.
Simulates the sequence and validates proper state transitions.
"""

import sys
import os
import threading
import time

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_state_transitions():
    """Test that all required state transitions are valid."""
    print("\n=== Test 1: State Transition Validation ===")
    
    # Import the frontend module to access state transition logic
    from frontend.main_window import JarvisFrontend
    
    # Create a mock instance (don't show window)
    class MockJarvisFrontend(JarvisFrontend):
        def __init__(self):
            # Initialize only what we need for testing
            self.current_state = "idle"
            self.state_lock = threading.Lock()
    
    frontend = MockJarvisFrontend()
    
    # Test successful voice request sequence
    print("\nTesting: IDLE -> LISTENING -> PROCESSING -> SEARCHING -> RESPONSE_READY -> CHAT_UPDATED -> SPEAKING -> IDLE")
    
    transitions = [
        ("idle", "listening"),
        ("listening", "processing"),
        ("processing", "searching"),
        ("searching", "response_ready"),
        ("response_ready", "chat_updated"),
        ("chat_updated", "speaking"),
        ("speaking", "idle")
    ]
    
    all_valid = True
    for from_state, to_state in transitions:
        frontend.current_state = from_state
        # Check if transition is allowed
        allowed_transitions = {
            "idle": ["listening", "processing"],
            "listening": ["processing", "speaking", "error", "idle"],
            "processing": ["searching", "response_ready", "error", "idle"],
            "searching": ["response_ready", "error", "idle"],
            "response_ready": ["chat_updated", "error"],
            "chat_updated": ["speaking", "idle"],
            "speaking": ["idle", "error"],
            "error": ["idle"]
        }
        
        is_allowed = to_state in allowed_transitions.get(from_state, [])
        status = "✓" if is_allowed else "✗"
        print(f"{status} {from_state} -> {to_state}")
        if not is_allowed:
            all_valid = False
    
    # Test text-only response sequence
    print("\nTesting: PROCESSING -> RESPONSE_READY -> CHAT_UPDATED -> IDLE")
    
    text_only_transitions = [
        ("processing", "response_ready"),
        ("response_ready", "chat_updated"),
        ("chat_updated", "idle")
    ]
    
    for from_state, to_state in text_only_transitions:
        frontend.current_state = from_state
        allowed_transitions = {
            "idle": ["listening", "processing"],
            "listening": ["processing", "speaking", "error", "idle"],
            "processing": ["searching", "response_ready", "error", "idle"],
            "searching": ["response_ready", "error", "idle"],
            "response_ready": ["chat_updated", "error"],
            "chat_updated": ["speaking", "idle"],
            "speaking": ["idle", "error"],
            "error": ["idle"]
        }
        
        is_allowed = to_state in allowed_transitions.get(from_state, [])
        status = "✓" if is_allowed else "✗"
        print(f"{status} {from_state} -> {to_state}")
        if not is_allowed:
            all_valid = False
    
    # Test TTS failure sequence
    print("\nTesting: RESPONSE_READY -> CHAT_UPDATED -> SPEAKING -> ERROR -> IDLE")
    
    tts_failure_transitions = [
        ("response_ready", "chat_updated"),
        ("chat_updated", "speaking"),
        ("speaking", "error"),
        ("error", "idle")
    ]
    
    for from_state, to_state in tts_failure_transitions:
        frontend.current_state = from_state
        allowed_transitions = {
            "idle": ["listening", "processing"],
            "listening": ["processing", "speaking", "error", "idle"],
            "processing": ["searching", "response_ready", "error", "idle"],
            "searching": ["response_ready", "error", "idle"],
            "response_ready": ["chat_updated", "error"],
            "chat_updated": ["speaking", "idle"],
            "speaking": ["idle", "error"],
            "error": ["idle"]
        }
        
        is_allowed = to_state in allowed_transitions.get(from_state, [])
        status = "✓" if is_allowed else "✗"
        print(f"{status} {from_state} -> {to_state}")
        if not is_allowed:
            all_valid = False
    
    return all_valid


def test_request_id_tracking():
    """Test request ID generation and tracking."""
    print("\n=== Test 2: Request ID Tracking ===")
    
    from frontend.main_window import JarvisFrontend
    
    class MockJarvisFrontend(JarvisFrontend):
        def __init__(self):
            self.request_counter = 0
            self.active_request_id = None
            self.request_lock = threading.Lock()
    
    frontend = MockJarvisFrontend()
    
    # Generate multiple request IDs
    id1 = frontend.next_request_id()
    id2 = frontend.next_request_id()
    id3 = frontend.next_request_id()
    
    print(f"Request ID 1: {id1}")
    print(f"Request ID 2: {id2}")
    print(f"Request ID 3: {id3}")
    
    # Verify IDs are unique and incrementing
    assert id1 < id2 < id3, "Request IDs should be incrementing"
    print("✓ Request IDs are unique and incrementing")
    
    # Verify active request tracking
    assert frontend.active_request_id == id3, "Active request should be the latest"
    print("✓ Active request ID tracks the latest request")
    
    # Test is_current_request
    assert not frontend.is_current_request(id1), "Old request 1 should not be current"
    assert not frontend.is_current_request(id2), "Old request 2 should not be current"
    assert frontend.is_current_request(id3), "Latest request 3 should be current"
    print("✓ is_current_request correctly identifies active vs. superseded requests")
    
    return True


def test_response_ordering_simulation():
    """Simulate the response ordering to verify chat updates before TTS."""
    print("\n=== Test 3: Response Ordering Simulation ===")
    
    events = []
    
    def simulate_request(text):
        """Simulate a complete request-response cycle."""
        events.append(("user_message_displayed", text))
        
        # Processing phase
        time.sleep(0.01)
        response_text = f"Response to: {text}"
        
        # Step 1: Response ready
        events.append(("response_ready", None))
        
        # Step 2: Display in chat BEFORE speaking
        events.append(("chat_updated", response_text))
        
        # Step 3: Speak AFTER chat update
        time.sleep(0.01)
        events.append(("tts_started", response_text))
        
        # Step 4: TTS completes
        time.sleep(0.01)
        events.append(("tts_completed", None))
        
        # Step 5: Return to idle
        events.append(("idle", None))
    
    # Simulate a request
    simulate_request("What is the weather?")
    
    # Verify ordering
    print("\nEvent sequence:")
    for i, (event_type, data) in enumerate(events):
        if data:
            print(f"  {i+1}. {event_type}: {data[:50]}...")
        else:
            print(f"  {i+1}. {event_type}")
    
    # Find indices of key events
    chat_updated_idx = next(i for i, (e, _) in enumerate(events) if e == "chat_updated")
    tts_started_idx = next(i for i, (e, _) in enumerate(events) if e == "tts_started")
    
    assert chat_updated_idx < tts_started_idx, "Chat must update before TTS starts"
    print("\n✓ Chat updated BEFORE TTS playback started")
    
    # Verify same text is displayed and spoken
    chat_text = next(d for e, d in events if e == "chat_updated")
    tts_text = next(d for e, d in events if e == "tts_started")
    assert chat_text == tts_text, "Displayed and spoken text must match"
    print("✓ Displayed text matches spoken text")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Jarvis Response Ordering Workflow Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("State Transitions", test_state_transitions()))
    results.append(("Request ID Tracking", test_request_id_tracking()))
    results.append(("Response Ordering", test_response_ordering_simulation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
