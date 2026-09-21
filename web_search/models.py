"""
Search request and result models for the web_search package.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SearchRequest:
    """Represents a user's search/information request."""
    
    request_id: str
    original_query: str
    interpreted_query: Optional[str] = None
    category: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    requires_web_search: bool = True
    location: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SearchResult:
    """Normalized search result with metadata."""
    
    request_id: str
    category: Optional[str] = None
    original_query: Optional[str] = None
    interpreted_query: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    data: Any = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_timestamps: List[Optional[datetime]] = field(default_factory=list)
    freshness: Optional[float] = None  # Age in seconds at retrieval time
    confidence: float = 1.0
    conflicts: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if result has valid data."""
        return self.data is not None and self.error is None
