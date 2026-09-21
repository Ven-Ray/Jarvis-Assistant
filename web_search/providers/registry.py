"""
Provider Registry - Priority-based provider selection.
Manages provider registration, priority ordering, and fallback chains.
"""

import logging
from typing import Dict, List, Optional, Type

from .base import SearchProvider


logger = logging.getLogger("jarvis.web_search.registry")


class ProviderRegistry:
    """
    Registry that manages search providers with priority-based selection.
    
    Providers are registered by data type (category) and assigned a priority level.
    Lower priority numbers have higher precedence. When selecting a provider,
    the registry returns the highest-priority provider that supports the request.
    """
    
    # Default provider priorities by category
    DEFAULT_PRIORITIES = {
        "weather": [
            ("open_meteo_api", 1),
            ("scrapy_weather_com", 2),
            ("ddgs_search", 3)
        ],
        "stocks": [
            ("alpha_vantage_api", 1),
            ("yahoo_finance_api", 2),
            ("scrapy_yahoo", 3)
        ],
        "local_businesses": [
            ("google_places_api", 1),
            ("scrapy_yelp", 2),
            ("ddgs_search", 3)
        ],
        "traffic": [
            ("google_maps_api", 1),
            ("scrapy_waze", 2),
            ("ddgs_search", 3)
        ],
        "news": [
            ("rss_feeds", 1),
            ("scrapy_news_sites", 2),
            ("ddgs_search", 3)
        ]
    }
    
    def __init__(self):
        # Map: category -> list of (provider_name, priority, provider_instance)
        self._providers = {}
        for category in self.DEFAULT_PRIORITIES:
            self._providers[category] = []
    
    def register(self, category: str, provider: SearchProvider, 
                 name: Optional[str] = None, priority: int = 10):
        """Register a provider for a specific category.
        
        Args:
            category: Data type category (e.g., "weather", "stocks")
            provider: Provider instance implementing SearchProvider interface
            name: Optional display name; defaults to class name
            priority: Priority level (lower = higher precedence)
        """
        if name is None:
            name = type(provider).__name__.lower()
        
        if category not in self._providers:
            self._providers[category] = []
        
        # Remove existing provider with same name to avoid duplicates
        self._providers[category] = [
            (n, p, inst) for n, p, inst in self._providers[category] 
            if n != name
        ]
        
        self._providers[category].append((name, priority, provider))
        # Sort by priority (lower first)
        self._providers[category].sort(key=lambda x: x[1])
        
        logger.info(f"Registered provider '{name}' for category '{category}' "
                    f"with priority {priority}")
    
    def get_providers(self, category: str) -> List[tuple]:
        """Get all providers registered for a category, sorted by priority.
        
        Returns:
            List of (name, priority, provider_instance) tuples
        """
        return self._providers.get(category, [])
    
    def select_provider(self, category: str, request=None):
        """Select the highest-priority provider that supports the request.
        
        Args:
            category: Data type category
            request: Optional SearchRequest to test provider support
            
        Returns:
            Tuple of (provider_name, provider_instance) or None if no suitable provider
        """
        providers = self.get_providers(category)
        
        for name, priority, provider in providers:
            try:
                if request is not None and not provider.supports(request):
                    logger.debug(f"Provider '{name}' does not support request")
                    continue
                
                logger.info(f"Selected provider '{name}' (priority {priority}) "
                           f"for category '{category}'")
                return name, provider
            except Exception as e:
                logger.warning(f"Error checking provider '{name}': {e}")
        
        logger.warning(f"No suitable provider found for category '{category}'")
        return None
    
    def get_fallback_chain(self, category: str) -> List[tuple]:
        """Get the complete fallback chain for a category.
        
        Returns:
            List of (name, priority, provider_instance) tuples in priority order
        """
        return self.get_providers(category)
