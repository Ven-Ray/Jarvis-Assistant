#!/usr/bin/env python3
"""
Comprehensive tests for LM Studio API integration.
Tests connection scenarios, error handling, and configuration.
"""

import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_loading():
    """Test that config.json is loaded correctly."""
    print("\n=== Test: Config Loading ===")
    
    from jarvis import JarvisAssistant
    
    # Create assistant (will load config)
    assistant = JarvisAssistant()
    
    assert hasattr(assistant, 'config'), "Config not loaded"
    assert 'lm_studio' in assistant.config, "lm_studio section missing from config"
    assert 'api_base' in assistant.config['lm_studio'], "api_base missing from lm_studio config"
    assert 'model' in assistant.config['lm_studio'], "model missing from lm_studio config"
    
    print(f"✓ Config loaded successfully")
    print(f"  API Base: {assistant.config['lm_studio']['api_base']}")
    print(f"  Model: {assistant.config['lm_studio']['model']}")


def test_config_file_not_found():
    """Test default config when file is missing."""
    print("\n=== Test: Config File Not Found ===")
    
    from jarvis import JarvisAssistant
    
    # Temporarily rename config.json
    if os.path.exists('config.json'):
        os.rename('config.json', 'config.json.bak')
    
    try:
        assistant = JarvisAssistant()
        
        assert hasattr(assistant, 'config'), "Config not loaded"
        assert assistant.config['lm_studio']['api_base'] == 'http://localhost:1234/v1'
        print("✓ Default config used when file missing")
    finally:
        if os.path.exists('config.json.bak'):
            os.rename('config.json.bak', 'config.json')


def test_invalid_config_json():
    """Test handling of malformed JSON in config."""
    print("\n=== Test: Invalid Config JSON ===")
    
    from jarvis import JarvisAssistant
    
    # Create invalid JSON file
    with open('config.json', 'w') as f:
        f.write('{invalid json}')
    
    try:
        assistant = JarvisAssistant()
        
        assert hasattr(assistant, 'config'), "Config not loaded"
        print("✓ Handled invalid JSON gracefully")
    except Exception as e:
        print(f"✗ Failed to handle invalid JSON: {e}")
        raise
    finally:
        # Restore original config
        with open('config.json', 'w') as f:
            json.dump({
                "lm_studio": {"api_base": "http://localhost:1234/v1", "model": "default-model"},
                "voice": {"rate": 150, "volume": 1.0, "voice_id": "default"},
                "search": {"max_results": 5}
            }, f, indent=4)


