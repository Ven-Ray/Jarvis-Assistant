#!/usr/bin/env python3
"""
Test suite for Jarvis location detection, live info retrieval, and request classification.
Tests weather queries, news queries, timeout handling, and freshness validation.
"""

import sys
import os
import time
import json

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_location_detection():
    """Test 1: Location detection module."""
    print("\n=== Test 1: Location Detection ===")
    
    from location import LocationDetector
    
    detector = LocationDetector()
    
    # Test with short timeout to verify it doesn't hang indefinitely
    start_time = time.time()
    result = detector.get_current_location(timeout=5)
    elapsed = time.time() - start_time
    
    print(f"Location lookup took {elapsed:.1f} seconds")
    
    if result:
        print(f"✓ Location detected: {result['city']}, {result['region']}, {result['country']}")
        print(f"  Provider: {result.get('provider', 'unknown')}")
        
        # Test location string formatting
        loc_str = detector.get_location_string(result)
        print(f"  Formatted for search: '{loc_str}'")
    else:
        print("✗ Location detection failed or timed out")
    
    return result is not None


def test_freshness_validation():
    """Test 2: Result freshness validation."""
    print("\n=== Test 2: Freshness Validation ===")
    
    from jarvis import JarvisAssistant
    
    # Create a minimal instance just for the validation method
    assistant = type('MockJarvis', (), {})()
    assistant.validate_result_freshness = JarvisAssistant.validate_result_freshness.__get__(assistant)
    
    test_cases = [
        ("Current conditions: sunny, 75°F", True),
        ("Updated today at 2 PM - partly cloudy", True),
        ("Live weather report from this morning", True),
        ("2 weeks ago - Mostly clear. Lows around 70.", False),
        ("Last week's forecast showed rain", False),
        ("3 days ago the temperature was high", False),
    ]
    
    all_passed = True
    for text, expected_fresh in test_cases:
        is_fresh, reason = assistant.validate_result_freshness(text)
        status = "✓" if is_fresh == expected_fresh else "✗"
        print(f"{status} '{text[:40]}...' -> fresh={is_fresh} (expected {expected_fresh})")
        if is_fresh != expected_fresh:
            all_passed = False
    
    return all_passed


def test_request_classification():
    """Test 3: Request classification for live vs general queries."""
    print("\n=== Test 3: Request Classification ===")
    
    # Test keyword-based fallback (doesn't require LM Studio)
    from jarvis import JarvisAssistant
    
    assistant = type('MockJarvis', (), {})()
    assistant._keyword_web_search_fallback = JarvisAssistant._keyword_web_search_fallback.__get__(assistant)
    
    test_cases = [
        ("What is the weather?", True),
        ("Tell me about quantum physics", False),
        ("What's the latest news today?", True),
        ("How do I write a Python function?", False),
        ("Will it rain tomorrow in London?", True),
        ("What is 2+2?", False),
    ]
    
    all_passed = True
    for query, expected_search in test_cases:
        result = assistant._keyword_web_search_fallback(query.lower())
        status = "✓" if result["requires_web_search"] == expected_search else "✗"
        print(f"{status} '{query}' -> search={result['requires_web_search']} (expected {expected_search})")
        if result["requires_web_search"] != expected_search:
            all_passed = False
    
    return all_passed


def test_weather_query():
    """Test 4: Weather query with location detection."""
    print("\n=== Test 4: Weather Query ===")
    
    try:
        from jarvis import JarvisAssistant
        
        assistant = JarvisAssistant()
        
        # Test current weather (should auto-detect location)
        print("Testing: 'What is the weather?'")
        response, is_exit = assistant.get_response_text("What is the weather?")
        
        if response:
            print(f"✓ Response received ({len(response)} chars)")
            print(f"  Preview: {response[:100]}...")
            
            # Check that it doesn't contain obviously outdated info
            if "2 weeks ago" in response.lower() or "last week" in response.lower():
                print("✗ Response appears to contain outdated information")
                return False
        else:
            print("✗ No response received")
            return False
        
        # Test weather with explicit location
        print("\nTesting: 'What is the weather in London?'")
        response2, _ = assistant.get_response_text("What is the weather in London?")
        
        if response2 and "london" in response2.lower():
            print(f"✓ Location-specific response received")
        else:
            print("⚠ Response may not be location-specific")
            
    except Exception as e:
        print(f"✗ Error during weather query test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_news_query():
    """Test 5: Live news query."""
    print("\n=== Test 5: Live News Query ===")
    
    try:
        from jarvis import JarvisAssistant
        
        assistant = JarvisAssistant()
        
        print("Testing: 'Give me the latest news.'")
        response, is_exit = assistant.get_response_text("Give me the latest news.")
        
        if response:
            print(f"✓ Response received ({len(response)} chars)")
            print(f"  Preview: {response[:100]}...")
            
            # Check for freshness indicators
            has_freshness = any(term in response.lower() for term in 
                               ["today", "current", "latest", "recent"])
            if has_freshness:
                print("✓ Response contains freshness indicators")
            else:
                print("⚠ Response may not indicate recency")
        else:
            print("✗ No response received")
            return False
            
    except Exception as e:
        print(f"✗ Error during news query test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_general_question():
    """Test 6: General question should not trigger location detection."""
    print("\n=== Test 6: General Question (No Location) ===")
    
    try:
        from jarvis import JarvisAssistant
        
        assistant = JarvisAssistant()
        
        # Clear any cached location to verify it's not fetched for general questions
        assistant.location_detector.clear_cache()
        
        print("Testing: 'What is the capital of France?'")
        response, is_exit = assistant.get_response_text("What is the capital of France?")
        
        if response and "paris" in response.lower():
            print(f"✓ Correct answer received without location lookup")
            
            # Verify no location was cached (meaning it wasn't fetched)
            if not assistant.location_detector._cached_location:
                print("✓ No unnecessary location detection triggered")
            else:
                print("⚠ Location may have been detected unnecessarily")
        else:
            print(f"✗ Unexpected response: {response}")
            
    except Exception as e:
        print(f"✗ Error during general question test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Jarvis Live Information & Location Detection Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run unit tests first (don't require network/LM Studio)
    results.append(("Location Detection", test_location_detection()))
    results.append(("Freshness Validation", test_freshness_validation()))
    results.append(("Request Classification", test_request_classification()))
    
    # Integration tests (require LM Studio and network)
    print("\n" + "=" * 60)
    print("Integration Tests (require LM Studio at localhost:1234)")
    print("=" * 60)
    
    results.append(("Weather Query", test_weather_query()))
    results.append(("Live News Query", test_news_query()))
    results.append(("General Question", test_general_question()))
    
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
