"""
Result validator for checking search result quality, freshness, and consistency.
"""

import re
from datetime import datetime, timezone


class ResultValidator:
    """Validates search results for relevance, freshness, and data integrity."""
    
    def validate(self, result):
        """
        Validate a search result.
        
        Args:
            result: SearchResult object to validate
            
        Returns:
            Tuple of (is_valid: bool, issues: list[str])
        """
        issues = []
        
        # Check for required fields
        if not result.request_id:
            issues.append("Missing request_id")
        
        if not result.original_query:
            issues.append("Missing original_query")
        
        # Validate data presence
        if result.data is None and not result.error:
            issues.append("No data or error provided")
        
        # Check freshness for time-sensitive categories
        if result.category in ["weather", "news", "sports"]:
            age_issues = self._check_freshness(result)
            issues.extend(age_issues)
        
        # Validate sources
        source_issues = self._validate_sources(result)
        issues.extend(source_issues)
        
        return len(issues) == 0, issues
    
    def _check_freshness(self, result):
        """Check if time-sensitive results are fresh."""
        issues = []
        
        if not result.retrieved_at:
            issues.append("Missing retrieval timestamp")
            return issues
        
        age_seconds = (datetime.now(timezone.utc) - result.retrieved_at).total_seconds()
        
        # Weather should be < 1 hour old
        if result.category == "weather" and age_seconds > 3600:
            issues.append(f"Weather data is {age_seconds/60:.0f} minutes old")
        
        # News should be < 24 hours old
        if result.category == "news" and age_seconds > 86400:
            issues.append("News data is more than 24 hours old")
        
        return issues
    
    def _validate_sources(self, result):
        """Validate source metadata."""
        issues = []
        
        for i, source in enumerate(result.sources):
            if not isinstance(source, dict):
                issues.append(f"Source {i} is not a dictionary")
                continue
            
            if "name" not in source and "url" not in source:
                issues.append(f"Source {i} missing name and url")
        
        return issues
