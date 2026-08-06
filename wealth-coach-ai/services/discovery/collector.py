"""
Content collectors for the Investment Discovery Engine.

Provides base classes, registry, and orchestration for collecting investment-related content
from various sources (RSS, NewsAPI, Reddit).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
import json

from .models import InvestmentArticle, CollectorResult
from .config import config

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all content collectors.
    
    All collectors must implement the collect() method and can optionally
    implement validate_source() for source-specific validation.
    """
    
    def __init__(self, source_name: str):
        """
        Initialize the collector.
        
        Args:
            source_name: Name of the source (e.g., 'rss', 'newsapi', 'reddit')
        """
        self.source_name = source_name
        self.config = config
    
    @abstractmethod
    def collect(self, **kwargs) -> CollectorResult:
        """
        Collect articles from the source.
        
        Args:
            **kwargs: Source-specific parameters
        
        Returns:
            CollectorResult containing collected articles and any errors
        """
        pass
    
    def validate_source(self) -> bool:
        """
        Validate that the source is supported and configured.
        
        Returns:
            True if source is valid, False otherwise
        """
        return True
    
    def create_result(self, articles: List[InvestmentArticle], 
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
    
    def _create_article(self, title: str, url: str, content: str, 
                       published_at: datetime, category: str = "general",
                       tags: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> InvestmentArticle:
        """
        Create an InvestmentArticle with standard fields.
        
        Args:
            title: Article title
            url: Article URL
            content: Article content
            published_at: Publication timestamp
            category: Article category
            tags: List of tags
            metadata: Additional metadata
        
        Returns:
            InvestmentArticle instance
        """
        return InvestmentArticle(
            title=title,
            source=self.source_name,
            url=url,
            published_at=published_at,
            content=content,
            category=category,
            tags=tags or [],
            metadata=metadata or {}
        )


class CollectorRegistry:
    """
    Registry for managing and accessing content collectors.
    
    Provides a centralized way to register and retrieve collectors
    for different sources.
    """
    
    def __init__(self):
        """Initialize the registry with an empty collector dictionary."""
        self._collectors: Dict[str, BaseCollector] = {}
    
    def register(self, collector: BaseCollector) -> None:
        """
        Register a collector for a specific source.
        
        Args:
            collector: BaseCollector instance to register
        
        Raises:
            ValueError: If collector with same source_name already registered
        """
        if collector.source_name in self._collectors:
            raise ValueError(
                f"Collector for source '{collector.source_name}' already registered"
            )
        
        self._collectors[collector.source_name] = collector
        logger.info(f"Registered collector for source: {collector.source_name}")
    
    def get(self, source_name: str) -> Optional[BaseCollector]:
        """
        Get a collector by source name.
        
        Args:
            source_name: Name of the source
        
        Returns:
            BaseCollector instance or None if not found
        """
        return self._collectors.get(source_name)
    
    def get_all(self) -> Dict[str, BaseCollector]:
        """
        Get all registered collectors.
        
        Returns:
            Dictionary of source_name -> BaseCollector
        """
        return self._collectors.copy()
    
    def collect_from_source(self, source_name: str, **kwargs) -> CollectorResult:
        """
        Collect articles from a specific source.
        
        Args:
            source_name: Name of the source to collect from
            **kwargs: Source-specific parameters
        
        Returns:
            CollectorResult with collected articles
        
        Raises:
            ValueError: If source is not registered
        """
        collector = self.get(source_name)
        
        if collector is None:
            raise ValueError(
                f"No collector registered for source: {source_name}. "
                f"Available sources: {list(self._collectors.keys())}"
            )
        
        logger.info(f"Collecting from source: {source_name}")
        return collector.collect(**kwargs)
    
    def collect_from_all(self, **kwargs) -> List[CollectorResult]:
        """
        Collect articles from all registered sources.
        
        Args:
            **kwargs: Parameters to pass to all collectors
        
        Returns:
            List of CollectorResult instances
        """
        results = []
        
        for source_name, collector in self._collectors.items():
            try:
                logger.info(f"Collecting from source: {source_name}")
                result = collector.collect(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error collecting from {source_name}: {e}")
                results.append(collector.create_result(
                    articles=[],
                    errors=[f"Collection failed: {str(e)}"]
                ))
        
        return results


# Global registry instance
registry = CollectorRegistry()


def collect_all_articles() -> List[InvestmentArticle]:
    """
    Collect articles from all sources (RSS, NewsAPI, Reddit).
    
    This is the main orchestration function that runs all collectors
    independently and merges their results. If one collector fails,
    it logs the error and continues with the others.
    
    Returns:
        List of InvestmentArticle objects from all sources
    """
    logger.info("Starting collection from all sources")
    
    all_articles = []
    collection_stats = {
        'rss': {'success': False, 'count': 0, 'error': None},
        'newsapi': {'success': False, 'count': 0, 'error': None},
        'reddit': {'success': False, 'count': 0, 'error': None}
    }
    
    # Import collectors here to avoid circular imports
    from .rss_collector import collect_all_rss_feeds
    from .newsapi_collector import collect_all_newsapi_topics
    from .reddit_collector import collect_all_reddit_subreddits
    
    # Collect from RSS feeds
    try:
        logger.info("Collecting from RSS feeds...")
        rss_results = collect_all_rss_feeds(max_articles_per_source=10)
        for result in rss_results:
            all_articles.extend(result.articles)
            collection_stats['rss']['success'] = True
            collection_stats['rss']['count'] += len(result.articles)
        logger.info(f"RSS collection complete: {collection_stats['rss']['count']} articles")
    except Exception as e:
        error_msg = f"RSS collection failed: {str(e)}"
        logger.error(error_msg)
        collection_stats['rss']['error'] = error_msg
    
    # Collect from NewsAPI
    try:
        logger.info("Collecting from NewsAPI...")
        newsapi_results = collect_all_newsapi_topics(max_articles_per_topic=5)
        for result in newsapi_results:
            all_articles.extend(result.articles)
            collection_stats['newsapi']['success'] = True
            collection_stats['newsapi']['count'] += len(result.articles)
        logger.info(f"NewsAPI collection complete: {collection_stats['newsapi']['count']} articles")
    except Exception as e:
        error_msg = f"NewsAPI collection failed: {str(e)}"
        logger.error(error_msg)
        collection_stats['newsapi']['error'] = error_msg
    
    # Collect from Reddit
    try:
        logger.info("Collecting from Reddit...")
        reddit_results = collect_all_reddit_subreddits(max_posts_per_subreddit=10)
        for result in reddit_results:
            all_articles.extend(result.articles)
            collection_stats['reddit']['success'] = True
            collection_stats['reddit']['count'] += len(result.articles)
        logger.info(f"Reddit collection complete: {collection_stats['reddit']['count']} articles")
    except Exception as e:
        error_msg = f"Reddit collection failed: {str(e)}"
        logger.error(error_msg)
        collection_stats['reddit']['error'] = error_msg
    
    # Log summary
    total_collected = len(all_articles)
    logger.info(f"Total articles collected: {total_collected}")
    logger.info(f"Collection stats: {collection_stats}")
    
    # Store stats in a global variable for debugging
    global _last_collection_stats
    _last_collection_stats = collection_stats
    
    return all_articles


def get_collection_stats() -> Dict[str, Any]:
    """
    Get statistics from the last collection run.
    
    Returns:
        Dictionary with collection statistics
    """
    global _last_collection_stats
    return getattr(_last_collection_stats, '_last_collection_stats', {
        'rss': {'success': False, 'count': 0, 'error': None},
        'newsapi': {'success': False, 'count': 0, 'error': None},
        'reddit': {'success': False, 'count': 0, 'error': None}
    })


def load_fallback_articles() -> List[InvestmentArticle]:
    """
    Load fallback demo articles when no articles are collected.
    
    Returns:
        List of demo InvestmentArticle objects
    """
    logger.info("Loading fallback demo articles")
    
    # Try to load from file first
    fallback_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'demo_investments.json')
    
    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = []
            for item in data:
                article = InvestmentArticle(
                    title=item.get('title', ''),
                    source=item.get('source', 'demo'),
                    url=item.get('url', ''),
                    published_at=datetime.fromisoformat(item.get('published_at', datetime.utcnow().isoformat())),
                    content=item.get('content', ''),
                    category=item.get('category', 'general'),
                    tags=item.get('tags', []),
                    metadata=item.get('metadata', {})
                )
                articles.append(article)
            
            logger.info(f"Loaded {len(articles)} fallback articles from file")
            return articles
        except Exception as e:
            logger.error(f"Error loading fallback articles from file: {e}")
    
    # If file doesn't exist or can't be loaded, create demo articles
    logger.info("Creating demo articles programmatically")
    return _create_demo_articles()


def _create_demo_articles() -> List[InvestmentArticle]:
    """
    Create demo articles for fallback when no real articles are available.
    
    Returns:
        List of demo InvestmentArticle objects
    """
    demo_articles = [
        {
            "title": "SIP Investment: A Systematic Approach to Wealth Creation",
            "content": "Systematic Investment Plans (SIPs) allow investors to invest a fixed amount regularly in mutual funds. "
                      "This disciplined approach helps in rupee cost averaging and building wealth over time. "
                      "Starting with as little as ₹500 per month, SIPs are ideal for salaried individuals. "
                      "Consider increasing your SIP amount by 10-15% annually as your income grows.",
            "category": "mutual_funds",
            "source": "demo",
            "url": "https://example.com/sip-guide",
            "tags": ["sip", "mutual funds", "wealth creation"]
        },
        {
            "title": "Index Funds: Low-Cost Way to Invest in Stock Markets",
            "content": "Index funds track market indices like Nifty 50 or Sensex, offering diversification at low cost. "
                      "With expense ratios as low as 0.05-0.5%, they outperform most actively managed funds over the long term. "
                      "Perfect for beginners seeking market returns without stock-picking complexity.",
            "category": "equity",
            "source": "demo",
            "url": "https://example.com/index-funds",
            "tags": ["index funds", "low cost", "diversification"]
        },
        {
            "title": "Gold ETFs vs Sovereign Gold Bonds: Which is Better?",
            "content": "Gold ETFs offer liquidity and ease of trading like stocks, while Sovereign Gold Bonds (SGBs) provide 2.5% annual interest. "
                      "SGBs have an 8-year lock-in but no capital gains tax on redemption. "
                      "Gold ETFs are better for short-term needs, SGBs for long-term portfolio diversification.",
            "category": "gold",
            "source": "demo",
            "url": "https://example.com/gold-investment",
            "tags": ["gold", "etf", "sovereign gold bonds"]
        },
        {
            "title": "PPF vs NPS: Which Retirement Scheme is Right for You?",
            "content": "Public Provident Fund (PPF) offers guaranteed 7.1% returns with EEE tax benefits. "
                      "National Pension System (NPS) provides higher potential returns (9-12%) with partial tax benefits. "
                      "PPF is ideal for conservative investors, NPS for those comfortable with market-linked returns.",
            "category": "retirement",
            "source": "demo",
            "url": "https://example.com/ppf-vs-nps",
            "tags": ["ppf", "nps", "retirement", "tax saving"]
        },
        {
            "title": "RBI Repo Rate Hike: Impact on Your Investments",
            "content": "The Reserve Bank of India recently hiked the repo rate by 25 basis points to 6.5%. "
                      "This makes debt instruments more attractive while putting pressure on equity markets. "
                      "Consider increasing allocation to short-term debt funds and reducing equity exposure temporarily.",
            "category": "government_policy",
            "source": "demo",
            "url": "https://example.com/rbi-rate-hike",
            "tags": ["rbi", "repo rate", "monetary policy"]
        },
        {
            "title": "SEBI's New Mutual Fund Categorization Rules",
            "content": "SEBI has simplified mutual fund categories to help investors choose better. "
                      "Now there are clear definitions for large-cap, mid-cap, and small-cap funds. "
                      "This transparency helps in comparing funds within the same category and making informed decisions.",
            "category": "government_policy",
            "source": "demo",
            "url": "https://example.com/sebi-mf-categorization",
            "tags": ["sebi", "mutual funds", "regulation"]
        },
        {
            "title": "Tax Saving Under 80C: ELSS vs PPF vs Life Insurance",
            "content": "ELSS (Equity Linked Savings Scheme) offers 12-15% returns with 3-year lock-in, "
                      "outperforming PPF (7.1%) and traditional life insurance (4-6%). "
                      "For tax saving under 80C, ELSS is the best choice for long-term wealth creation.",
            "category": "tax",
            "source": "demo",
            "url": "https://example.com/80c-tax-saving",
            "tags": ["tax", "80c", "elss", "ppf"]
        },
        {
            "title": "Emergency Fund: How Much is Enough?",
            "content": "Financial experts recommend maintaining 6-12 months of expenses as an emergency fund. "
                      "Keep this in a liquid fund or high-yield savings account for easy access. "
                      "This safety net prevents you from breaking long-term investments during crises.",
            "category": "emergency_fund",
            "source": "demo",
            "url": "https://example.com/emergency-fund",
            "tags": ["emergency fund", "savings", "liquidity"]
        },
        {
            "title": "Debt Funds vs Fixed Deposits: Where to Invest?",
            "content": "Debt funds offer better tax efficiency than FDs for investments beyond 3 years. "
                      "While FDs give guaranteed returns, debt funds provide 8-10% returns with indexation benefits. "
                      "For investors in 30% tax bracket, debt funds are more tax-efficient after 3 years.",
            "category": "debt",
            "source": "demo",
            "url": "https://example.com/debt-funds-vs-fd",
            "tags": ["debt funds", "fixed deposits", "tax efficiency"]
        },
        {
            "title": "Portfolio Rebalancing: Why and When to Do It",
            "content": "Portfolio rebalancing involves adjusting your asset allocation back to target percentages. "
                      "Do this annually or when any asset class deviates by 5-10% from target. "
                      "This maintains your risk level and can improve returns by 0.5-1% annually.",
            "category": "market_news",
            "source": "demo",
            "url": "https://example.com/portfolio-rebalancing",
            "tags": ["portfolio", "rebalancing", "asset allocation"]
        },
        {
            "title": "Sovereign Gold Bonds vs Physical Gold: Smart Investment Choice",
            "content": "Sovereign Gold Bonds (SGBs) offer 2.5% annual interest plus gold price appreciation. "
                      "They're safer than physical gold (no making charges, theft risk) and more tax-efficient. "
                      "SGBs mature in 8 years with capital gains tax exemption. Available in primary and secondary markets.",
            "category": "gold",
            "source": "demo",
            "url": "https://example.com/sovereign-gold-bonds",
            "tags": ["gold", "sovereign gold bonds", "tax efficient"]
        },
        {
            "title": "NPS Tier 2 Account: Liquidity Meets Tax Benefits",
            "content": "NPS Tier 2 account offers liquidity while maintaining tax benefits under Section 80C. "
                      "Unlike Tier 1 (locked till retirement), Tier 2 allows partial withdrawals. "
                      "Ideal for those wanting NPS tax benefits without complete lock-in.",
            "category": "retirement",
            "source": "demo",
            "url": "https://example.com/nps-tier-2",
            "tags": ["nps", "retirement", "tax benefits"]
        },
        {
            "title": "Market Volatility: Should You Stop Your SIPs?",
            "content": "During market downturns, continuing SIPs actually helps through rupee cost averaging. "
                      "You buy more units when markets are low, boosting long-term returns. "
                      "Historical data shows SIPs during volatility delivered 2-3% higher returns over 5+ years.",
            "category": "market_news",
            "source": "demo",
            "url": "https://example.com/sip-during-volatility",
            "tags": ["sip", "market volatility", "rupee cost averaging"]
        },
        {
            "title": "ELSS Funds: Best Tax-Saving Investment for 2024",
            "content": "ELSS (Equity Linked Savings Scheme) combines tax saving with wealth creation. "
                      "With 3-year lock-in (shortest among 80C options) and 12-15% historical returns, "
                      "ELSS beats PPF, FD, and insurance for long-term goals. Top funds include Mirae Asset and Axis Long Term Equity.",
            "category": "tax",
            "source": "demo",
            "url": "https://example.com/best-elss-funds",
            "tags": ["elss", "tax saving", "80c", "equity"]
        },
        {
            "title": "Debt Mutual Funds: Safe Haven in Volatile Markets",
            "content": "Debt mutual funds invest in fixed-income securities like bonds and treasury bills. "
                      "They offer 7-9% returns with lower volatility than equity. "
                      "Liquid funds (for <3 months), ultra-short (3-6 months), and short-term (6 months-3 years) "
                      "cater to different time horizons.",
            "category": "debt",
            "source": "demo",
            "url": "https://example.com/debt-mutual-funds",
            "tags": ["debt funds", "bonds", "fixed income"]
        },
        {
            "title": "Emergency Fund Planning: Your Financial Safety Net",
            "content": "An emergency fund covers 6-12 months of expenses for unexpected situations like job loss or medical emergencies. "
                      "Park this in liquid funds or high-yield savings accounts earning 4-6% annually. "
                      "Build it before starting investments - it's the foundation of financial security.",
            "category": "emergency_fund",
            "source": "demo",
            "url": "https://example.com/emergency-fund-planning",
            "tags": ["emergency fund", "financial planning", "liquidity"]
        },
        {
            "title": "RBI's New Digital Rupee: What Investors Should Know",
            "content": "RBI's Digital Rupee (e-Rupee) is a Central Bank Digital Currency (CBDC) launched for retail use. "
                      "While not an investment vehicle yet, it represents the future of digital payments. "
                      "Monitor developments as CBDCs could impact banking and payment stocks.",
            "category": "government_policy",
            "source": "demo",
            "url": "https://example.com/digital-rupee",
            "tags": ["rbi", "digital currency", "fintech"]
        },
        {
            "title": "SEBI Crackdown on Mis-selling in Mutual Funds",
            "content": "SEBI has tightened norms to prevent mis-selling of mutual funds by distributors. "
                      "New rules mandate risk disclosure and suitability assessment before recommending funds. "
                      "Investors should verify if recommendations match their risk profile and financial goals.",
            "category": "government_policy",
            "source": "demo",
            "url": "https://example.com/sebi-mis-selling",
            "tags": ["sebi", "mutual funds", "investor protection"]
        },
        {
            "title": "SIP vs Lumpsum: Which Investment Strategy is Better?",
            "content": "SIP (Systematic Investment Plan) averages market volatility through regular investments. "
                      "Lumpsum investing works better in rising markets but risks timing the market. "
                      "For salaried investors, SIPs are ideal. For windfall gains, consider dollar-cost averaging over 6-12 months.",
            "category": "mutual_funds",
            "source": "demo",
            "url": "https://example.com/sip-vs-lumpsum",
            "tags": ["sip", "lumpsum", "investment strategy"]
        },
        {
            "title": "Tax-Saving Investments Beyond 80C",
            "content": "Beyond 80C (1.5L limit), consider NPS (additional 50K deduction), "
                      "health insurance (25K deduction), and home loan interest (2L deduction). "
                      "These additional benefits can save ₹40K+ in taxes for high-income individuals.",
            "category": "tax",
            "source": "demo",
            "url": "https://example.com/tax-saving-beyond-80c",
            "tags": ["tax", "80c", "nps", "tax planning"]
        }
    ]
    
    # Convert to InvestmentArticle objects
    articles = []
    for item in demo_articles:
        article = InvestmentArticle(
            title=item['title'],
            source=item['source'],
            url=item['url'],
            published_at=datetime.utcnow(),
            content=item['content'],
            category=item['category'],
            tags=item['tags'],
            metadata={'is_demo': True}
        )
        articles.append(article)
    
    logger.info(f"Created {len(articles)} demo articles")
    return articles


# Global variable to store last collection stats
_last_collection_stats = {
    'rss': {'success': False, 'count': 0, 'error': None},
    'newsapi': {'success': False, 'count': 0, 'error': None},
    'reddit': {'success': False, 'count': 0, 'error': None}
}