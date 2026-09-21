"""
Pydantic schema models for retrieval layer validation.
Defines typed schemas for weather, stock prices, and location-based search results.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    """Geographic location information."""
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    timezone: str = ""
    provider: str = ""

    def to_string(self) -> str:
        """Format location as readable string."""
        parts = [p for p in [self.city, self.region, self.country] if p]
        return ", ".join(parts)


class CurrentConditions(BaseModel):
    """Current weather conditions."""
    temperature: Optional[float] = None
    apparent_temperature: Optional[float] = None
    humidity: Optional[float] = None
    is_day: Optional[bool] = None
    precipitation: Optional[float] = None
    rain: Optional[float] = None
    snow: Optional[float] = None
    weather_code: Optional[int] = None
    conditions: str = "unknown"
    cloud_cover: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_gusts: Optional[float] = None
    observation_time: datetime
    timezone: str = ""


class DailyForecast(BaseModel):
    """Daily weather forecast."""
    date: str
    high_temp: Optional[float] = None
    low_temp: Optional[float] = None
    precipitation_probability: Optional[float] = None
    weather_code: Optional[int] = None
    conditions: str = "unknown"
    max_wind_speed: Optional[float] = None


class WeatherAlert(BaseModel):
    """Weather alert information."""
    event: str = ""
    severity: str = ""
    headline: str = ""
    description: str = ""
    onset: Optional[str] = None
    expires: Optional[str] = None


class WeatherResult(BaseModel):
    """Complete weather result with validation metadata."""
    location: LocationInfo
    current: CurrentConditions
    forecast: Optional[DailyForecast] = None
    alerts: List[WeatherAlert] = Field(default_factory=list)
    retrieved_at: datetime
    source: str = "open-meteo"
    data_timestamp: Optional[datetime] = None
    freshness_seconds: float = 0.0


class StockPriceResult(BaseModel):
    """Stock price result with validation metadata."""
    symbol: str
    name: str = ""
    price: float
    currency: str = "USD"
    change: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: datetime
    source: str = ""
    data_timestamp: Optional[datetime] = None
    freshness_seconds: float = 0.0


class LocalBusinessResult(BaseModel):
    """Local business search result."""
    name: str
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    open_now: Optional[bool] = None
    hours: str = ""
    categories: List[str] = Field(default_factory=list)
    location: Optional[LocationInfo] = None


class LocalSearchResult(BaseModel):
    """Complete local search result with validation metadata."""
    query: str
    businesses: List[LocalBusinessResult] = Field(default_factory=list)
    retrieved_at: datetime
    source: str = ""
    data_timestamp: Optional[datetime] = None
    freshness_seconds: float = 0.0


class RetrievalMetadata(BaseModel):
    """Common metadata for all retrieval results."""
    request_id: str
    original_query: str
    interpreted_query: str = ""
    provider_name: str = ""
    source_url: Optional[str] = None
    retrieved_at: datetime
    data_timestamp: Optional[datetime] = None
    freshness_seconds: float = 0.0
    confidence: float = 1.0
    warnings: List[str] = Field(default_factory=list)
