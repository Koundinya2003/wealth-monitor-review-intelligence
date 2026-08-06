"""
Reddit collector for investment-related discussions.

Provides collection from Reddit subreddits including:
- r/IndiaInvestments
- r/personalfinanceindia
- r/IndianStreetBets

Collects posts with title, body, top comments, score, and created time.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
import time

import requests

from .models import InvestmentArticle, CollectorResult
from .config import config

logger = logging.getLogger(__name__)


class RedditCollector:
    """
    Collector for Reddit investment discussions.
    
    Collects posts and comments from specified subreddits with
    retry logic and duplicate removal.
    """
    
    # Target subreddits for investment discussions
    SUBREDDITS = [
        "IndiaInvestments",
        "personalfinanceindia",
        "IndianStreetBets"
    ]
    
    # Reddit API endpoints
    BASE_URL = "https://www.reddit.com/r/{subreddit}/hot.json"
    SEARCH_URL = "https://www.reddit.com/r/{subreddit}/search.json"
    
    def __init__(self):
        """Initialize the Reddit collector."""
        self.api_key = os.environ.get('REDDIT_API_KEY')
        self.api_secret = os.environ.get('REDDIT_API_SECRET')
        self.user_agent = os.environ.get('REDDIT_USER_AGENT', 'WealthCoachAI/1.0')
        
        self.config = config
        self.session = requests.Session()
        
        # Set user agent
        self.session.headers.update({'User-Agent': self.user_agent})
        
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
        Check if post is a duplicate.
        
        Args:
            url: Post URL
            title: Post title
        
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
        Mark post as seen to prevent duplicates.
        
        Args:
            url: Post URL
            title: Post title
        """
        self.seen_urls.add(self._normalize_url(url))
        self.seen_titles.add(self._normalize_title(title))
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic and timeout handling.
        
        Args:
            url: Request URL
            params: Query parameters
        
        Returns:
            Response JSON or None if request failed
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making Reddit API request (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limited by Reddit (attempt {attempt + 1})")
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
                        f"Reddit API request failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    return None
                
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1} {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
        
        return None
    
    def _extract_comments(self, post_data: Dict[str, Any], max_comments: int = 5) -> List[Dict[str, Any]]:
        """
        Extract top comments from post data.
        
        Args:
            post_data: Post data from Reddit API
            max_comments: Maximum number of comments to extract
        
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        try:
            # Navigate to comments
            comment_data = post_data.get('data', {}).get('children', [])
            
            for comment_item in comment_data[:max_comments]:
                try:
                    comment = comment_item.get('data', {})
                    
                    # Skip if comment was deleted or removed
                    if comment.get('body') in ['[deleted]', '[removed]']:
                        continue
                    
                    comments.append({
                        'author': comment.get('author', 'Unknown'),
                        'body': comment.get('body', ''),
                        'score': comment.get('score', 0),
                        'created_utc': comment.get('created_utc', 0)
                    })
                except Exception as e:
                    logger.debug(f"Error extracting comment: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error extracting comments: {e}")
        
        return comments
    
    def _parse_post(self, post_data: Dict[str, Any], category: str = "general") -> Optional[InvestmentArticle]:
        """
        Parse Reddit post into InvestmentArticle.
        
        Args:
            post_data: Post data from Reddit API
            category: Article category
        
        Returns:
            InvestmentArticle or None if parsing fails
        """
        try:
            # Extract post data
            data = post_data.get('data', {})
            
            title = data.get('title', '').strip()
            selftext = data.get('selftext', '').strip()
            url = f"https://reddit.com{data.get('permalink', '')}"
            score = data.get('score', 0)
            created_utc = data.get('created_utc', 0)
            num_comments = data.get('num_comments', 0)
            author = data.get('author', 'Unknown')
            
            # Validate required fields
            if not title or not url:
                logger.warning(f"Missing required fields: title={bool(title)}, url={bool(url)}")
                return None
            
            # Check for duplicates
            if self._is_duplicate(url, title):
                logger.debug(f"Skipping duplicate: {title[:50]}")
                return None
            
            # Parse created time
            published_at = datetime.utcnow()
            if created_utc:
                try:
                    published_at = datetime.fromtimestamp(created_utc)
                except Exception as e:
                    logger.warning(f"Could not parse created_utc {created_utc}: {e}")
            
            # Combine title and body for content
            content_parts = [title]
            if selftext and selftext != '[deleted]':
                content_parts.append(selftext)
            
            content = '\n\n'.join(content_parts)
            
            # Extract comments if available
            comments = []
            if 'replies' in data and data['replies']:
                comments = self._extract_comments(data['replies'])
            
            # Create tags
            tags = [
                f"score:{score}",
                f"comments:{num_comments}",
                f"author:{author.lower()}"
            ]
            
            # Create metadata
            metadata = {
                "score": score,
                "num_comments": num_comments,
                "author": author,
                "subreddit": data.get('subreddit', ''),
                "upvote_ratio": data.get('upvote_ratio', 0),
                "comments": comments,
                "post_type": "self" if selftext else "link"
            }
            
            # Create article
            article = InvestmentArticle(
                title=title,
                source="reddit",
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
            logger.error(f"Error parsing post '{post_data.get('data', {}).get('title', 'Unknown')}': {e}")
            return None
    
    def collect(self, subreddit: str, max_posts: Optional[int] = None,
                category: str = "general") -> CollectorResult:
        """
        Collect posts from a specific subreddit.
        
        Args:
            subreddit: Subreddit name (e.g., 'IndiaInvestments')
            max_posts: Maximum number of posts to collect (uses config default if not provided)
            category: Category to assign to collected posts
        
        Returns:
            CollectorResult with collected articles and any errors
        """
        if max_posts is None:
            max_posts = self.config.max_articles_per_source
        
        logger.info(f"Starting Reddit collection from r/{subreddit}")
        
        articles = []
        errors = []
        
        # Prepare URL
        url = self.BASE_URL.format(subreddit=subreddit)
        params = {
            'limit': max_posts
        }
        
        # Make request with retry logic
        data = self._make_request(url, params)
        
        if not data:
            error_msg = f"Failed to fetch posts from r/{subreddit}"
            logger.error(error_msg)
            errors.append(error_msg)
            return self._create_result(articles, errors, subreddit)
        
        # Parse posts
        try:
            posts = data.get('data', {}).get('children', [])
            logger.info(f"Received {len(posts)} posts from r/{subreddit}")
            
            for post_item in posts[:max_posts]:
                try:
                    article = self._parse_post(post_item, category)
                    if article:
                        articles.append(article)
                except Exception as e:
                    error_msg = f"Error processing post: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            logger.info(
                f"Successfully collected {len(articles)} posts from r/{subreddit}"
            )
            
        except Exception as e:
            error_msg = f"Error parsing posts from r/{subreddit}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return self._create_result(articles, errors, subreddit)
    
    def collect_multiple_subreddits(self, subreddits: Optional[List[str]] = None,
                                   max_posts_per_subreddit: Optional[int] = None) -> List[CollectorResult]:
        """
        Collect posts from multiple subreddits.
        
        Args:
            subreddits: List of subreddit names (uses default list if not provided)
            max_posts_per_subreddit: Maximum posts per subreddit (uses config default if not provided)
        
        Returns:
            List of CollectorResult instances
        """
        if subreddits is None:
            subreddits = self.SUBREDDITS
        
        if max_posts_per_subreddit is None:
            max_posts_per_subreddit = self.config.max_articles_per_source
        
        logger.info(f"Collecting posts from {len(subreddits)} subreddits")
        
        results = []
        
        for subreddit in subreddits:
            try:
                logger.info(f"Collecting from r/{subreddit}...")
                result = self.collect(subreddit, max_posts_per_subreddit)
                results.append(result)
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit}: {e}")
                error_result = self._create_result(
                    articles=[],
                    errors=[f"Collection failed: {str(e)}"],
                    source=subreddit
                )
                results.append(error_result)
        
        return results
    
    def _create_result(self, articles: List[InvestmentArticle], 
                      errors: List[str], source: str) -> CollectorResult:
        """
        Create a CollectorResult with current timestamp.
        
        Args:
            articles: List of collected articles
            errors: List of errors encountered
            source: Source name
        
        Returns:
            CollectorResult instance
        """
        return CollectorResult(
            articles=articles,
            errors=errors,
            collected_at=datetime.utcnow(),
            source=f"reddit/r/{source}"
        )
    
    def close(self):
        """Close the requests session."""
        if self.session:
            self.session.close()


# Convenience function to create Reddit collector
def create_reddit_collector() -> RedditCollector:
    """
    Create a Reddit collector instance.
    
    Returns:
        RedditCollector instance
    """
    return RedditCollector()


# Convenience function to collect from all subreddits
def collect_all_reddit_subreddits(max_posts_per_subreddit: Optional[int] = None) -> List[CollectorResult]:
    """
    Collect posts from all predefined subreddits.
    
    Args:
        max_posts_per_subreddit: Maximum posts per subreddit (uses config default if not provided)
    
    Returns:
        List of CollectorResult instances
    """
    collector = create_reddit_collector()
    results = collector.collect_multiple_subreddits(max_posts_per_subreddit=max_posts_per_subreddit)
    collector.close()
    return results