"""
Insight analyzer for the Investment Discovery Engine.

Provides methods for analyzing collected articles and generating
AI-ready insights for investment recommendations using OpenRouter.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
import json

import requests

from .models import InvestmentArticle, DiscoveryInsight, CollectorResult
from .config import config

logger = logging.getLogger(__name__)


class InsightAnalyzer:
    """
    Analyzes investment articles and generates insights using OpenRouter AI.
    
    Analyzes collected investment content and generates structured insights
    including opportunities, market summary, policy updates, recommendations, and risks.
    """
    
    def __init__(self):
        """Initialize the analyzer with configuration settings."""
        self.config = config
        self.min_relevance_score = config.min_relevance_score
        self.max_insights_per_article = config.max_insights_per_article
        
        # OpenRouter configuration
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3-0324:free')
        self.base_url = "https://api.openrouter.ai/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")
    
    def _call_openrouter(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """
        Call OpenRouter API with the given prompt.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
        
        Returns:
            Response text or None if request failed
        """
        if not self.api_key:
            logger.error("Cannot call OpenRouter: API key not configured")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial analyst assistant. Analyze the provided investment articles and return structured JSON only. Do not include any text outside the JSON structure."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=body,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text[:200]}")
                return None
            
            data = response.json()
            choices = data.get('choices', [])
            
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                return content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON response from OpenRouter.
        
        Args:
            response: Response text from OpenRouter
        
        Returns:
            Parsed JSON dictionary or None if parsing failed
        """
        try:
            # Try to extract JSON from response (in case there's extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # If no JSON found, try parsing entire response
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            return None
    
    def analyze_article(self, article: InvestmentArticle, 
                       user_context: Optional[Dict[str, Any]] = None) -> List[DiscoveryInsight]:
        """
        Analyze a single article and generate insights.
        
        Args:
            article: InvestmentArticle to analyze
            user_context: Optional user profile context for personalization
        
        Returns:
            List of DiscoveryInsight objects generated from the article
        """
        logger.info(f"Analyzing article: {article.title[:50]}...")
        
        insights = []
        
        # For single article, create a simple insight
        # Full batch analysis is done in analyze_batch
        try:
            insight = DiscoveryInsight(
                summary=article.content[:200] + "..." if len(article.content) > 200 else article.content,
                relevance_score=0.5,
                recommendation=f"Article from {article.source}: {article.title}",
                reason=f"Category: {article.category}",
                source=article.url,
                confidence=0.5
            )
            insights.append(insight)
        except Exception as e:
            logger.error(f"Error creating insight for article: {e}")
        
        logger.debug(f"Generated {len(insights)} insights from article")
        return insights
    
    def analyze_batch(self, articles: List[InvestmentArticle],
                     user_context: Optional[Dict[str, Any]] = None) -> List[DiscoveryInsight]:
        """
        Analyze a batch of articles and generate insights using OpenRouter.
        
        Args:
            articles: List of InvestmentArticle objects to analyze
            user_context: Optional user profile context for personalization
        
        Returns:
            List of DiscoveryInsight objects from all articles
        """
        logger.info(f"Analyzing batch of {len(articles)} articles")
        
        if not articles:
            return []
        
        # Prepare articles summary for the prompt
        articles_summary = []
        for i, article in enumerate(articles[:20], 1):  # Limit to 20 articles for context
            articles_summary.append(
                f"{i}. [{article.category}] {article.title}\n"
                f"   Source: {article.source}\n"
                f"   Content: {article.content[:500]}...\n"
            )
        
        articles_text = "\n".join(articles_summary)
        
        # Create prompt for OpenRouter
        prompt = f"""Analyze the following {len(articles[:20])} investment-related articles and provide a comprehensive analysis in JSON format.

Articles:
{articles_text}

Provide analysis in the following JSON structure:
{{
    "top_opportunities": [
        {{
            "title": "Opportunity title",
            "description": "Brief description",
            "category": "category name",
            "relevance_score": 0.0-1.0,
            "source": "source name"
        }}
    ],
    "market_summary": "2-3 sentence summary of current market trends based on the articles",
    "important_policy_updates": [
        {{
            "policy": "Policy name",
            "impact": "Description of impact",
            "source": "source name"
        }}
    ],
    "investment_recommendations": [
        {{
            "recommendation": "Specific recommendation",
            "reasoning": "Why this recommendation",
            "risk_level": "Low/Medium/High"
        }}
    ],
    "risks": [
        {{
            "risk": "Risk description",
            "severity": "Low/Medium/High",
            "mitigation": "How to mitigate"
        }}
    ],
    "confidence_score": 0.0-1.0
}}

Return ONLY valid JSON. Do not include any text before or after the JSON."""
        
        # Call OpenRouter
        response = self._call_openrouter(prompt, max_tokens=2000)
        
        if not response:
            logger.warning("OpenRouter call failed, returning empty insights")
            return []
        
        # Parse JSON response
        analysis = self._parse_json_response(response)
        
        if not analysis:
            logger.warning("Failed to parse OpenRouter response")
            return []
        
        # Convert to DiscoveryInsight objects
        all_insights = []
        
        # Create insights from top opportunities
        for opp in analysis.get('top_opportunities', []):
            try:
                insight = DiscoveryInsight(
                    summary=opp.get('title', ''),
                    relevance_score=float(opp.get('relevance_score', 0.5)),
                    recommendation=opp.get('description', ''),
                    reason=f"Category: {opp.get('category', 'general')}",
                    source=opp.get('source', ''),
                    confidence=float(analysis.get('confidence_score', 0.5))
                )
                all_insights.append(insight)
            except Exception as e:
                logger.error(f"Error creating insight from opportunity: {e}")
                continue
        
        logger.info(f"Batch analysis complete: {len(all_insights)} insights generated from OpenRouter")
        
        return all_insights
    
    def calculate_relevance_score(self, article: InvestmentArticle,
                                  user_context: Dict[str, Any]) -> float:
        """
        Calculate relevance score for an article based on user context.
        
        Args:
            article: InvestmentArticle to score
            user_context: User profile and preferences
        
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Placeholder implementation - can be enhanced later with AI
        score = 0.5  # Default neutral score
        
        # Simple keyword matching for now
        text = (article.title + " " + article.content).lower()
        
        # Boost score if article category matches user goal
        user_goal = user_context.get('goal', '').lower()
        if user_goal and article.category:
            if user_goal.replace(' ', '_') in article.category.lower():
                score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def filter_by_relevance(self, insights: List[DiscoveryInsight],
                           min_score: Optional[float] = None) -> List[DiscoveryInsight]:
        """
        Filter insights by minimum relevance score.
        
        Args:
            insights: List of DiscoveryInsight objects
            min_score: Minimum relevance score (uses config default if not provided)
        
        Returns:
            Filtered list of insights
        """
        if min_score is None:
            min_score = self.min_relevance_score
        
        filtered = [insight for insight in insights if insight.relevance_score >= min_score]
        
        logger.info(
            f"Filtered {len(insights)} insights to {len(filtered)} "
            f"(min score: {min_score})"
        )
        
        return filtered
    
    def rank_insights(self, insights: List[DiscoveryInsight]) -> List[DiscoveryInsight]:
        """
        Rank insights by relevance and confidence.
        
        Args:
            insights: List of DiscoveryInsight objects
        
        Returns:
            Sorted list of insights (highest ranked first)
        """
        # Sort by combined relevance and confidence score
        ranked = sorted(
            insights,
            key=lambda x: (x.relevance_score * 0.6 + x.confidence * 0.4),
            reverse=True
        )
        
        logger.info(f"Ranked {len(insights)} insights")
        
        return ranked
    
    def generate_summary(self, insights: List[DiscoveryInsight], 
                        max_insights: int = 5) -> str:
        """
        Generate a summary of top insights.
        
        Args:
            insights: List of DiscoveryInsight objects
            max_insights: Maximum number of insights to include in summary
        
        Returns:
            Formatted summary string
        """
        if not insights:
            return "No insights available at this time."
        
        # Take top insights
        top_insights = insights[:max_insights]
        
        # Build summary
        summary_parts = []
        for i, insight in enumerate(top_insights, 1):
            summary_parts.append(f"{i}. {insight.summary}")
        
        summary = "\n\n".join(summary_parts)
        
        logger.info(f"Generated summary with {len(top_insights)} insights")
        
        return summary
    
    def analyze_collection(self, articles: List[InvestmentArticle],
                          user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a collection of articles and return structured JSON output.
        
        Args:
            articles: List of InvestmentArticle objects to analyze
            user_context: Optional user profile context for personalization
        
        Returns:
            Dictionary with structured analysis results
        """
        logger.info(f"Analyzing collection of {len(articles)} articles")
        
        if not articles:
            return {
                "top_opportunities": [],
                "market_summary": "No articles available for analysis.",
                "important_policy_updates": [],
                "investment_recommendations": [],
                "risks": [],
                "confidence_score": 0.0
            }
        
        # Prepare articles summary for the prompt
        articles_summary = []
        for i, article in enumerate(articles[:20], 1):  # Limit to 20 articles
            articles_summary.append(
                f"{i}. [{article.category}] {article.title}\n"
                f"   Source: {article.source}\n"
                f"   Published: {article.published_at.strftime('%Y-%m-%d')}\n"
                f"   Content: {article.content[:500]}...\n"
            )
        
        articles_text = "\n".join(articles_summary)
        
        # Create prompt for OpenRouter
        prompt = f"""Analyze the following {len(articles[:20])} investment-related articles and provide a comprehensive analysis in JSON format.

Articles:
{articles_text}

Provide analysis in the following JSON structure:
{{
    "top_opportunities": [
        {{
            "title": "Opportunity title",
            "description": "Brief description of the opportunity",
            "category": "category name",
            "relevance_score": 0.0-1.0,
            "source": "source name"
        }}
    ],
    "market_summary": "2-3 sentence summary of current market trends based on the articles",
    "important_policy_updates": [
        {{
            "policy": "Policy name or title",
            "impact": "Description of impact on investors",
            "source": "source name"
        }}
    ],
    "investment_recommendations": [
        {{
            "recommendation": "Specific actionable recommendation",
            "reasoning": "Why this recommendation makes sense",
            "risk_level": "Low/Medium/High"
        }}
    ],
    "risks": [
        {{
            "risk": "Risk description",
            "severity": "Low/Medium/High",
            "mitigation": "How to mitigate this risk"
        }}
    ],
    "confidence_score": 0.0-1.0
}}

Return ONLY valid JSON. Do not include any text before or after the JSON."""
        
        # Call OpenRouter
        response = self._call_openrouter(prompt, max_tokens=2000)
        
        if not response:
            logger.warning("OpenRouter call failed, returning default analysis")
            return {
                "top_opportunities": [],
                "market_summary": "Unable to generate market summary at this time.",
                "important_policy_updates": [],
                "investment_recommendations": [],
                "risks": [],
                "confidence_score": 0.0
            }
        
        # Parse JSON response
        analysis = self._parse_json_response(response)
        
        if not analysis:
            logger.warning("Failed to parse OpenRouter response")
            return {
                "top_opportunities": [],
                "market_summary": "Unable to parse analysis results.",
                "important_policy_updates": [],
                "investment_recommendations": [],
                "risks": [],
                "confidence_score": 0.0
            }
        
        logger.info(f"Analysis complete: {len(analysis.get('top_opportunities', []))} opportunities found")
        
        return analysis
    
    def get_insights_by_category(self, insights: List[DiscoveryInsight],
                                 category: str) -> List[DiscoveryInsight]:
        """
        Filter insights by category.
        
        Args:
            insights: List of DiscoveryInsight objects
            category: Category to filter by
        
        Returns:
            Filtered list of insights
        """
        # Note: This is a placeholder - actual implementation would need
        # category information stored in insights or linked to articles
        filtered = [insight for insight in insights if category.lower() in insight.summary.lower()]
        
        logger.info(f"Filtered {len(insights)} insights to {len(filtered)} for category '{category}'")
        
        return filtered
    
    def get_top_recommendations(self, insights: List[DiscoveryInsight],
                               count: int = 3) -> List[Dict[str, Any]]:
        """
        Get top N recommendations from insights.
        
        Args:
            insights: List of DiscoveryInsight objects
            count: Number of top recommendations to return
        
        Returns:
            List of recommendation dictionaries
        """
        # Sort by relevance score
        sorted_insights = sorted(insights, key=lambda x: x.relevance_score, reverse=True)
        
        # Take top N
        top_insights = sorted_insights[:count]
        
        # Convert to dictionaries
        recommendations = []
        for insight in top_insights:
            recommendations.append({
                "summary": insight.summary,
                "recommendation": insight.recommendation,
                "reason": insight.reason,
                "relevance_score": insight.relevance_score,
                "confidence": insight.confidence,
                "source": insight.source
            })
        
        logger.info(f"Extracted top {len(recommendations)} recommendations")
        
        return recommendations


# Global analyzer instance
analyzer = InsightAnalyzer()