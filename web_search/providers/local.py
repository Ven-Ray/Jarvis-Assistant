"""Local search provider for businesses, places, directions."""

from ..providers.base import SearchProvider


class LocalSearchProvider(SearchProvider):
    """Nearby businesses and places provider."""
    
    def supports(self, request) -> bool:
        query_lower = (request.original_query or "").lower()
        return any(word in query_lower for word in [
            "near me", "nearby", "closest", "nearest", "directions",
            "open now", "business hours"
        ])
    
    async def search(self, request):
        from ..models import SearchResult
        # TODO: Implement local search logic
        return SearchResult(
            request_id=request.request_id,
            category="local",
            original_query=request.original_query,
            data=f"Local search for: {request.original_query}"
        )
