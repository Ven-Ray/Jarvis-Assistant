"""Tests for web_search models."""

import pytest
from datetime import datetime, timezone
from web_search.models import SearchRequest, SearchResult


def test_search_request_creation():
    """Test creating a search request."""
    req = SearchRequest(
        request_id="test-1",
        original_query="What's the weather?"
    )
    
    assert req.request_id == "test-1"
    assert req.original_query == "What's the weather?"
    assert req.interpreted_query is None
    assert req.category is None
    assert req.requires_web_search is True


def test_search_result_valid():
    """Test valid search result."""
    result = SearchResult(
        request_id="test-1",
        category="weather",
        original_query="weather today",
        data="It's sunny and 25°C.",
        sources=[{"name": "Open-Meteo", "url": "https://api.open-meteo.com"}]
    )
    
    assert result.is_valid() is True
    assert result.category == "weather"
    assert len(result.sources) == 1


def test_search_result_invalid():
    """Test invalid search result with error."""
    result = SearchResult(
        request_id="test-2",
        original_query="weather today",
        data=None,
        error="API timeout"
    )
    
    assert result.is_valid() is False
    assert result.error == "API timeout"


def test_search_result_conflicts():
    """Test search result with conflicts."""
    result = SearchResult(
        request_id="test-3",
        original_query="stock price AAPL",
        data="$150.00",
        conflicts=["Source A says $149.50, Source B says $150.25"]
    )
    
    assert len(result.conflicts) == 1


def test_search_result_freshness():
    """Test search result freshness tracking."""
    result = SearchResult(
        request_id="test-4",
        original_query="latest news",
        data="Breaking: ...",
        freshness=30.0,  # 30 seconds old
        confidence=0.95
    )
    
    assert result.freshness == 30.0
    assert result.confidence == 0.95
