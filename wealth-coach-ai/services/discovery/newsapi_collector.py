"""
NewsAPI collector for investment-related news.

Provides collection from NewsAPI for investment topics including:
- Mutual Funds
- SIP
- Index Funds
- Gold ETF
- PPF
- NPS
- SEBI
- RBI
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import os
import time

import requests

from .models import InvestmentArticle, CollectorResult
from .config import config

logger = logging.getLogger(__name__)


class NewsAPICollector:
    """
    Collector for NewsAPI financial news.
    
    Searches for investment-related articles from NewsAPI with
    retry logic and timeout handling.
    """
    
    # Search topics for investment-related news
    SEARCH_TOPICS = [
        "Mutual Funds",
        "SIP",
        "Index Funds",
        "Gold ETF",
        "PPF",
        "NPS",
        "SEBI",
        "RBI"
    ]
    
    # NewsAPI endpoint
    BASE_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self):
        """Initialize the NewsAPI collector."""
        self.api_key = os.environ.get('NEWSAPI_API_KEY')
        
        if not self.api_key:
            logger.warning("NEWSAPI_API_KEY not found in environment variables")
        
        self.config = config
        self.session = requests.Session()
        
        # Retry configuration
        self.max_retries = self.config.retry_attempts
        self.retry_delay = 1  # seconds
        self.timeout = self.config.request_timeout
        
        # Duplicate tracking
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
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic and timeout handling.
        
        Args:
            params: Request parameters
        
        Returns:
            Response JSON or None if request failed
        """
        if not self.api_key:
            logger.error("Cannot make request: NEWSAPI_API_KEY not configured")
            return None
        
        headers = {
            "X-Api-Key": self.api_key
        }
        
        # Add API key to params
        params['apiKey'] = self.api_key
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making NewsAPI request (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limited by NewsAPI (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        sleep_time = self.retry_delay * (attempt + 1)
                        logger.info(f"Waiting {sleep_time}s before retry...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        logger.error("Max retries reached for rate limiting")
                        return None
                
                # Check for other errors
                if response.status_code != 200:
                    logger.error(
                        f"NewsAPI request failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    return None
                
                # Parse response
                data = response.json()
                
                if data.get('status') == 'ok':
                    return data
                else:
                    logger.error(f"NewsAPI returned error: {data.get('message', 'Unknown error')}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
        
        return None
    
    def _parse_article(self, article_data: Dict[str, Any], category: str = "general") -> Optional[InvestmentArticle]:
        """
        Parse NewsAPI article data into InvestmentArticle.
        
        Args:
            article_data: Article data from NewsAPI
            category: Article category
        
        Returns:
            InvestmentArticle or None if parsing fails
        """
        try:
            # Extract fields
            title = article_data.get('title', '').strip()
            url = article_data.get('url', '').strip()
            content = article_data.get('content', article_data.get('description', '')).strip()
            
            # Validate required fields
            if not title or not url:
                logger.warning(f"Missing required fields: title={bool(title)}, url={bool(url)}")
                return None
            
            # Check for duplicates
            if self._is_duplicate(url, title):
                logger.debug(f"Skipping duplicate: {title[:50]}")
                return None
            
            # Parse published date
            published_at = datetime.utcnow()
            published_at_str = article_data.get('publishedAt')
            
            if published_at_str:
                try:
                    # NewsAPI uses ISO format
                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Could not parse published date '{published_at_str}': {e}")
            
            # Extract source information
            source_data = article_data.get('source', {})
            source_name = source_data.get('name', 'NewsAPI')
            
            # Extract tags
            tags = []
            if article_data.get('author'):
                tags.append('author:' + article_data['author'].lower())
            
            # Create metadata
            metadata = {
                "source_name": source_name,
                "author": article_data.get('author', ''),
                "url_to_image": article_data.get('urlToImage', ''),
            }
            
            # Create article
            article = InvestmentArticle(
                title=title,
                source="newsapi",
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
            logger.error(f"Error parsing article '{article_data.get('title', 'Unknown')}': {e}")
            return None
    
    def collect(self, topic: str, max_articles: Optional[int] = None,
                days_back: int = 7) -> CollectorResult:
        """
        Collect articles for a specific topic from NewsAPI.
        
        Args:
            topic: Search topic (e.g., "Mutual Funds", "SIP")
            max_articles: Maximum number of articles to collect (uses config default if not provided)
            days_back: Number of days to look back for articles
        
        Returns:
            CollectorResult with collected articles and any errors
        """
        if max_articles is None:
            max_articles = self.config.max_articles_per_source
        
        logger.info(f"Starting NewsAPI collection for topic: {topic}")
        
        articles = []
        errors = []
        
        if not self.api_key:
            error_msg = "NEWSAPI_API_KEY not configured in environment variables"
            logger.error(error_msg)
            errors.append(error_msg)
            return self._create_result(articles, errors)
        
        # Calculate date range
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Prepare request parameters
        params = {
            'q': topic,
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': max_articles
        }
        
        # Make request with retry logic
        data = self._make_request(params)
        
        if not data:
            error_msg = f"Failed to fetch articles for topic: {topic}"
            logger.error(error_msg)
            errors.append(error_msg)
            return self._create_result(articles, errors)
        
        # Parse articles
        raw_articles = data.get('articles', [])
        logger.info(f"Received {len(raw_articles)} articles from NewsAPI for topic: {topic}")
        
        for article_data in raw_articles[:max_articles]:
            try:
                article = self._parse_article(article_data, category="market_news")
                if article:
                    articles.append(article)
            except Exception as e:
                error_msg = f"Error processing article: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        logger.info(
            f"Successfully collected {len(articles)} articles for topic: {topic}"
        )
        
        return self._create_result(articles, errors)
    
    def collect_multiple_topics(self, topics: Optional[List[str]] = None,
                               max_articles_per_topic: Optional[int] = None) -> List[CollectorResult]:
        """
        Collect articles for multiple topics.
        
        Args:
            topics: List of topics to search (uses default topics if not provided)
            max_articles_per_topic: Maximum articles per topic (uses config default if not provided)
        
        Returns:
            List of CollectorResult instances
        """
        if topics is None:
            topics = self.SEARCH_TOPICS
        
        if max_articles_per_topic is None:
            max_articles_per_topic = self.config.max_articles_per_source
        
        logger.info(f"Collecting articles for {len(topics)} topics")
        
        results = []
        
        for topic in topics:
            try:
                logger.info(f"Collecting for topic: {topic}")
                result = self.collect(topic, max_articles_per_topic)
                results.append(result)
            except Exception as e:
                logger.error(f"Error collecting for topic {topic}: {e}")
                error_result = self._create_result(
                    articles=[],
                    errors=[f"Collection failed: {str(e)}"]
                )
                results.append(error_result)
        
        return results
    
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
            source="newsapi"
        )
    
    def close(self):
        """Close the requests session."""
        if self.session:
            self.session.close()


# Convenience function to create NewsAPI collector
def create_newsapi_collector() -> NewsAPICollector:
    """
    Create a NewsAPI collector instance.
    
    Returns:
        NewsAPICollector instance
    """
    return NewsAPICollector()


# Convenience function to collect from all topics
def collect_all_newsapi_topics(max_articles_per_topic: Optional[int] = None) -> List[CollectorResult]:
    """
    Collect articles for all predefined topics from NewsAPI.
    
    Args:
        max_articles_per_topic: Maximum articles per topic (uses config default if not provided)
    
    Returns:
        List of CollectorResult instances
    """
    collector = create_newsapi_collector()
    results = collector.collect_multiple_topics(max_articles_per_topic=max_articles_per_topic)
    collector.close()
    return results