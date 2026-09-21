"""
General web search provider using DuckDuckGo as fallback for any category.
"""

from typing import Any, Dict, Optional

from ..providers.base import SearchProvider


class GeneralSearchProvider(SearchProvider):
    """Fallback general web search provider."""
    
    def __init__(self, ddgs_client=None):
        self.ddgs = ddgs_client
    
    def supports(self, request) -> bool:
        """Always supports any request (fallback)."""
        return True
    
    async def search(self, request):
        """Execute general web search and return normalized result."""
        from ..models import SearchResult
        
        try:
            if not self.ddgs:
                raise RuntimeError("DuckDuckGo client not configured")
            
            query = request.interpreted_query or request.original_query
            
            results = self.ddgs.text(query, max_results=5)
            
            if not results or len(results) == 0:
                return SearchResult(
                    request_id=request.request_id,
                    category="general",
                    original_query=request.original_query,
                    interpreted_query=query,
                    error="No search results found"
                )
            
            # Collect snippets from top results
            context_parts = []
            sources = []
            for i, result in enumerate(results[:3]):
                title = result.get('title', '')
                body = result.get('body', '')
                url = result.get('href', '')
                if body:
                    context_parts.append(f"[{i+1}] {title}: {body}")
                sources.append({"name": title, "url": url})
            
            return SearchResult(
                request_id=request.request_id,
                category="general",
                original_query=request.original_query,
                interpreted_query=query,
                data="\n\n".join(context_parts),
                sources=sources,
                confidence=0.8
            )
            
        except Exception as e:
            return SearchResult(
                request_id=request.request_id,
                category="general",
                original_query=request.original_query,
                interpreted_query=request.interpreted_query or request.original_query,
                error=str(e)
            )