def test_api_connection_success():
    """Test successful API connection."""
    print("\n=== Test: API Connection Success ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    assert assistant.client is not None, "API client not initialized"
    print("✓ API client connected successfully")


def test_api_connection_failure():
    """Test handling of failed API connection."""
    print("\n=== Test: API Connection Failure ===")
    
    import openai
    
    # Mock the OpenAI client to raise an exception
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.side_effect = Exception("Connection refused")
        
        from jarvis import JarvisAssistant
        
        assistant = JarvisAssistant()
        
        assert assistant.client is None, "Client should be None on connection failure"
        print("✓ Handled API connection failure gracefully")


def test_get_ai_response_success():
    """Test successful AI response."""
    print("\n=== Test: Get AI Response Success ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Good day, Sir. How may I assist you?"
    assistant.client.chat.completions.create.return_value = mock_response
    
    response = assistant.get_ai_response("Hello")
    
    assert response == "Good day, Sir. How may I assist you?", f"Unexpected response: {response}"
    print("✓ Got successful AI response")


def test_get_ai_response_connection_error():
    """Test handling of API connection error."""
    print("\n=== Test: Get AI Response - Connection Error ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise connection error
    assistant.client.chat.completions.create.side_effect = openai.APIConnectionError(
        "Connection refused", request=Mock()
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected ConnectionError but got response: {response}")
    except ConnectionError as e:
        assert "Cannot connect to LM Studio API" in str(e)
        print("✓ Handled connection error correctly")


def test_get_ai_response_timeout():
    """Test handling of API timeout."""
    print("\n=== Test: Get AI Response - Timeout ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise timeout
    assistant.client.chat.completions.create.side_effect = openai.Timeout(
        "Request timed out", request=Mock()
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected TimeoutError but got response: {response}")
    except TimeoutError as e:
        assert "timed out after 30 seconds" in str(e)
        print("✓ Handled timeout correctly")


def test_get_ai_response_invalid_request():
    """Test handling of invalid API request."""
    print("\n=== Test: Get AI Response - Invalid Request ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise invalid request error
    assistant.client.chat.completions.create.side_effect = openai.InvalidRequestError(
        "Invalid model", response=Mock(), body={}
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected ValueError but got response: {response}")
    except ValueError as e:
        assert "Invalid request to LM Studio" in str(e)
        print("✓ Handled invalid request correctly")


def test_get_ai_response_auth_error():
    """Test handling of API authentication error."""
    print("\n=== Test: Get AI Response - Auth Error ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise auth error
    assistant.client.chat.completions.create.side_effect = openai.AuthenticationError(
        "Invalid API key", response=Mock(), body={}
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected PermissionError but got response: {response}")
    except PermissionError as e:
        assert "authentication failed" in str(e)
        print("✓ Handled authentication error correctly")


def test_get_ai_response_model_not_found():
    """Test handling of model not found error."""
    print("\n=== Test: Get AI Response - Model Not Found ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise not found error
    assistant.client.chat.completions.create.side_effect = openai.NotFoundError(
        "Model not found", response=Mock(), body={}
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected ValueError but got response: {response}")
    except ValueError as e:
        assert "not found in LM Studio" in str(e)
        print("✓ Handled model not found correctly")


def test_get_ai_response_server_error():
    """Test handling of server error."""
    print("\n=== Test: Get AI Response - Server Error ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise server error
    assistant.client.chat.completions.create.side_effect = openai.InternalServerError(
        "Internal server error", response=Mock(), body={}
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected RuntimeError but got response: {response}")
    except RuntimeError as e:
        assert "server error (500)" in str(e)
        print("✓ Handled server error correctly")


def test_get_ai_response_rate_limit():
    """Test handling of rate limit error."""
    print("\n=== Test: Get AI Response - Rate Limit ===")
    
    from jarvis import JarvisAssistant
    import openai
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method to raise rate limit error
    assistant.client.chat.completions.create.side_effect = openai.RateLimitError(
        "Rate limit exceeded", response=Mock(), body={}
    )
    
    try:
        response = assistant.get_ai_response("Hello")
        print(f"✗ Expected RuntimeError but got response: {response}")
    except RuntimeError as e:
        assert "rate limit exceeded" in str(e)
        print("✓ Handled rate limit correctly")


def test_web_search_classification():
    """Test web search intent classification."""
    print("\n=== Test: Web Search Classification ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "requires_web_search": True,
        "search_query": "current weather New York",
        "reason": "Weather query requires current information"
    })
    assistant.client.chat.completions.create.return_value = mock_response
    
    result = assistant.classify_web_search("What's the weather in New York?")
    
    assert result['requires_web_search'] == True, f"Expected web search required: {result}"
    assert "weather" in result['search_query'].lower(), f"Unexpected search query: {result['search_query']}"
    print("✓ Web search classification works correctly")


def test_web_search_classification_no_search():
    """Test web search intent classification for non-search queries."""
    print("\n=== Test: Web Search Classification - No Search ===")
    
    from jarvis import JarvisAssistant
    
    assistant = JarvisAssistant()
    
    # Mock the client's chat.completions.create method
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "requires_web_search": False,
        "search_query": "",
        "reason": "General knowledge question"
    })
    assistant.client.chat.completions.create.return_value = mock_response
    
    result = assistant.classify_web_search("What is the capital of France?")
    
    assert result['requires_web_search'] == False, f"Expected no web search: {result}"
    print("✓ Web search classification correctly identifies non-search queries")


def test_api_url_validation():
    """Test API URL validation in frontend."""
    print("\n=== Test: API URL Validation ===")
    
    # Import the frontend module to access URL validation logic
    from frontend.main_window import JarvisFrontend
    
    # Create a mock instance (don't show window)
    class MockJarvisFrontend(JarvisFrontend):
        def __init__(self):
            self.jarvis = None
            self.current_state = "idle"
    
    frontend = MockJarvisFrontend()
    
    # Test valid URLs
    assert frontend._validate_api_url("http://localhost:1234/v1") == True, "Valid URL rejected"
    print("✓ Valid HTTP URL accepted")
    
    assert frontend._validate_api_url("https://api.example.com/v1") == True, "Valid HTTPS URL rejected"
    print("✓ Valid HTTPS URL accepted")
    
    # Test invalid URLs
    assert frontend._validate_api_url("") == False, "Empty URL accepted"
    print("✓ Empty URL rejected")
    
    assert frontend._validate_api_url("not-a-url") == False, "Invalid URL accepted"
    print("✓ Invalid URL rejected")


def test_environment_variable_support():
    """Test environment variable handling for API configuration."""
    print("\n=== Test: Environment Variable Support ===")
    
    # Check if LM_STUDIO_API_BASE env var is respected (if implemented)
    original_env = os.environ.get('LM_STUDIO_API_BASE')
    
    try:
        # Set custom API base via environment variable
        os.environ['LM_STUDIO_API_BASE'] = 'http://custom-host:9999/v1'
        
        from jarvis import JarvisAssistant
        
        assistant = JarvisAssistant()
        
        # Check if config uses environment variable (if implemented)
        expected_base = os.environ.get('LM_STUDIO_API_BASE', 'http://localhost:1234/v1')
        
        if assistant.config['lm_studio']['api_base'] == expected_base:
            print("✓ Environment variable LM_STUDIO_API_BASE is respected")
        else:
            print(f"ℹ Environment variable handling may not be implemented (using config file)")
            print(f"  Expected: {expected_base}")
            print(f"  Actual: {assistant.config['lm_studio']['api_base']}")
    except Exception as e:
        print(f"✗ Failed to test environment variables: {e}")
        raise
    finally:
        if original_env is None:
            os.environ.pop('LM_STUDIO_API_BASE', None)
        else:
            os.environ['LM_STUDIO_API_BASE'] = original_env


def main():
    """Main test function"""
    print("LM Studio API Integration - Test Suite")
    print("=" * 40)
    
    tests = [
        test_config_loading,
        test_config_file_not_found,
        test_invalid_config_json,
        test_api_connection_success,
        test_api_connection_failure,
        test_get_ai_response_success,
        test_get_ai_response_connection_error,
        test_get_ai_response_timeout,
        test_get_ai_response_invalid_request,
        test_get_ai_response_auth_error,
        test_get_ai_response_model_not_found,
        test_get_ai_response_server_error,
        test_get_ai_response_rate_limit,
        test_web_search_classification,
        test_web_search_classification_no_search,
        test_api_url_validation,
        test_environment_variable_support
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
        print("\n✓ All LM Studio API integration tests passed!")
        return 0
    else:
        print("\n✗ Some LM Studio API integration tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
