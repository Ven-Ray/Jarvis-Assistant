"""Tests for ProviderRegistry."""

import pytest
from web_search.providers.registry import ProviderRegistry


class MockProvider:
    def __init__(self, name):
        self.name = name
    
    def supports(self, request):
        return True
    
    async def search(self, request):
        pass


class TestProviderRegistry:
    def test_register_and_select(self):
        registry = ProviderRegistry()
        
        provider1 = MockProvider("api")
        provider2 = MockProvider("scraper")
        
        registry.register("weather", provider1, name="open_meteo_api", priority=1)
        registry.register("weather", provider2, name="scrapy_weather_com", priority=2)
        
        selected_name, selected_provider = registry.select_provider("weather")
        assert selected_name == "open_meteo_api"
        assert selected_provider is provider1
    
    def test_fallback_chain_order(self):
        registry = ProviderRegistry()
        
        p1 = MockProvider("api")
        p2 = MockProvider("scraper")
        p3 = MockProvider("search")
        
        registry.register("stocks", p1, name="alpha_vantage_api", priority=1)
        registry.register("stocks", p2, name="scrapy_yahoo", priority=2)
        registry.register("stocks", p3, name="ddgs_search", priority=3)
        
        chain = registry.get_fallback_chain("stocks")
        assert len(chain) == 3
        assert chain[0][0] == "alpha_vantage_api"
        assert chain[1][0] == "scrapy_yahoo"
        assert chain[2][0] == "ddgs_search"
    
    def test_no_provider_for_category(self):
        registry = ProviderRegistry()
        
        result = registry.select_provider("unknown_category")
        assert result is None
