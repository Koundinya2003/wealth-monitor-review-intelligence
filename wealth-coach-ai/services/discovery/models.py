"""
Data models for the Investment Discovery Engine.

Defines clean dataclasses for articles, insights, and collection results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class InvestmentArticle:
    """
    Represents a single investment-related article or content piece.
    
    Attributes:
        title: Article title
        source: Source platform (e.g., 'google_play', 'youtube', 'hacker_news')
        url: Direct URL to the content
        published_at: Publication timestamp
        content: Full text content of the article
        category: Investment category (e.g., 'investment', 'savings', 'retirement')
        tags: List of relevant tags for categorization
        metadata: Additional source-specific metadata
    """
    title: str
    source: str
    url: str
    published_at: datetime
    content: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and clean data after initialization"""
        # Ensure title and content are stripped
        self.title = self.title.strip()
        self.content = self.content.strip()
        
        # Ensure source is lowercase
        self.source = self.source.lower()
        
        # Ensure tags are lowercase
        self.tags = [tag.lower().strip() for tag in self.tags]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestmentArticle":
        """Create instance from dictionary"""
        data["published_at"] = datetime.fromisoformat(data["published_at"])
        return cls(**data)


@dataclass
class DiscoveryInsight:
    """
    Represents an AI-generated insight from analyzing an article.
    
    Attributes:
        summary: Brief summary of the article content
        relevance_score: Score indicating relevance to user profile (0.0-1.0)
        recommendation: Specific actionable recommendation
        reason: Explanation of why this is relevant
        source: Source article URL or identifier
        confidence: Confidence level in the insight (0.0-1.0)
    """
    summary: str
    relevance_score: float
    recommendation: str
    reason: str
    source: str
    confidence: float = 0.0
    
    def __post_init__(self):
        """Validate data after initialization"""
        # Clamp scores to valid range
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Clean strings
        self.summary = self.summary.strip()
        self.recommendation = self.recommendation.strip()
        self.reason = self.reason.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "summary": self.summary,
            "relevance_score": self.relevance_score,
            "recommendation": self.recommendation,
            "reason": self.reason,
            "source": self.source,
            "confidence": self.confidence
        }


@dataclass
class CollectorResult:
    """
    Represents the result of a collection operation from a single source.
    
    Attributes:
        articles: List of successfully collected articles
        errors: List of errors encountered during collection
        collected_at: Timestamp when collection was performed
        source: Name of the source that was collected
        total_count: Total number of articles collected
    """
    articles: List[InvestmentArticle]
    errors: List[str]
    collected_at: datetime
    source: str
    total_count: int = 0
    
    def __post_init__(self):
        """Calculate total count if not provided"""
        if self.total_count == 0:
            self.total_count = len(self.articles)
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result"""
        self.errors.append(error)
    
    def add_article(self, article: InvestmentArticle) -> None:
        """Add an article to the result"""
        self.articles.append(article)
        self.total_count = len(self.articles)
    
    def is_successful(self) -> bool:
        """Check if collection was successful (no errors)"""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "articles": [article.to_dict() for article in self.articles],
            "errors": self.errors,
            "collected_at": self.collected_at.isoformat(),
            "source": self.source,
            "total_count": self.total_count
        }