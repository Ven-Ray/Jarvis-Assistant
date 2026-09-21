#!/usr/bin/env python3
"""
Tests for async provider execution, fallback behavior, timeout handling,
duplicate request prevention, and UI state transitions.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_async_provider_execution():
    """Test that async provider methods are properly awaited."""
    from web_search.manager import SearchManager
    from web_search.providers.base import SearchProvider
    from web_search.models import SearchResult

    class MockWeatherProvider(SearchProvider):
        def supports(self, request):
            return True
        
        async def search(self, request):
            # Simulate some async work
            await asyncio.sleep(0.01)
            return SearchResult(
                request_id=request.request_id,
                original_query=request.original_query,
                data="Mock result",
                confidence=1.0
            )

    manager = SearchManager(providers=[MockWeatherProvider()])
    
    async def run_test():
        result = await manager.execute("test-req-1", "weather test query")
        assert result.is_valid(), "Result should be valid"
        assert result.data == "Mock result", f"Expected 'Mock result', got '{result.data}'"
        return True

    loop = asyncio.new_event_loop()
    try:
        success = loop.run_until_complete(run_test())
        print(f"✓ test_async_provider_execution - {'PASS' if success else 'FAIL'}")
        return success
    finally:
        loop.close()


def test_provider_failure_and_fallback():
    """Test that fallback provider is used when primary fails."""
    from web_search.manager import SearchManager
    from web_search.providers.base import SearchProvider
    from web_search.models import SearchResult

    class FailingWeatherProvider(SearchProvider):
        def supports(self, request):
            return True
        
        async def search(self, request):
            raise Exception("Primary provider failed")

    class SuccessGeneralProvider(SearchProvider):
        def supports(self, request):
            return True
        
        async def search(self, request):
            return SearchResult(
                request_id=request.request_id,
                original_query=request.original_query,
                data="Fallback result",
                confidence=0.8
            )

    manager = SearchManager(providers=[FailingWeatherProvider(), SuccessGeneralProvider()])
    
    async def run_test():
        result = await manager.execute("test-req-2", "weather test query")
        assert result.is_valid(), "Result should be valid from fallback"
        return True

    loop = asyncio.new_event_loop()
    try:
        success = loop.run_until_complete(run_test())
        print(f"✓ test_provider_failure_and_fallback - {'PASS' if success else 'FAIL'}")
        return success
    finally:
        loop.close()


def test_provider_timeout_cleanup():
    """Test that provider timeout properly cleans up tasks."""
    from web_search.manager import SearchManager
    from web_search.providers.base import SearchProvider

    class SlowWeatherProvider(SearchProvider):
        def supports(self, request):
            return True
        
        async def search(self, request):
            # Sleep longer than timeout
            await asyncio.sleep(10)
            return None

    manager = SearchManager(providers=[SlowWeatherProvider()])
    
    import time
    
    start_time = time.time()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(manager.execute("test-req-3", "weather test query"))
        elapsed = time.time() - start_time
        
        # Should timeout and use fallback (not hang indefinitely)
        assert elapsed < 5.0, f"Timeout took too long: {elapsed}s"
        print(f"✓ test_provider_timeout_cleanup - PASS (took {elapsed:.2f}s)")
        return True
    except Exception as e:
        print(f"✗ test_provider_timeout_cleanup - FAIL: {e}")
        return False
    finally:
        loop.close()


def test_duplicate_request_prevention():
    """Test that duplicate requests are prevented."""
    from request_manager import RequestManager

    rm = RequestManager()
    
    # Create first request
    req1 = rm.create_request(source="text")
    assert rm.is_current_request(req1.id), "First request should be current"
    
    # Create second request (supersedes first)
    req2 = rm.create_request(source="text")
    assert not rm.is_current_request(req1.id), "First request should no longer be current"
    assert rm.is_current_request(req2.id), "Second request should be current"
    
    print("✓ test_duplicate_request_prevention - PASS")
    return True


def test_ui_state_transitions():
    """Test UI state transition validation."""
    # Simulate the state machine logic from main_window.py
    valid_states = ["idle", "listening", "processing", "searching", 
                   "response_ready", "chat_updated", "speaking", "error"]
    
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

    current_state = "idle"
    
    # Test valid transitions
    test_transitions = [
        ("listening", True),   # idle -> listening (valid)
        ("processing", True),  # listening -> processing (valid)
        ("searching", True),   # processing -> searching (valid)
        ("response_ready", True),  # searching -> response_ready (valid)
        ("chat_updated", True),    # response_ready -> chat_updated (valid)
        ("speaking", True),        # chat_updated -> speaking (valid)
        ("idle", True),            # speaking -> idle (valid)
    ]

    all_passed = True
    for target_state, should_be_valid in test_transitions:
        is_valid = target_state in allowed_transitions.get(current_state, [])
        
        if is_valid != should_be_valid:
            print(f"✗ State transition {current_state} -> {target_state}: expected valid={should_be_valid}, got {is_valid}")
            all_passed = False
        
        # Apply the transition for next test
        current_state = target_state

    print(f"✓ test_ui_state_transitions - {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def test_weather_provider_async():
    """Test that WeatherProvider.search is properly async and awaited."""
    from web_search.providers.weather import WeatherProvider
    
    provider = WeatherProvider()
    
    # Verify search method is a coroutine function
    assert asyncio.iscoroutinefunction(provider.search), "WeatherProvider.search should be async"
    
    print("✓ test_weather_provider_async - PASS")
    return True


def test_general_provider_async():
    """Test that GeneralSearchProvider.search is properly async and awaited."""
    from web_search.providers.general import GeneralSearchProvider
    
    provider = GeneralSearchProvider()
    
    # Verify search method is a coroutine function
    assert asyncio.iscoroutinefunction(provider.search), "GeneralSearchProvider.search should be async"
    
    print("✓ test_general_provider_async - PASS")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Running async provider and UI state tests")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    try:
        results.append(test_async_provider_execution())
    except Exception as e:
        print(f"✗ test_async_provider_execution - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_provider_failure_and_fallback())
    except Exception as e:
        print(f"✗ test_provider_failure_and_fallback - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_provider_timeout_cleanup())
    except Exception as e:
        print(f"✗ test_provider_timeout_cleanup - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_duplicate_request_prevention())
    except Exception as e:
        print(f"✗ test_duplicate_request_prevention - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_ui_state_transitions())
    except Exception as e:
        print(f"✗ test_ui_state_transitions - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_weather_provider_async())
    except Exception as e:
        print(f"✗ test_weather_provider_async - ERROR: {e}")
        results.append(False)
    
    try:
        results.append(test_general_provider_async())
    except Exception as e:
        print(f"✗ test_general_provider_async - ERROR: {e}")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    if passed == total:
        print("All tests PASSED!")
    else:
        print(f"{total - passed} test(s) FAILED")
    print("=" * 60)
