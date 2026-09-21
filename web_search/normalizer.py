"""
Result normalizer for standardizing search results across providers.
Ensures consistent data structure and metadata.
"""

from datetime import datetime, timezone


class ResultNormalizer:
    """Normalizes raw provider results into standardized SearchResult objects."""
    
    def normalize(self, request_id, category, original_query, interpreted_query, 
                  raw_data, sources=None):
        """
        Normalize raw search data into a standard result object.
        
        Args:
            request_id: Unique request identifier
            category: Search category
            original_query: User's original query
            interpreted_query: Processed/optimized query used
            raw_data: Raw data from provider
            sources: List of source metadata dicts
            
        Returns:
            Normalized SearchResult object
        """
        from .models import SearchResult
        
        return SearchResult(
            request_id=request_id,
            category=category,
            original_query=original_query,
            interpreted_query=interpreted_query,
            data=raw_data,
            sources=sources or [],
            retrieved_at=datetime.now(timezone.utc),
            confidence=self._estimate_confidence(raw_data)
        )
    
    def _estimate_confidence(self, raw_data):
        """Estimate result confidence based on data quality."""
        if not raw_data:
            return 0.0
        
        if isinstance(raw_data, str):
            # Longer, more detailed responses are typically more confident
            length = len(raw_data)
            if length > 200:
                return 0.95
            elif length > 100:
                return 0.85
            else:
                return 0.7
        
        # Structured data is typically high confidence
        return 0.9
