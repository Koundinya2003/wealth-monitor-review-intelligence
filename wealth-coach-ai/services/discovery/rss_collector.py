"""
RSS feed collectors for financial news sources.

Provides collectors for:
- RBI (Reserve Bank of India)
- SEBI (Securities and Exchange Board of India)
- Economic Times Markets
- Business Standard Markets
- Mint Markets
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import feedparser

from .models import InvestmentArticle, CollectorResult
from .config import config

logger = logging.getLogger(__name__)


class RSSCollector:
    """
    Generic RSS feed collector for financial news sources.
    
    Handles feed parsing, duplicate detection, and error handling.
    """
    
    # RSS feed URLs for financial news sources
    FEED_URLS = {
        "rbi": "https://rbi.org.in/rssfeed.xml",
        "sebi": "https://www.sebi.gov.in/rss-feed.xml",
        "economic_times_markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "business_standard_markets": "https://www.business-standard.com/rss/markets-106.rss",
        "mint_markets": "https://www.livemint.com/rss/markets"
    }
    
    def __init__(self, source_name: str):
        """
        Initialize the RSS collector.
        
        Args:
            source_name: Name of the source (must be in FEED_URLS)
        """
        self.source_name = source_name
        self.feed_url = self.FEED_URLS.get(source_name)
        
        if not self.feed_url:
            raise ValueError(f"Unknown RSS source: {source_name}")
        
        self.config = config
        self.seen_urls = set()
        self.seen_titles = set()
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for duplicate detection.
        
        Args:
            url: URL to normalize
        
        Returns:
            Normalized URL string
        """
        if not url:
            return ""
        
        # Remove trailing slashes and convert to lowercase
        normalized = url.lower().strip().rstrip('/')
        return normalized
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for duplicate detection.
        
        Args:
            title: Title to normalize
        
        Returns:
            Normalized title string
        """
        if not title:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = ' '.join(title.lower().split())
        return normalized
    
    def _is_duplicate(self, url: str, title: str) -> bool:
        """
        Check if article is a duplicate.
        
        Args:
            url: Article URL
            title: Article title
        
        Returns:
            True if duplicate, False otherwise
        """
        normalized_url = self._normalize_url(url)
        normalized_title = self._normalize_title(title)
        
        if normalized_url in self.seen_urls:
            logger.debug(f"Duplicate URL detected: {normalized_url}")
            return True
        
        if normalized_title in self.seen_titles:
            logger.debug(f"Duplicate title detected: {normalized_title}")
            return True
        
        return False
    
    def _mark_as_seen(self, url: str, title: str) -> None:
        """
        Mark article as seen to prevent duplicates.
        
        Args:
            url: Article URL
            title: Article title
        """
        self.seen_urls.add(self._normalize_url(url))
        self.seen_titles.add(self._normalize_title(title))
    
    def _parse_entry(self, entry, category: str = "general") -> Optional[InvestmentArticle]:
        """
        Parse a feed entry into an InvestmentArticle.
        
        Args:
            entry: feedparser entry object
            category: Article category
        
        Returns:
            InvestmentArticle or None if parsing fails
        """
        try:
            # Extract basic fields
            title = entry.get('title', '').strip()
            url = entry.get('link', '').strip()
            content = entry.get('summary', entry.get('description', '')).strip()
            
            # Validate required fields
            if not title or not url:
                logger.warning(f"Missing required fields in entry: {title[:50]}")
                return None
            
            # Check for duplicates
            if self._is_duplicate(url, title):
                logger.debug(f"Skipping duplicate: {title[:50]}")
                return None
            
            # Parse published date
            published_at = datetime.utcnow()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    from time import mktime
                    published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
                except Exception as e:
                    logger.warning(f"Could not parse published date: {e}")
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            elif hasattr(entry, 'category'):
                tags = [entry.category]
            
            # Create metadata
            metadata = {
                "feed_title": entry.get('feed_title', ''),
                "author": entry.get('author', ''),
            }
            
            # Create article
            article = InvestmentArticle(
                title=title,
                source=self.source_name,
                url=url,
                published_at=published_at,
                content=content,
                category=category,
                tags=tags,
                metadata=metadata
            )
            
            # Mark as seen
            self._mark_as_seen(url, title)
            
            return article
            
        except Exception as e:
            logger.error(f"Error parsing entry '{entry.get('title', 'Unknown')}': {e}")
            return None
    
    def collect(self, max_articles: Optional[int] = None, 
                category: str = "general") -> CollectorResult:
        """
        Collect articles from RSS feed.
        
        Args:
            max_articles: Maximum number of articles to collect (uses config default if not provided)
            category: Category to assign to collected articles
        
        Returns:
            CollectorResult with collected articles and any errors
        """
        if max_articles is None:
            max_articles = self.config.max_articles_per_source
        
        logger.info(f"Starting RSS collection from {self.source_name}: {self.feed_url}")
        
        articles = []
        errors = []
        
        try:
            # Parse feed
            feed = feedparser.parse(self.feed_url)
            
            # Check for feed parsing errors
            if feed.bozo and not feed.entries:
                error_msg = f"Feed parsing error for {self.source_name}: {feed.bozo_exception}"
                logger.error(error_msg)
                errors.append(error_msg)
                return self._create_result(articles, errors)
            
            # Log feed info
            logger.info(
                f"Feed '{feed.feed.get('title', 'Unknown')}' has {len(feed.entries)} entries"
            )
            
            # Process entries
            for entry in feed.entries[:max_articles]:
                try:
                    article = self._parse_entry(entry, category)
                    if article:
                        articles.append(article)
                except Exception as e:
                    error_msg = f"Error processing entry: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            logger.info(
                f"Successfully collected {len(articles)} articles from {self.source_name}"
            )
            
        except Exception as e:
            error_msg = f"Failed to fetch RSS feed from {self.source_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return self._create_result(articles, errors)
    
    def _create_result(self, articles: List[InvestmentArticle], 
                      errors: List[str]) -> CollectorResult:
        """
        Create a CollectorResult with current timestamp.
        
        Args:
            articles: List of collected articles
            errors: List of errors encountered
        
        Returns:
            CollectorResult instance
        """
        return CollectorResult(
            articles=articles,
            errors=errors,
            collected_at=datetime.utcnow(),
            source=self.source_name
        )


class RBICollector(RSSCollector):
    """Collector for Reserve Bank of India RSS feed"""
    
    def __init__(self):
        """Initialize RBI collector"""
        super().__init__("rbi")
    
    def collect(self, max_articles: Optional[int] = None) -> CollectorResult:
        """Collect articles from RBI feed"""
        return super().collect(max_articles=max_articles, category="monetary_policy")


class SEBICollector(RSSCollector):
    """Collector for SEBI RSS feed"""
    
    def __init__(self):
        """Initialize SEBI collector"""
        super().__init__("sebi")
    
    def collect(self, max_articles: Optional[int] = None) -> CollectorResult:
        """Collect articles from SEBI feed"""
        return super().collect(max_articles=max_articles, category="regulatory")


class EconomicTimesMarketsCollector(RSSCollector):
    """Collector for Economic Times Markets RSS feed"""
    
    def __init__(self):
        """Initialize Economic Times Markets collector"""
        super().__init__("economic_times_markets")
    
    def collect(self, max_articles: Optional[int] = None) -> CollectorResult:
        """Collect articles from Economic Times Markets feed"""
        return super().collect(max_articles=max_articles, category="market_news")


class BusinessStandardMarketsCollector(RSSCollector):
    """Collector for Business Standard Markets RSS feed"""
    
    def __init__(self):
        """Initialize Business Standard Markets collector"""
        super().__init__("business_standard_markets")
    
    def collect(self, max_articles: Optional[int] = None) -> CollectorResult:
        """Collect articles from Business Standard Markets feed"""
        return super().collect(max_articles=max_articles, category="market_news")


class MintMarketsCollector(RSSCollector):
    """Collector for Mint Markets RSS feed"""
    
    def __init__(self):
        """Initialize Mint Markets collector"""
        super().__init__("mint_markets")
    
    def collect(self, max_articles: Optional[int] = None) -> CollectorResult:
        """Collect articles from Mint Markets feed"""
        return super().collect(max_articles=max_articles, category="market_news")


# Convenience function to create collectors
def create_rss_collector(source_name: str) -> Optional[RSSCollector]:
    """
    Create an RSS collector for a specific source.
    
    Args:
        source_name: Name of the source (rbi, sebi, economic_times_markets, 
                     business_standard_markets, mint_markets)
    
    Returns:
        RSSCollector instance or None if source not found
    """
    collector_classes = {
        "rbi": RBICollector,
        "sebi": SEBICollector,
        "economic_times_markets": EconomicTimesMarketsCollector,
        "business_standard_markets": BusinessStandardMarketsCollector,
        "mint_markets": MintMarketsCollector,
    }
    
    collector_class = collector_classes.get(source_name.lower())
    
    if collector_class:
        return collector_class()
    
    logger.warning(f"No RSS collector found for source: {source_name}")
    return None


# Convenience function to collect from all RSS sources
def collect_all_rss_feeds(max_articles_per_source: Optional[int] = None) -> List[CollectorResult]:
    """
    Collect articles from all RSS feeds.
    
    Args:
        max_articles_per_source: Maximum articles per source (uses config default if not provided)
    
    Returns:
        List of CollectorResult instances
    """
    results = []
    
    sources = [
        "rbi",
        "sebi",
        "economic_times_markets",
        "business_standard_markets",
        "mint_markets"
    ]
    
    for source_name in sources:
        try:
            collector = create_rss_collector(source_name)
            if collector:
                logger.info(f"Collecting from {source_name}...")
                result = collector.collect(max_articles=max_articles_per_source)
                results.append(result)
            else:
                logger.warning(f"Skipping unknown source: {source_name}")
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")
            # Create error result
            error_result = CollectorResult(
                articles=[],
                errors=[f"Collection failed: {str(e)}"],
                collected_at=datetime.utcnow(),
                source=source_name
            )
            results.append(error_result)
    
    return results