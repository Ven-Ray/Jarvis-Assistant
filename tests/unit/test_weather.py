"""
Tests for the Open-Meteo weather API integration.
Covers: geocoding, current conditions, forecasts, alerts, formatting, errors.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from weather import (
    WeatherAPI, format_weather_response, _compass_direction,
    WeatherError, WeatherTimeoutError, WeatherLocationError
)


class TestCompassDirection:
    """Test wind direction conversion."""
    
    def test_north(self):
        assert _compass_direction(0) == "N"
    
    def test_northeast(self):
        assert _compass_direction(45) == "NE"
    
    def test_east(self):
        assert _compass_direction(90) == "E"
    
    def test_southwest(self):
        assert _compass_direction(225) == "SW"
    
    def test_west(self):
        assert _compass_direction(270) == "W"
    
    def test_none(self):
        assert _compass_direction(None) == ""


class TestWeatherAPI:
    """Test the WeatherAPI client."""
    
    @pytest.fixture
    def api(self):
        return WeatherAPI(timeout=5)
    
    @patch('weather.requests.get')
    def test_geocode_success(self, mock_get, api):
        """Test successful geocoding."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{
                "latitude": 42.5,
                "longitude": -83.4,
                "name": "Farmington Hills",
                "admin1": "Michigan",
                "country": "United States of America",
                "timezone": "America/Detroit"
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api.geocode("Farmington Hills, MI")
        
        assert result["lat"] == 42.5
        assert result["lon"] == -83.4
        assert result["city"] == "Farmington Hills"
        assert result["region"] == "Michigan"
    
    @patch('weather.requests.get')
    def test_geocode_not_found(self, mock_get, api):
        """Test geocoding with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(WeatherLocationError) as exc_info:
            api.geocode("Nonexistent City")
        
        assert "No location found" in str(exc_info.value)
    
    @patch('weather.requests.get')
    def test_geocode_timeout(self, mock_get, api):
        """Test geocoding timeout."""
        import requests as req
        mock_get.side_effect = req.Timeout()
        
        with pytest.raises(WeatherTimeoutError):
            api.geocode("Farmington Hills")
    
    @patch('weather.requests.get')
    def test_current_weather_success(self, mock_get, api):
        """Test successful current weather retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {
                "time": "2026-09-14T15:30:00Z",
                "temperature_2m": 22.5,
                "relative_humidity_2m": 65,
                "apparent_temperature": 24.0,
                "is_day": 1,
                "precipitation": 0.0,
                "rain": 0.0,
                "snow": 0.0,
                "weather_code": 2,
                "cloud_cover": 35,
                "pressure_msl": 1015.0,
                "wind_speed_10m": 18.0,
                "wind_direction_10m": 270,
                "wind_gusts_10m": 25.0
            },
            "timezone": "America/Detroit"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api.get_current_weather(42.5, -83.4)
        
        assert result["temperature"] == 22.5
        assert result["humidity"] == 65
        assert result["conditions"] == "partly cloudy"
        assert result["wind_speed"] == 18.0
        assert isinstance(result["observation_time"], datetime)
    
    @patch('weather.requests.get')
    def test_forecast_success(self, mock_get, api):
        """Test successful forecast retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-09-14"],
                "temperature_2m_max": [28.0],
                "temperature_2m_min": [15.0],
                "precipitation_probability_max": [30],
                "weather_code": [2]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api.get_forecast(42.5, -83.4)
        
        assert result["high_temp"] == 28.0
        assert result["low_temp"] == 15.0
        assert result["precipitation_probability"] == 30
    
    @patch('weather.requests.get')
    def test_alerts_with_data(self, mock_get, api):
        """Test alerts retrieval with active alerts."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "alerts": [{
                "event": "Thunderstorm Warning",
                "severity": "severe",
                "headline": "Severe thunderstorms expected",
                "description": "Large hail and strong winds possible.",
                "start": "2026-09-14T18:00:00Z",
                "end": "2026-09-14T22:00:00Z"
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api.get_alerts(42.5, -83.4)
        
        assert len(result) == 1
        assert result[0]["event"] == "Thunderstorm Warning"
        assert result[0]["severity"] == "severe"
    
    @patch('weather.requests.get')
    def test_alerts_empty(self, mock_get, api):
        """Test alerts retrieval with no active alerts."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"alerts": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api.get_alerts(42.5, -83.4)
        
        assert len(result) == 0
    
    @patch('weather.requests.get')
    def test_complete_weather_query(self, mock_get, api):
        """Test complete weather query flow."""
        # Mock geocoding response
        geo_response = MagicMock()
        geo_response.json.return_value = {
            "results": [{
                "latitude": 42.5,
                "longitude": -83.4,
                "name": "Farmington Hills",
                "admin1": "Michigan",
                "country": "United States of America",
                "timezone": "America/Detroit"
            }]
        }
        
        # Mock current weather response
        current_response = MagicMock()
        current_response.json.return_value = {
            "current": {
                "time": "2026-09-14T15:30:00Z",
                "temperature_2m": 22.5,
                "relative_humidity_2m": 65,
                "apparent_temperature": 24.0,
                "is_day": 1,
                "precipitation": 0.0,
                "rain": 0.0,
                "snow": 0.0,
                "weather_code": 2,
                "cloud_cover": 35,
                "pressure_msl": 1015.0,
                "wind_speed_10m": 18.0,
                "wind_direction_10m": 270,
                "wind_gusts_10m": 25.0
            },
            "timezone": "America/Detroit"
        }
        
        # Mock forecast response
        forecast_response = MagicMock()
        forecast_response.json.return_value = {
            "daily": {
                "time": ["2026-09-14"],
                "temperature_2m_max": [28.0],
                "temperature_2m_min": [15.0],
                "precipitation_probability_max": [30],
                "weather_code": [2]
            }
        }
        
        # Mock alerts response
        alerts_response = MagicMock()
        alerts_response.json.return_value = {"alerts": []}
        
        for resp in [geo_response, current_response, forecast_response, alerts_response]:
            resp.raise_for_status.return_value = None
        
        mock_get.side_effect = [geo_response, current_response, forecast_response, alerts_response]
        
        result = api.get_weather("Farmington Hills, MI")
        
        assert result["location"]["city"] == "Farmington Hills"
        assert result["current"]["temperature"] == 22.5
        assert result["forecast"]["high_temp"] == 28.0
        assert len(result["alerts"]) == 0
        assert isinstance(result["retrieved_at"], datetime)


class TestFormatWeatherResponse:
    """Test weather response formatting."""
    
    def test_complete_response(self):
        """Test formatting with complete data."""
        weather_data = {
            "location": {
                "city": "Farmington Hills",
                "region": "Michigan",
                "country": "United States of America"
            },
            "current": {
                "temperature": 22.5,
                "apparent_temperature": 24.0,
                "conditions": "partly cloudy",
                "wind_speed": 18.0,
                "wind_direction": 270,
                "humidity": 65
            },
            "forecast": {
                "high_temp": 28.0,
                "low_temp": 15.0,
                "precipitation_probability": 30
            },
            "alerts": [],
            "retrieved_at": datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
        }
        
        response = format_weather_response(weather_data)
        
        assert "Farmington Hills" in response
        assert "partly cloudy" in response
        assert "Winds are 18 km/h from the W" in response
        assert "Humidity is 65%" in response
        assert "Today's high will be 28°C with a low of 15°C" in response
        assert "30% chance of precipitation" in response
        assert "no active weather alerts" in response
        assert "retrieved at 15:30 UTC" in response
    
    def test_response_with_alerts(self):
        """Test formatting with active weather alerts."""
        weather_data = {
            "location": {"city": "Chicago", "region": "Illinois"},
            "current": {
                "temperature": 15.0,
                "conditions": "thunderstorm",
                "wind_speed": 40.0,
                "wind_direction": 90,
                "humidity": 80
            },
            "forecast": None,
            "alerts": [{
                "event": "Severe Thunderstorm Warning",
                "severity": "severe",
                "headline": "Large hail and damaging winds expected."
            }],
            "retrieved_at": datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
        }
        
        response = format_weather_response(weather_data)
        
        assert "Severe Thunderstorm Warning" in response
        assert "severe alert" in response
    
    def test_missing_fields(self):
        """Test formatting with missing optional fields."""
        weather_data = {
            "location": {"city": "Unknown"},
            "current": {
                "temperature": 20.0,
                "conditions": "clear sky",
                "wind_speed": None,
                "wind_direction": None,
                "humidity": None
            },
            "forecast": None,
            "alerts": [],
            "retrieved_at": datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
        }
        
        response = format_weather_response(weather_data)
        
        assert "clear sky" in response
        assert "Winds are" not in response
        assert "Humidity is" not in response
    
    def test_apparent_temperature_difference(self):
        """Test that apparent temperature is shown when significantly different."""
        weather_data = {
            "location": {"city": "Phoenix"},
            "current": {
                "temperature": 35.0,
                "apparent_temperature": 42.0,
                "conditions": "clear sky",
                "wind_speed": 5.0,
                "wind_direction": 180,
                "humidity": 10
            },
            "forecast": None,
            "alerts": [],
            "retrieved_at": datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
        }
        
        response = format_weather_response(weather_data)
        
        assert "feels like 42°C" in response


class TestWeatherErrorHandling:
    """Test error handling scenarios."""
    
    @patch('weather.requests.get')
    def test_api_request_failure(self, mock_get):
        """Test handling of API request failures."""
        import requests as req
        
        api = WeatherAPI()
        
        # Geocoding fails
        geo_response = MagicMock()
        geo_response.json.return_value = {"results": []}
        geo_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [geo_response]
        
        with pytest.raises(WeatherError):
            api.get_weather("Nonexistent City")
