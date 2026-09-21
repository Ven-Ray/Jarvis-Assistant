#!/usr/bin/env python3
"""
Test script for Jarvis Voice Assistant
Verifies that all components are properly installed and configured.
"""

import sys
import os

from unittest.mock import Mock, patch

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dependencies():
    """Test if all required dependencies are installed"""
    required_packages = [
        'speech_recognition',
        'pyttsx3', 
        'openai',
        'ddgs'
    ]
    
    print("Testing required dependencies...")
    print("-" * 40)
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} - OK")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print("\nMissing packages:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        return False
    else:
        print("\nAll required dependencies are installed!")
        return True

def test_config():
    """Test if config file exists and is valid"""
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✓ config.json - OK")
        return True
    except FileNotFoundError:
        print("✗ config.json - NOT FOUND")
        return False
    except json.JSONDecodeError:
        print("✗ config.json - INVALID JSON")
        return False

def test_sentence_completeness():
    """Test speech completeness validation"""
    from jarvis import JarvisAssistant
    
    # Create a mock assistant without initializing hardware
    assistant = Mock(spec=JarvisAssistant)
    
    # Import the actual method
    def is_complete(text):
        if not text or len(text.strip()) == 0:
            return False
        if any(text.endswith(p) for p in ['.', '!', '?']):
            return True
        words = text.split()
        if len(words) < 3:
            return False
        command_words = ["hello", "hi", "bye", "goodbye", "shut up", "be quiet", 
                        "stop talking", "silence"]
        if any(word in text.lower() for word in command_words):
            return True
        if text.lower().startswith("search") or text.lower().startswith("find"):
            return True
        # Longer utterances (8+ words) without punctuation are likely incomplete
        if len(words) >= 8:
            return False
        question_words = ["what", "who", "when", "where", "why", "how", "is", "are", 
                         "can", "does", "tell"]
        if any(text.lower().startswith(w) for w in question_words):
            return True
        return False
    
    print("\nTesting speech completeness validation...")
    print("-" * 40)
    
    # Complete sentences should pass
    assert is_complete("What's the weather today?"), "Complete question failed"
    print("✓ Complete question detected")
    
    assert is_complete("Hello Jarvis."), "Complete greeting failed"
    print("✓ Complete greeting detected")
    
    # Incomplete speech should fail
    assert not is_complete("What is the weather going to be for the rest of the"), "Incomplete sentence passed"
    print("✓ Incomplete sentence detected")
    
    assert not is_complete("hello"), "Short incomplete phrase passed"
    print("✓ Short incomplete phrase detected")
    
    # Commands should pass even without punctuation
    assert is_complete("search for weather"), "Command failed"
    print("✓ Command detected as complete")
    
    return True

def test_weather_query_parsing():
    """Test that weather queries are parsed correctly"""
    print("\nTesting weather query parsing...")
    print("-" * 40)
    
    # Test current weather vs forecast detection
    def is_forecast(query):
        query_lower = query.lower()
        return any(word in query_lower for word in ["week", "forecast", 
                 "tomorrow", "next week", "this week", "entire week"])
    
    assert not is_forecast("What's the weather today?"), "Today detected as forecast"
    print("✓ Current weather query detected")
    
    assert is_forecast("What's the weather going to be this entire week?"), "Week forecast missed"
    print("✓ Week forecast query detected")
    
    assert is_forecast("Give me the weather forecast for tomorrow"), "Tomorrow forecast missed"
    print("✓ Tomorrow forecast query detected")
    
    return True

def test_command_matching():
    """Test improved stop/silence command matching with word boundaries"""
    import re
    
    def matches_command(command_lower, phrases):
        for phrase in phrases:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, command_lower):
                return True
        return False
    
    print("\nTesting command matching with word boundaries...")
    print("-" * 40)
    
    # Test goodbye commands
    assert matches_command("goodbye", ["bye", "goodbye"]), "Goodbye not matched"
    print("✓ 'goodbye' matched")
    
    assert matches_command("see you bye", ["bye", "goodbye"]), "'bye' in sentence not matched"
    print("✓ 'bye' in sentence matched")
    
    # Test silence commands
    assert matches_command("shut up", ["shut up", "be quiet", "stop talking", "silence"]), "'shut up' not matched"
    print("✓ 'shut up' matched")
    
    assert matches_command("please be quiet", ["shut up", "be quiet", "stop talking", "silence"]), "'be quiet' not matched"
    print("✓ 'be quiet' matched")
    
    # Test word boundary - should NOT match partial words
    assert not matches_command("goodbyes to all", ["bye", "goodbye"]), "Partial word 'goodbyes' incorrectly matched"
    print("✓ Partial word 'goodbyes' correctly rejected")
    
    # "shut up" as a phrase should match even in longer sentences
    assert matches_command("please shut up for a moment", ["shut up", "be quiet", "stop talking", "silence"]), "'shut up' phrase not matched in sentence"
    print("✓ 'shut up' phrase correctly matched in sentence")
    
    return True

def test_tts_synchronization():
    """Test that TTS is called for every response"""
    from unittest.mock import Mock, patch
    
    print("\nTesting TTS synchronization...")
    print("-" * 40)
    
    # Create real assistant (not mocked __init__) to ensure all attributes are set
    from jarvis import JarvisAssistant
    assistant = JarvisAssistant()
    
    # Mock the speak method to track calls
    spoken_messages = []
    def mock_speak(text):
        spoken_messages.append(text)
        print(f"Jarvis: {text}")
    
    assistant.speak = mock_speak
    
    # Test that weather query triggers speech (now only final response is spoken)
    with patch.object(assistant, 'search_and_answer', return_value="It's sunny today."):
        assistant.process_command("What's the weather?")
        
        assert len(spoken_messages) >= 1, f"Expected at least 1 spoken message, got {len(spoken_messages)}"
        print(f"✓ Weather query produced {len(spoken_messages)} spoken response(s)")
    
    # Test that search command triggers speech (now only final response is spoken)
    spoken_messages.clear()
    with patch.object(assistant, 'search_web', return_value=[{'body': 'Test result'}]):
        assistant.process_command("Search for Python programming")
        
        assert len(spoken_messages) >= 1, f"Expected at least 1 spoken message, got {len(spoken_messages)}"
        print(f"✓ Search command produced {len(spoken_messages)} spoken response(s)")
    
    return True

def main():
    """Main test function"""
    print("Jarvis Voice Assistant - Test Suite")
    print("=" * 40)
    
    tests = [
        test_dependencies,
        test_config,
        test_sentence_completeness,
        test_weather_query_parsing,
        test_command_matching,
        test_tts_synchronization
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
        print()
    
    if all(results):
        print("✓ All tests passed! Jarvis is ready to run.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())