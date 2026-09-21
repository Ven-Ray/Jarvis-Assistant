"""Web search providers."""

from .base import SearchProvider
from .weather import WeatherProvider
from .finance import StockPriceProvider as FinanceProvider
from .sports import SportsProvider
from .news import NewsProvider
from .shopping import ShoppingProvider
from .local import LocalSearchProvider
from .general import GeneralSearchProvider

__all__ = [
    "SearchProvider",
    "WeatherProvider",
    "FinanceProvider",
    "SportsProvider",
    "NewsProvider",
    "ShoppingProvider",
    "LocalSearchProvider",
    "GeneralSearchProvider"
]
