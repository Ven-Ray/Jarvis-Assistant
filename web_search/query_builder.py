"""
Query builder for constructing optimized search queries.
Adds freshness terms, location context, and category-specific modifiers.
"""

import datetime


class QueryBuilder:
    """Builds optimized search queries with context."""
    
    def build(self, original_query, category=None, location=None):
        """
        Build an optimized search query from user input.
        
        Args:
            original_query: User's raw query text
            category: Request category (weather, news, finance, etc.)
            location: Optional location dict with city/region/country
            
        Returns:
            Optimized search query string
        """
        now = datetime.datetime.now()
        today_str = now.strftime("%B %d, %Y")
        
        # Build base query
        query = original_query
        
        # Add freshness terms based on category
        if category in ["news", "weather", "sports"]:
            query = f"{query} today {today_str}"
        elif category == "finance":
            query = f"current price {query}"
        
        # Add location context when needed
        needs_location = category in ["weather", "local", "traffic"]
        if needs_location and location:
            loc_str = self._format_location(location)
            if loc_str:
                query = f"{query} in {loc_str}"
        
        return query
    
    def _format_location(self, location):
        """Format location dict to string."""
        parts = []
        if location.get("city"):
            parts.append(location["city"])
        if location.get("region"):
            parts.append(location["region"])
        if location.get("country"):
            parts.append(location["country"])
        return ", ".join(parts)
