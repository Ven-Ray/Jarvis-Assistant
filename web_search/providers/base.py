"""
Base search provider interface for the web_search package.
All providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SearchProvider(ABC):
    """Abstract base class for all search providers."""
    
    @abstractmethod
    def supports(self, request) -> bool:
        """Determine if this provider can handle the given request.
        
        Args:
            request: A SearchRequest object
            
        Returns:
            True if this provider should handle the request
        """
        pass
    
    @abstractmethod
    async def search(self, request):
        """Execute a search for the given request.
        
        Args:
            request: A SearchRequest object
            
        Returns:
            A SearchResult object with normalized data and metadata
        """
        pass
