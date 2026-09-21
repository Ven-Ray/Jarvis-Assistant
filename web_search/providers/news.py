"""News search provider for latest headlines."""

from ..providers.base import SearchProvider


class NewsProvider(SearchProvider):
    """Latest news and headlines provider."""
    
    def supports(self, request) -> bool:
        query_lower = (request.original_query or "").lower()
        return any(word in query_lower for word in [
            "news", "headlines", "breaking", "latest news", "what's happening"
        ])
    
    async def search(self, request):
        from ..models import SearchResult
        # TODO: Implement news-specific search logic
        return SearchResult(
            request_id=request.request_id,
            category="news",
            original_query=request.original_query,
            data=f"News search for: {request.original_query}"
        )
