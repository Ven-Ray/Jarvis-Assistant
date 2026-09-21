"""
Fallback response generator for when search or LLM generation fails.
Creates deterministic, user-friendly responses from normalized data.
"""


class FallbackGenerator:
    """Generates fallback responses when primary methods fail."""
    
    def generate(self, request):
        """
        Generate a fallback response based on the original request.
        
        Args:
            request: SearchRequest object
            
        Returns:
            User-friendly fallback response string
        """
        query = (request.interpreted_query or request.original_query).lower()
        
        # Category-specific fallbacks
        if "weather" in query:
            return self._weather_fallback(request)
        elif any(word in query for word in ["stock", "price", "market"]):
            return self._finance_fallback(request)
        elif any(word in query for word in ["news", "headlines"]):
            return self._news_fallback(request)
        elif any(word in query for word in ["score", "game", "match"]):
            return self._sports_fallback(request)
        
        # General fallback
        return (f"I'm sorry, Sir. I was unable to find reliable information about: "
                f"{request.original_query}")
    
    def _weather_fallback(self, request):
        """Fallback for weather queries."""
        location = self._extract_location(request)
        if location:
            return (f"I'm sorry, Sir. I was unable to retrieve current weather "
                    f"information for {location} at this time.")
        return ("I'm sorry, Sir. I was unable to retrieve current weather "
                "information at this time.")
    
    def _finance_fallback(self, request):
        """Fallback for finance queries."""
        return (f"I'm sorry, Sir. I was unable to retrieve current market data "
                f"for: {request.original_query}")
    
    def _news_fallback(self, request):
        """Fallback for news queries."""
        return ("I'm sorry, Sir. I was unable to retrieve the latest news at "
                "this time.")
    
    def _sports_fallback(self, request):
        """Fallback for sports queries."""
        return (f"I'm sorry, Sir. I was unable to retrieve current sports "
                f"information about: {request.original_query}")
    
    def _extract_location(self, request):
        """Try to extract location from request entities or query."""
        if request.entities and "location" in request.entities:
            return request.entities["location"]
        
        # Try to parse from query text (simplified)
        query = request.original_query.lower()
        for word in ["in", "for"]:
            parts = query.split(word)
            if len(parts) > 1:
                potential = parts[1].strip()
                if potential and not any(c.isdigit() for c in potential):
                    return potential
        
        return None
