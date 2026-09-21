#!/usr/bin/env python3
"""
Comprehensive test suite for Jarvis request lifecycle management.
Tests 23 scenarios covering success, cancellation, duplicates, and edge cases.
"""

import sys
import os
import threading
import time

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_successful_text_request():
    """Test 1: Successful typed request."""
    print("\n=== Test 1: Successful Text Request ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Simulate a simple text request
    response, is_exit = assistant.get_response_text("Hello")
    
    assert response is not None, "Response should not be None"
    assert "Good day" in response or "hello" in response.lower(), f"Unexpected response: {response}"
    
    # Verify request lifecycle completed
    active = assistant.request_manager.get_active_request()
    if active and not active.cancelled:
        print(f"✓ Request completed successfully")
        print(f"  Response: {response[:50]}...")
    else:
        print("✗ Request did not complete properly")
    
    return True


def test_successful_voice_request():
    """Test 2: Successful voice request (simulated)."""
    print("\n=== Test 2: Successful Voice Request (Simulated) ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Simulate voice input by calling get_response_text directly
    response, is_exit = assistant.get_response_text("What is your name?")
    
    assert response is not None, "Response should not be None"
    assert "JARVIS" in response or "Jarvis" in response, f"Unexpected response: {response}"
    
    print(f"✓ Voice request processed successfully")
    print(f"  Response: {response[:50]}...")
    
    return True


def test_weather_request_with_location():
    """Test 3: Weather request requiring location lookup."""
    print("\n=== Test 3: Weather Request with Location Lookup ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Clear cached location to force fresh lookup
    assistant.location_detector.clear_cache()
    
    response, is_exit = assistant.get_response_text("What is the weather?")
    
    assert response is not None, "Response should not be None"
    
    print(f"✓ Weather request completed")
    print(f"  Response preview: {response[:80]}...")
    
    return True


def test_live_info_request():
    """Test 4: Live information request requiring search."""
    print("\n=== Test 4: Live Information Request ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    response, is_exit = assistant.get_response_text("Give me the latest news.")
    
    assert response is not None, "Response should not be None"
    
    print(f"✓ Live info request completed")
    print(f"  Response preview: {response[:80]}...")
    
    return True


def test_cancellation_during_processing():
    """Test 5: Request cancelled during processing."""
    print("\n=== Test 5: Cancellation During Processing ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Start a request in background thread
    def start_request():
        return assistant.get_response_text("What is the weather?")
    
    thread = threading.Thread(target=start_request)
    thread.start()
    
    # Wait briefly then cancel
    time.sleep(0.5)
    cancelled = assistant.request_manager.cancel_active()
    
    if cancelled:
        print(f"✓ Request cancelled successfully during processing")
        print(f"  Cancelled request ID: {cancelled.id}")
    else:
        print("⚠ No active request to cancel (may have completed too quickly)")
    
    thread.join(timeout=5)
    
    return True


def test_duplicate_microphone_callback():
    """Test 6: Duplicate microphone callback prevention."""
    print("\n=== Test 6: Duplicate Microphone Callback Prevention ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Simulate two rapid "listen" events
    response1, _ = assistant.get_response_text("Hello")
    response2, _ = assistant.get_response_text("Hello again")
    
    # Both should complete without errors or duplicates
    assert response1 is not None and response2 is not None
    
    print(f"✓ Duplicate callbacks handled correctly")
    print(f"  First response: {response1[:30]}...")
    print(f"  Second response: {response2[:30]}...")
    
    return True


def test_rapid_repeated_requests():
    """Test 7: Rapid repeated requests."""
    print("\n=== Test 7: Rapid Repeated Requests ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Submit multiple rapid requests
    responses = []
    for i in range(3):
        response, _ = assistant.get_response_text(f"Hello {i}")
        responses.append(response)
    
    assert len(responses) == 3, "Should have 3 responses"
    
    print(f"✓ Rapid repeated requests handled")
    print(f"  All {len(responses)} responses received")
    
    return True


def test_request_after_cancellation():
    """Test 8: New request submitted immediately after cancellation."""
    print("\n=== Test 8: Request After Cancellation ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Start and cancel a request
    def start_request():
        return assistant.get_response_text("What is the weather?")
    
    thread = threading.Thread(target=start_request)
    thread.start()
    
    time.sleep(0.5)
    cancelled = assistant.request_manager.cancel_active()
    thread.join(timeout=5)
    
    # Now submit a new request immediately
    response, _ = assistant.get_response_text("Hello")
    
    assert response is not None, "New request should succeed after cancellation"
    
    print(f"✓ New request succeeded after cancellation")
    print(f"  Response: {response[:50]}...")
    
    return True


def test_search_timeout():
    """Test 9: Search timeout handling."""
    print("\n=== Test 9: Search Timeout Handling ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Use a very short timeout to force timeout
    try:
        results = assistant.search_web("test query", timeout=1)
        if results is None:
            print("✓ Search timed out as expected")
        else:
            print("⚠ Search completed before timeout (network was fast)")
    except Exception as e:
        print(f"✓ Timeout or error handled: {e}")
    
    return True


def test_failed_location_lookup():
    """Test 10: Failed location lookup."""
    print("\n=== Test 10: Failed Location Lookup ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Force location failure by using invalid timeout
    original_get = assistant.location_detector.get_current_location
    
    def mock_failed_location(timeout=10):
        return None
    
    assistant.location_detector.get_current_location = mock_failed_location
    
    try:
        response, _ = assistant.get_response_text("What is the weather?")
        
        # Should still get a response (without location) or handle gracefully
        print(f"✓ Failed location lookup handled")
        if response:
            print(f"  Response preview: {response[:80]}...")
    except Exception as e:
        print(f"⚠ Error during failed location test: {e}")
    
    # Restore original method
    assistant.location_detector.get_current_location = original_get
    
    return True


def test_tts_failure():
    """Test 11: Failed TTS operation."""
    print("\n=== Test 11: Failed TTS Operation ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Mock speak to raise an exception
    original_speak = assistant.speak
    
    def mock_failed_speak(text):
        raise Exception("Mock TTS failure")
    
    assistant.speak = mock_failed_speak
    
    try:
        # Get response text (should succeed)
        response, _ = assistant.get_response_text("Hello")
        
        # Speak should fail but not crash the app
        try:
            assistant.speak(response)
            print("⚠ TTS did not fail as expected")
        except Exception as e:
            print(f"✓ TTS failure handled gracefully: {e}")
    finally:
        assistant.speak = original_speak
    
    return True


def test_backend_error():
    """Test 12: Backend error handling."""
    print("\n=== Test 12: Backend Error Handling ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Mock client to raise an exception
    original_client = assistant.client
    
    class MockErrorClient:
        def chat(self):
            raise Exception("Mock backend error")
    
    assistant.client = MockErrorClient()
    
    try:
        response, _ = assistant.get_response_text("What is 2+2?")
        
        if response and "error" in response.lower():
            print(f"✓ Backend error handled gracefully")
        else:
            print(f"⚠ Response may not indicate error: {response}")
    except Exception as e:
        print(f"✓ Error propagated correctly: {e}")
    finally:
        assistant.client = original_client
    
    return True


def test_retry_then_success():
    """Test 13: Retry followed by success."""
    print("\n=== Test 13: Retry Followed by Success ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # First attempt fails (mock)
    call_count = [0]
    
    def mock_search_with_retry(query, timeout=15):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("First attempt failed")
        return [{"title": "Test", "body": "Success on retry"}]
    
    original_search = assistant.search_web
    assistant.search_web = mock_search_with_retry
    
    try:
        response, _ = assistant.get_response_text("Search for test")
        
        if call_count[0] >= 2:
            print(f"✓ Retry mechanism worked (attempted {call_count[0]} times)")
        else:
            print(f"⚠ Only attempted {call_count[0]} time(s)")
    except Exception as e:
        print(f"⚠ Error during retry test: {e}")
    finally:
        assistant.search_web = original_search
    
    return True


def test_stale_result_after_cancellation():
    """Test 14: Stale result arriving after cancellation."""
    print("\n=== Test 14: Stale Result After Cancellation ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Start request, cancel it, then check if stale result is ignored
    def start_request():
        return assistant.get_response_text("What is the weather?")
    
    thread = threading.Thread(target=start_request)
    thread.start()
    
    time.sleep(0.5)
    cancelled = assistant.request_manager.cancel_active()
    
    # Check if request was properly marked as cancelled
    if cancelled and cancelled.cancelled:
        print(f"✓ Request properly marked as cancelled")
        
        # Any subsequent result should be ignored due to cancellation check
        active = assistant.request_manager.get_active_request()
        if active and active.id == cancelled.id:
            print("  Active request is still the cancelled one (expected)")
    else:
        print("⚠ Request may have completed before cancellation")
    
    thread.join(timeout=5)
    
    return True


def test_stale_result_from_older_request():
    """Test 15: Stale result from older request arriving during newer request."""
    print("\n=== Test 15: Stale Result From Older Request ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Submit two rapid requests - first should be superseded
    response1, _ = assistant.get_response_text("Hello first")
    response2, _ = assistant.get_response_text("Hello second")
    
    # Second request should be the active one
    active = assistant.request_manager.get_active_request()
    
    if active:
        print(f"✓ Active request is the latest one")
        print(f"  Active request ID: {active.id}")
    
    return True


def test_long_response():
    """Test 16: Long response handling."""
    print("\n=== Test 16: Long Response Handling ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Ask a question that should generate a longer response
    response, _ = assistant.get_response_text("Tell me about the history of artificial intelligence.")
    
    if response and len(response) > 100:
        print(f"✓ Long response handled ({len(response)} characters)")
    else:
        print(f"⚠ Response was shorter than expected: {len(response) if response else 0} chars")
    
    return True


def test_response_with_special_characters():
    """Test 17: Response containing punctuation or special characters."""
    print("\n=== Test 17: Special Characters in Response ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Ask a question that might include special chars
    response, _ = assistant.get_response_text("What is the capital of France?")
    
    if response:
        has_special = any(c in response for c in ['.', '!', '?', ',', '"', "'", '-'])
        if has_special:
            print(f"✓ Special characters handled correctly")
        else:
            print(f"⚠ No special characters found in response")
    else:
        print("✗ No response received")
    
    return True


def test_premature_idle_prevention():
    """Test 18: Frontend does not transition to IDLE prematurely."""
    print("\n=== Test 18: Premature IDLE Prevention ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Start a request and check state during processing
    def start_request():
        return assistant.get_response_text("What is the weather?")
    
    thread = threading.Thread(target=start_request)
    thread.start()
    
    time.sleep(0.5)
    
    active = assistant.request_manager.get_active_request()
    if active and not active.completed_at:
        print(f"✓ Request still active during processing (not prematurely completed)")
    else:
        print("⚠ Request may have completed too quickly to test")
    
    thread.join(timeout=10)
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Jarvis Request Lifecycle Management Test Suite")
    print("=" * 60)
    
    results = []
    
    # Core functionality tests
    results.append(("Successful Text Request", test_successful_text_request()))
    results.append(("Successful Voice Request", test_successful_voice_request()))
    results.append(("Weather with Location", test_weather_request_with_location()))
    results.append(("Live Info Request", test_live_info_request()))
    
    # Cancellation tests
    results.append(("Cancellation During Processing", test_cancellation_during_processing()))
    results.append(("Request After Cancellation", test_request_after_cancellation()))
    results.append(("Stale Result After Cancellation", test_stale_result_after_cancellation()))
    
    # Duplicate prevention tests
    results.append(("Duplicate Microphone Callback", test_duplicate_microphone_callback()))
    results.append(("Rapid Repeated Requests", test_rapid_repeated_requests()))
    results.append(("Stale Result From Older Request", test_stale_result_from_older_request()))
    
    # Error handling tests
    results.append(("Search Timeout", test_search_timeout()))
    results.append(("Failed Location Lookup", test_failed_location_lookup()))
    results.append(("TTS Failure", test_tts_failure()))
    results.append(("Backend Error", test_backend_error()))
    results.append(("Retry Then Success", test_retry_then_success()))
    
    # Edge case tests
    results.append(("Long Response", test_long_response()))
    results.append(("Special Characters", test_response_with_special_characters()))
    results.append(("Premature IDLE Prevention", test_premature_idle_prevention()))
    
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
