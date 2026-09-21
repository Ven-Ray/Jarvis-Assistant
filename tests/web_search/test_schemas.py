"""Tests for Pydantic schema models."""

import pytest
from datetime import datetime, timezone
from web_search.schemas import (
    LocationInfo, CurrentConditions, DailyForecast, WeatherAlert,
    WeatherResult, StockPriceResult, LocalBusinessResult, RetrievalMetadata
)


class TestLocationInfo:
    def test_basic_creation(self):
        loc = LocationInfo(city="Detroit", region="Michigan", country="US")
        assert loc.city == "Detroit"
        assert loc.to_string() == "Detroit, Michigan, US"

    def test_empty_location(self):
        loc = LocationInfo()
        assert loc.to_string() == ""


class TestCurrentConditions:
    def test_weather_code_decoding(self):
        conditions = CurrentConditions(
            temperature=25.0,
            weather_code=0,
            observation_time=datetime.now(timezone.utc)
        )
        assert conditions.conditions == "unknown"  # Decoded by provider


class TestWeatherResult:
    def test_complete_weather_result(self):
        location = LocationInfo(city="Detroit", region="Michigan")
        current = CurrentConditions(
            temperature=20.0,
            observation_time=datetime.now(timezone.utc)
        )
        
        result = WeatherResult(
            location=location,
            current=current,
            retrieved_at=datetime.now(timezone.utc),
            source="open-meteo"
        )
        
        assert result.location.city == "Detroit"
        assert result.current.temperature == 20.0
        assert result.source == "open-meteo"


class TestStockPriceResult:
    def test_stock_price_validation(self):
        result = StockPriceResult(
            symbol="AAPL",
            name="Apple Inc.",
            price=150.50,
            change=2.30,
            change_percent=1.54,
            timestamp=datetime.now(timezone.utc),
            source="alpha-vantage"
        )
        
        assert result.symbol == "AAPL"
        assert result.price == 150.50


class TestRetrievalMetadata:
    def test_metadata_creation(self):
        meta = RetrievalMetadata(
            request_id="req-1-test",
            original_query="weather in Detroit",
            provider_name="open_meteo_api"
        )
        
        assert meta.request_id == "req-1-test"
        assert meta.confidence == 1.0
