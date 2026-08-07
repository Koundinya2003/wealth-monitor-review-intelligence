"""
Configuration and constants for the Investment Discovery Engine.
"""

from dataclasses import dataclass
from typing import List
import os


@dataclass
class DiscoveryConfig:
    """Configuration settings for the discovery engine"""
    
    # Collection settings
    max_articles_per_source: int = 50
    request_timeout: int = 10
    retry_attempts: int = 3
    
    # Cleaning settings
    min_content_length: int = 50
    max_content_length: int = 10000
    remove_html_tags: bool = True
    remove_special_chars: bool = True
    
    # Analysis settings
    min_relevance_score: float = 0.3
    max_insights_per_article: int = 3
    
    # Supported sources
    supported_sources: List[str] = None
    
    # Category keywords for classification
    category_keywords: dict = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.supported_sources is None:
            self.supported_sources = [
                "google_play",
                "youtube",
                "steam",
                "github",
                "hacker_news",
                "rss"
            ]
        
        if self.category_keywords is None:
            self.category_keywords = {
                "investment": ["invest", "stock", "mutual fund", "SIP", "portfolio"],
                "savings": ["save", "emergency fund", "fixed deposit", "FD"],
                "retirement": ["retirement", "NPS", "PPF", "pension"],
                "tax": ["tax", "ELSS", "80C", "deduction"],
                "insurance": ["insurance", "life insurance", "health insurance"],
                "real_estate": ["property", "real estate", "home loan", "REIT"],
                "crypto": ["crypto", "bitcoin", "blockchain", "digital currency"],
                "market_trends": ["market", "nifty", "sensex", "bull", "bear"]
            }


# Global configuration instance
config = DiscoveryConfig()