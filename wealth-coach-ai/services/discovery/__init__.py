"""
Investment Discovery Engine

A modular system for collecting, cleaning, and analyzing investment-related content
from multiple trusted sources to provide AI-ready insights.

Modules:
    - config: Configuration and constants
    - models: Data models for articles and insights
    - collector: Base collector classes and registry
    - cleaner: Data cleaning and normalization
    - analyzer: Insight generation and analysis
    - rss_collector: RSS feed collectors for financial news sources
    - newsapi_collector: NewsAPI collector for investment topics
    - reddit_collector: Reddit collector for investment discussions
    - personalization: Personalization engine for user-specific recommendations
"""

from .config import DiscoveryConfig
from .models import InvestmentArticle, DiscoveryInsight, CollectorResult
from .collector import BaseCollector, CollectorRegistry
from .cleaner import ContentCleaner
from .analyzer import InsightAnalyzer
from .rss_collector import (
    RSSCollector,
    RBICollector,
    SEBICollector,
    EconomicTimesMarketsCollector,
    BusinessStandardMarketsCollector,
    MintMarketsCollector,
    create_rss_collector,
    collect_all_rss_feeds,
)
from .newsapi_collector import (
    NewsAPICollector,
    create_newsapi_collector,
    collect_all_newsapi_topics,
)
from .reddit_collector import (
    RedditCollector,
    create_reddit_collector,
    collect_all_reddit_subreddits,
)
from .personalization import PersonalizationEngine
from .collector import collect_all_articles, load_fallback_articles, get_collection_stats

__version__ = "1.0.0"

__all__ = [
    "DiscoveryConfig",
    "InvestmentArticle",
    "DiscoveryInsight",
    "CollectorResult",
    "BaseCollector",
    "CollectorRegistry",
    "ContentCleaner",
    "InsightAnalyzer",
    "RSSCollector",
    "RBICollector",
    "SEBICollector",
    "EconomicTimesMarketsCollector",
    "BusinessStandardMarketsCollector",
    "MintMarketsCollector",
    "create_rss_collector",
    "collect_all_rss_feeds",
    "NewsAPICollector",
    "create_newsapi_collector",
    "collect_all_newsapi_topics",
    "RedditCollector",
    "create_reddit_collector",
    "collect_all_reddit_subreddits",
    "PersonalizationEngine",
    "collect_all_articles",
    "load_fallback_articles",
    "get_collection_stats",
]
