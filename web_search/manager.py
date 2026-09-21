"""
Search Manager - Central orchestration for all web searches.
Coordinates classification, provider selection via registry, execution, and result normalization.
Uses priority-based provider fallback chains with proper timeout handling.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import SearchRequest, SearchResult
from .classifier import SearchClassifier
from .providers.base import SearchProvider
from .providers.registry import ProviderRegistry


logger = logging.getLogger("jarvis.web_search")


class SearchManager:
    """Central manager for all web search operations with provider registry."""
    
    def __init__(self, providers: List[SearchProvider], classifier=None):
        self.classifier = classifier or SearchClassifier()
        
        # Initialize provider registry and register all providers
        self.registry = ProviderRegistry()
        self._register_providers(providers)
    
    def _register_providers(self, providers: List[SearchProvider]):
        """Register providers with the registry based on their capabilities."""
        for provider in providers:
            # Determine category from provider type/name
            provider_name = type(provider).__name__.lower()
            
            if "weather" in provider_name:
                self.registry.register("weather", provider, name="open_meteo_api", priority=1)
            elif "stock" in provider_name or "finance" in provider_name:
                self.registry.register("stocks", provider, name="alpha_vantage_api", priority=1)
            elif "general" in provider_name or "ddgs" in provider_name:
                # Register as fallback for all categories with lower priority
                for category in ["weather", "stocks", "local_businesses", "traffic", "news"]:
                    self.registry.register(category, provider, name="ddgs_search", priority=3)
            else:
                logger.warning(f"Unknown provider type: {provider_name}")
    
    async def execute(self, request_id: str, original_query: str, 
                      location: Optional[Dict] = None) -> SearchResult:
        """Execute a complete search workflow with provider fallback chain.
        
        Args:
            request_id: Unique identifier for this request
            original_query: User's original query text
            location: Optional location data dict
            
        Returns:
            Normalized SearchResult object
        """
        logger.info(f"[{request_id}] REQUEST_STARTED - {original_query}")
        
        # Step 1: Classify intent
        classification = self.classifier.classify(original_query)
        logger.info(f"[{request_id}] REQUEST_CLASSIFIED - requires_web_search={classification['requires_web_search']}")
        
        if not classification["requires_web_search"]:
            return SearchResult(
                request_id=request_id,
                original_query=original_query,
                data=None,
                error="No web search required"
            )
        
        # Step 2: Create search request object
        search_request = SearchRequest(
            request_id=request_id,
            original_query=original_query,
            interpreted_query=classification["search_query"],
            location=location
        )
        logger.info(f"[{request_id}] ENTITIES_EXTRACTED - query={search_request.interpreted_query}")
        
        # Step 3: Determine category and get fallback chain
        category = self._determine_category(search_request)
        fallback_chain = self.registry.get_fallback_chain(category)
        
        if not fallback_chain:
            logger.warning(f"[{request_id}] No providers registered for category '{category}'")
            return SearchResult(
                request_id=request_id,
                original_query=original_query,
                error=f"No providers available for category '{category}'"
            )
        
        # Step 4: Execute provider fallback chain with timeout handling
        result = None
        last_error = None
        
        for name, priority, provider in fallback_chain:
            try:
                logger.info(f"[{request_id}] PROVIDER_SELECTED - {name} (priority {priority})")
                
                # Check if provider supports this request
                if not provider.supports(search_request):
                    logger.debug(f"[{request_id}] Provider '{name}' does not support request")
                    continue
                
                # Execute with timeout
                logger.info(f"[{request_id}] SEARCH_STARTED - provider={name}")
                
                result = await asyncio.wait_for(
                    provider.search(search_request),
                    timeout=30.0
                )
                
                logger.info(f"[{request_id}] SEARCH_COMPLETED - success={result.is_valid()}")
                
                # If successful, break out of fallback chain
                if result.is_valid():
                    break
                    
            except asyncio.TimeoutError:
                last_error = f"Provider '{name}' timed out after 30 seconds"
                logger.warning(f"[{request_id}] SEARCH_TIMEOUT - provider={name}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{request_id}] PROVIDER_ERROR - provider={name} error={e}")
            
            # Continue to next provider in fallback chain
        
        # Step 5: Handle final result or generate fallback response
        if not result or not result.is_valid():
            logger.info(f"[{request_id}] FALLBACK_RESPONSE_USED")
            result = self._generate_fallback_result(search_request, last_error)
        
        # Step 6: Validate and log metadata
        if result.is_valid():
            logger.info(f"[{request_id}] RESULTS_NORMALIZED")
            logger.info(f"[{request_id}] FRESHNESS_VALIDATED - age={result.freshness}s")
            
            if result.conflicts:
                logger.warning(f"[{request_id}] CONFLICTS_DETECTED - {len(result.conflicts)} conflicts")
        
        logger.info(f"[{request_id}] REQUEST_COMPLETED")
        return result
    
    def _determine_category(self, request) -> str:
        """Determine the data category for a search request."""
        query_lower = (request.original_query or "").lower()
        
        if any(word in query_lower for word in ["weather", "temperature", "forecast"]):
            return "weather"
        elif any(word in query_lower for word in ["stock", "price of", "market"]):
            return "stocks"
        elif any(word in query_lower for word in ["near me", "nearby", "restaurant"]):
            return "local_businesses"
        elif any(word in query_lower for word in ["traffic", "route"]):
            return "traffic"
        elif any(word in query_lower for word in ["news", "headlines"]):
            return "news"
        
        # Default to general search
        return "general"
    
    def _generate_fallback_result(self, request: SearchRequest, error=None) -> SearchResult:
        """Generate a deterministic fallback response from normalized data."""
        query = request.interpreted_query or request.original_query
        
        if error:
            return SearchResult(
                request_id=request.request_id,
                original_query=request.original_query,
                interpreted_query=query,
                data=f"I'm sorry, Sir. I encountered an issue retrieving information about {query}: {error}"
            )
        
        # Try to provide useful information even without successful search
        if "weather" in query.lower():
            return SearchResult(
                request_id=request.request_id,
                category="weather",
                original_query=request.original_query,
                data=f"I'm sorry, Sir. I was unable to retrieve current weather information at this time."
            )
        
        return SearchResult(
            request_id=request.request_id,
            original_query=request.original_query,
            interpreted_query=query,
            data=f"I'm sorry, Sir. I was unable to find reliable information about: {query}"
        )
