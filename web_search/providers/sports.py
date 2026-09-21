"""Sports search provider for scores, schedules, standings."""

from ..providers.base import SearchProvider


class SportsProvider(SearchProvider):
    """Sports scores and information provider."""
    
    def supports(self, request) -> bool:
        query_lower = (request.original_query or "").lower()
        return any(word in query_lower for word in [
            "score", "scores", "game", "games", "match", "matches",
            "standings", "schedule", "who won", "final score"
        ])
    
    async def search(self, request):
        from ..models import SearchResult
        # TODO: Implement sports-specific search logic
        return SearchResult(
            request_id=request.request_id,
            category="sports",
            original_query=request.original_query,
            data=f"Sports search for: {request.original_query}"
        )
