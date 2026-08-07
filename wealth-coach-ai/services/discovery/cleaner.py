"""
Content cleaning and normalization for the Investment Discovery Engine.

Provides utilities for cleaning, normalizing, and preparing collected content
for analysis and AI processing.
"""

import re
import html
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .models import InvestmentArticle
from .config import config

logger = logging.getLogger(__name__)


class ContentCleaner:
    """
    Cleans and normalizes investment-related content.
    
    Handles HTML removal, special character cleaning, text normalization,
    and content validation.
    """
    
    def __init__(self):
        """Initialize the cleaner with configuration settings."""
        self.config = config
        self.html_pattern = re.compile(r'<[^>]+>')
        self.special_chars_pattern = re.compile(r'[^\w\s\-.,!?;:()₹%]')
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Category keywords for classification
        self.category_keywords = {
            'market_news': ['market', 'stock', 'trading', 'nifty', 'sensex', 'bull', 'bear', 'index', 'shares'],
            'mutual_funds': ['mutual fund', 'sip', 'nav', 'amc', 'fund manager', 'equity fund', 'debt fund'],
            'government_policy': ['rbi', 'reserve bank', 'government', 'policy', 'regulation', 'sebi', 'ministry', 'budget'],
            'tax': ['tax', '80c', 'deduction', 'income tax', 'gst', 'tax saving', 'elss', 'tax slab'],
            'gold': ['gold', 'gold etf', 'sovereign gold bond', 'sgb', 'precious metal'],
            'debt': ['bond', 'fixed deposit', 'fd', 'debt', 'corporate bond', 'government bond', 'ncd', 'debenture'],
            'equity': ['equity', 'share', 'stock market', 'ipo', 'listing', 'dividend', 'equity fund'],
            'education': ['learn', 'course', 'certification', 'skill', 'career', 'job', 'salary', 'investment basics']
        }
        
        # Advertisement patterns
        self.ad_patterns = [
            r'click here',
            r'subscribe now',
            r'limited time offer',
            r'buy now',
            r'special offer',
            r'discount',
            r'promotion',
            r'advertisement',
            r'sponsored',
            r'paid content',
            r'subscribe',
            r'newsletter',
            r'follow us',
            r'like us',
            r'share this',
            r'related articles',
            r'you may also like',
            r'recommended for you',
            r'trending now',
            r'popular posts',
            r'most read',
            r'top stories'
        ]
        
        # Navigation patterns
        self.nav_patterns = [
            r'home\s*\|',
            r'\|.*home',
            r'menu\s*:',
            r'nav\s*:',
            r'breadcrumb',
            r'you are here',
            r'previous\s*\|',
            r'next\s*\|',
            r'back to',
            r'return to',
            r'jump to',
            r'skip to',
            r'copyright\s*©',
            r'all rights reserved',
            r'terms of use',
            r'privacy policy',
            r'cookie policy',
            r'about us',
            r'contact us',
            r'advertise with us',
            r'feedback',
            r'sitemap'
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean raw text by removing HTML tags, ads, navigation, and special characters.
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Unescape HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags if configured
        if self.config.remove_html_tags:
            text = self.html_pattern.sub(' ', text)
        
        # Remove advertisements
        text = self._remove_ads(text)
        
        # Remove navigation text
        text = self._remove_navigation(text)
        
        # Remove special characters if configured (preserve newlines)
        if self.config.remove_special_chars:
            # Preserve paragraph breaks
            text = text.replace('\n\n', '\n\n')
            text = text.replace('\n', ' ')
            text = self.special_chars_pattern.sub('', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def clean_article(self, article: InvestmentArticle) -> Optional[InvestmentArticle]:
        """
        Clean an investment article's content.
        
        Args:
            article: InvestmentArticle to clean
        
        Returns:
            Cleaned InvestmentArticle or None if article should be discarded
        """
        try:
            # Clean title
            cleaned_title = self.clean_text(article.title)
            
            # Clean content
            cleaned_content = self.clean_text(article.content)
            
            # Validate content length
            if len(cleaned_content) < self.config.min_content_length:
                logger.warning(
                    f"Article content too short after cleaning: {len(cleaned_content)} chars. "
                    f"Discarding: {article.title[:50]}..."
                )
                return None
            
            if len(cleaned_content) > self.config.max_content_length:
                logger.info(
                    f"Truncating article content from {len(cleaned_content)} to "
                    f"{self.config.max_content_length} chars"
                )
                cleaned_content = cleaned_content[:self.config.max_content_length]
            
            # Create cleaned article
            cleaned_article = InvestmentArticle(
                title=cleaned_title,
                source=article.source,
                url=article.url,
                published_at=article.published_at,
                content=cleaned_content,
                category=article.category,
                tags=article.tags,
                metadata=article.metadata
            )
            
            return cleaned_article
            
        except Exception as e:
            logger.error(f"Error cleaning article: {e}")
            return None
    
    def clean_articles(self, articles: List[InvestmentArticle]) -> List[InvestmentArticle]:
        """
        Clean a list of articles.
        
        Args:
            articles: List of InvestmentArticle objects to clean
        
        Returns:
            List of cleaned InvestmentArticle objects
        """
        cleaned_articles = []
        
        for article in articles:
            cleaned = self.clean_article(article)
            if cleaned:
                cleaned_articles.append(cleaned)
        
        logger.info(
            f"Cleaned {len(articles)} articles, "
            f"{len(cleaned_articles)} passed validation"
        )
        
        return cleaned_articles
    
    def normalize_category(self, text: str) -> str:
        """
        Normalize category text to standard format.
        
        Args:
            text: Category text to normalize
        
        Returns:
            Normalized category string
        """
        text = text.lower().strip()
        text = self.whitespace_pattern.sub('_', text)
        return text
    
    def extract_tags(self, text: str, max_tags: int = 10) -> List[str]:
        """
        Extract relevant tags from text based on category keywords.
        
        Args:
            text: Text to extract tags from
            max_tags: Maximum number of tags to extract
        
        Returns:
            List of extracted tags
        """
        text_lower = text.lower()
        tags = []
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower and category not in tags:
                    tags.append(category)
                    break
        
        return tags[:max_tags]
    
    def validate_url(self, url: str) -> bool:
        """
        Validate that a URL is properly formatted.
        
        Args:
            url: URL to validate
        
        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        
        return bool(url_pattern.match(url))
    
    def remove_duplicates(self, articles: List[InvestmentArticle]) -> List[InvestmentArticle]:
        """
        Remove duplicate articles based on URL and title similarity.
        
        Args:
            articles: List of articles to deduplicate
        
        Returns:
            List of unique articles
        """
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Normalize URL and title for comparison
            url_normalized = article.url.lower().strip()
            title_normalized = article.title.lower().strip()
            
            # Check if we've seen this URL or very similar title
            if url_normalized in seen_urls:
                logger.debug(f"Duplicate URL found: {url_normalized}")
                continue
            
            if title_normalized in seen_titles:
                logger.debug(f"Duplicate title found: {title_normalized}")
                continue
            
            seen_urls.add(url_normalized)
            seen_titles.add(title_normalized)
            unique_articles.append(article)
        
        if len(unique_articles) < len(articles):
            logger.info(
                f"Removed {len(articles) - len(unique_articles)} duplicate articles"
            )
        
        return unique_articles
    
    def _remove_ads(self, text: str) -> str:
        """
        Remove advertisement text from content.
        
        Args:
            text: Text to clean
        
        Returns:
            Text with advertisements removed
        """
        text_lower = text.lower()
        
        for pattern in self.ad_patterns:
            # Check if pattern exists in text
            if re.search(pattern, text_lower):
                # Remove the line containing the ad
                lines = text.split('\n')
                cleaned_lines = []
                for line in lines:
                    if not re.search(pattern, line.lower()):
                        cleaned_lines.append(line)
                text = '\n'.join(cleaned_lines)
        
        return text
    
    def _remove_navigation(self, text: str) -> str:
        """
        Remove navigation text from content.
        
        Args:
            text: Text to clean
        
        Returns:
            Text with navigation removed
        """
        text_lower = text.lower()
        
        for pattern in self.nav_patterns:
            # Check if pattern exists in text
            if re.search(pattern, text_lower):
                # Remove the line containing navigation
                lines = text.split('\n')
                cleaned_lines = []
                for line in lines:
                    if not re.search(pattern, line.lower()):
                        cleaned_lines.append(line)
                text = '\n'.join(cleaned_lines)
        
        return text
    
    def assign_category(self, article: InvestmentArticle) -> InvestmentArticle:
        """
        Assign category to article based on keyword matching.
        
        Args:
            article: Article to categorize
        
        Returns:
            Article with assigned category
        """
        # Combine title and content for analysis
        text_to_analyze = (article.title + " " + article.content).lower()
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                score += text_to_analyze.count(keyword)
            category_scores[category] = score
        
        # Assign category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                article.category = best_category
                logger.debug(f"Assigned category '{best_category}' to article: {article.title[:50]}")
        
        return article
    
    def enrich_article(self, article: InvestmentArticle) -> InvestmentArticle:
        """
        Enrich article with additional metadata.
        
        Args:
            article: Article to enrich
        
        Returns:
            Enriched article
        """
        # Extract tags if not already present
        if not article.tags:
            article.tags = self.extract_tags(article.title + " " + article.content)
        
        # Assign category based on content
        article = self.assign_category(article)
        
        # Validate and clean URL
        if not self.validate_url(article.url):
            logger.warning(f"Invalid URL found: {article.url}")
        
        return article
    
    def process_batch(self, articles: List[InvestmentArticle]) -> List[InvestmentArticle]:
        """
        Process a batch of articles through the full cleaning pipeline.
        
        Args:
            articles: List of raw articles
        
        Returns:
            List of cleaned, deduplicated, and enriched articles
        """
        logger.info(f"Processing batch of {len(articles)} articles")
        
        # Step 1: Clean individual articles
        cleaned = self.clean_articles(articles)
        
        # Step 2: Remove duplicates
        deduplicated = self.remove_duplicates(cleaned)
        
        # Step 3: Enrich with metadata
        enriched = [self.enrich_article(article) for article in deduplicated]
        
        logger.info(f"Batch processing complete: {len(enriched)} articles ready for analysis")
        
        return enriched