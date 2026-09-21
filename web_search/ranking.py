"""
Result ranking for scoring and ordering search results.
Uses relevance, freshness, source authority, and confidence signals.
"""


class ResultRanker:
    """Ranks multiple search results by quality and relevance."""
    
    def rank(self, results):
        """
        Rank a list of SearchResult objects.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            Results sorted by score (highest first)
        """
        scored = []
        for result in results:
            score = self._score(result)
            scored.append((score, result))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [r for _, r in scored]
    
    def _score(self, result):
        """Calculate quality score for a single result (0.0 to 1.0)."""
        if not result.is_valid():
            return 0.0
        
        # Base score from confidence
        score = result.confidence * 0.5
        
        # Freshness bonus (up to 0.3)
        freshness_score = self._freshness_score(result)
        score += freshness_score
        
        # Source authority bonus (up to 0.2)
        source_score = self._source_authority_score(result)
        score += source_score
        
        return min(score, 1.0)
    
    def _freshness_score(self, result):
        """Score based on data freshness."""
        if not result.freshness is None:
            # Freshness in seconds - lower is better
            if result.freshness < 60:
                return 0.3
            elif result.freshness < 300:
                return 0.25
            elif result.freshness < 3600:
                return 0.15
            else:
                return 0.05
        
        # No freshness info - neutral score
        return 0.1
    
    def _source_authority_score(self, result):
        """Score based on source authority."""
        if not result.sources:
            return 0.05
        
        # More sources = higher confidence in accuracy
        num_sources = len(result.sources)
        if num_sources >= 3:
            return 0.2
        elif num_sources == 2:
            return 0.15
        else:
            return 0.1
