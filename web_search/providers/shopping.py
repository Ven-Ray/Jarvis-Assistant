"""Shopping search provider for products, prices, reviews."""

from ..providers.base import SearchProvider


class ShoppingProvider(SearchProvider):
    """Product prices, availability, and reviews provider."""
    
    def supports(self, request) -> bool:
        query_lower = (request.original_query or "").lower()
        return any(word in query_lower for word in [
            "buy", "price of", "cost of", "shop", "shopping", "product",
            "review", "reviews", "in stock", "available"
        ])
    
    async def search(self, request):
        from ..models import SearchResult
        # TODO: Implement shopping-specific search logic
        return SearchResult(
            request_id=request.request_id,
            category="shopping",
            original_query=request.original_query,
            data=f"Shopping search for: {request.original_query}"
        )
