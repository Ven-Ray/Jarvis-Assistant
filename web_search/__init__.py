"""
Web search package for Jarvis.
Provides general-purpose web search capabilities with specialized providers.
"""

from .manager import SearchManager
from .classifier import SearchClassifier
from .models import SearchRequest, SearchResult
from .query_builder import QueryBuilder
from .normalizer import ResultNormalizer
from .validator import ResultValidator
from .ranking import ResultRanker
from .fallback import FallbackGenerator

__all__ = [
    "SearchManager",
    "SearchClassifier",
    "SearchRequest",
    "SearchResult",
    "QueryBuilder",
    "ResultNormalizer",
    "ResultValidator",
    "ResultRanker",
    "FallbackGenerator"
]
