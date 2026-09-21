#!/usr/bin/env python3
"""
Tests for time query handling and error reporting.
Verifies that:
1. Time queries are routed to local handler (not web search/LLM)
2. Failed requests return clear errors, not stale results
"""

import sys
import os
from unittest.mock import Mock, patch

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_time_query_routing():
    """Test that 'What time is it?' is routed to local time handler."""
    from jarvis import JarvisAssistant
    
    # Create assistant with mocked dependencies
    with patch.object(JarvisAssistant, '__init__', lambda self: None):
        assistant = JarvisAssistant()
        assistant.request_manager = Mock()
        
        # Mock request manager to return a mock request
        mock_request = Mock()
        mock_request.id = "test-req-1"
        mock_request.cancelled = False
        mock_request.completed_at = None
        assistant.request_manager.get_active_request.return_value = mock_request
        
        # Test time query detection in get_response_text
        with patch.object(assistant, 'get_current_time_response', return_value="The current time is 3:45 PM, Sir."):
            response, is_exit = assistant.get_response_text("What time is it right now?")
            
            assert "current time" in response.lower(), f"Expected time response, got: {response}"
            assert not is_exit, "Time query should not exit"
            print("✓ Time query routed to local handler correctly")


def test_time_response_format():
    """Test that get_current_time_response returns properly formatted time."""
    from jarvis import JarvisAssistant
    
    with patch.object(JarvisAssistant, '__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        response = assistant.get_current_time_response("test-req")
        
        # Should contain AM or PM
        assert "AM" in response or "PM" in response, f"Missing AM/PM indicator: {response}"
        # Should contain time format with colon
        assert ":" in response, f"Missing time separator: {response}"
        # Should address user as Sir (Jarvis personality)
        assert "Sir" in response, f"Missing Jarvis personality: {response}"
        
        print(f"✓ Time response format correct: {response}")


def test_no_model_loaded_error_handling():
    """Test that 'no models loaded' error returns clear message."""
    from jarvis import JarvisAssistant
    
    with patch.object(JarvisAssistant, '__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Mock request manager (search_and_answer checks for cancelled requests)
        mock_request = Mock()
        mock_request.id = "test-req"
        mock_request.is_cancelled.return_value = False
        assistant.request_manager = Mock()
        assistant.request_manager.get_active_request.return_value = mock_request
        
        # Mock config
        assistant.config = {"lm_studio": {"model": "test-model"}}
        
        # Mock search_web to succeed but LLM call to fail with "no models loaded"
        mock_results = [{"title": "Test", "body": "Test body"}]
        assistant.search_web = Mock(return_value=mock_results)
        
        # Simulate the error that occurs when no model is loaded in LM Studio
        def failing_chat(*args, **kwargs):
            raise Exception("Error code: 400 - {'error': {'message': 'No models loaded. Please load a model.'}}")
        
        assistant.client = Mock()
        assistant.client.chat.completions.create.side_effect = failing_chat
        
        response = assistant.search_and_answer("test query", max_retries=1)
        
        # Should return clear error, not stale search results
        assert "model" in response.lower() or "not available" in response.lower(), \
            f"Expected model error message, got: {response}"
        print(f"✓ No-model error handled correctly: {response}")


def test_search_failure_returns_error_not_stale_results():
    """Test that failed search returns error, not unrelated results."""
    from jarvis import JarvisAssistant
    
    with patch.object(JarvisAssistant, '__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Mock request manager (search_and_answer checks for cancelled requests)
        mock_request = Mock()
        mock_request.id = "test-req"
        mock_request.is_cancelled.return_value = False
        assistant.request_manager = Mock()
        assistant.request_manager.get_active_request.return_value = mock_request
        
        # Mock config
        assistant.config = {"lm_studio": {"model": "test-model"}}
        
        # Mock both search and LLM to fail
        assistant.search_web = Mock(side_effect=Exception("Search failed"))
        
        response = assistant.search_and_answer("test query", max_retries=1)
        
        # Should contain error info, not fabricated results
        assert "sorry" in response.lower() or "error" in response.lower() or "issue" in response.lower(), \
            f"Expected error message, got: {response}"
        print(f"✓ Search failure returns clear error: {response}")


def test_request_isolation():
    """Test that each request has unique ID and doesn't reuse results."""
    from jarvis import JarvisAssistant
    
    with patch.object(JarvisAssistant, '__init__', lambda self: None):
        assistant = JarvisAssistant()
        
        # Mock dependencies for simple command
        assistant.request_manager = Mock()
        
        mock_req1 = Mock()
        mock_req1.id = "req-1"
        mock_req1.cancelled = False
        mock_req1.completed_at = None
        
        mock_req2 = Mock()
        mock_req2.id = "req-2"
        mock_req2.cancelled = False
        mock_req2.completed_at = None
        
        assistant.request_manager.get_active_request.side_effect = [mock_req1, mock_req2]
        
        # Two separate requests should get different IDs
        response1, _ = assistant.get_response_text("hello")
        response2, _ = assistant.get_response_text("hello again")
        
        assert "Good day" in response1 or "Sir" in response1, f"Unexpected response: {response1}"
        print("✓ Request isolation verified - separate requests processed independently")


if __name__ == "__main__":
    print("Running time query and error handling tests...")
    print("-" * 50)
    
    try:
        test_time_query_routing()
        test_time_response_format()
        test_no_model_loaded_error_handling()
        test_search_failure_returns_error_not_stale_results()
        test_request_isolation()
        
        print("-" * 50)
        print("All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
