"""
Personalization engine for investment opportunities.

Ranks and personalizes investment opportunities based on user profile
and AI-generated discovery insights.
"""

from typing import List, Dict, Any, Optional
import logging

from .models import InvestmentArticle, DiscoveryInsight
from .config import config

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Personalizes investment opportunities based on user profile.
    
    Ranks opportunities by relevance to user's financial profile and
    generates explanations for why each opportunity matches.
    """
    
    def __init__(self):
        """Initialize the personalization engine."""
        self.config = config
    
    def calculate_relevance_score(self, opportunity: Dict[str, Any], 
                                  user_profile: Dict[str, Any]) -> float:
        """
        Calculate relevance score for an opportunity based on user profile.
        
        Args:
            opportunity: Opportunity dictionary with category, risk_level, etc.
            user_profile: User profile with salary, age, risk, goal, etc.
        
        Returns:
            Relevance score between 0 and 100
        """
        score = 50.0  # Base score
        
        # Extract user profile data
        user_risk = user_profile.get('risk', 'Medium').lower()
        user_goal = user_profile.get('goal', '').lower()
        user_age = user_profile.get('age', 30)
        monthly_investment = user_profile.get('monthly_investment', 0)
        
        # Extract opportunity data
        opp_category = opportunity.get('category', '').lower()
        opp_risk = opportunity.get('risk_level', 'Medium').lower()
        opp_min_investment = opportunity.get('min_investment', 0)
        
        # Risk alignment (max +20 points)
        if user_risk == opp_risk:
            score += 20
        elif (user_risk == 'low' and opp_risk in ['low', 'medium']) or \
             (user_risk == 'high' and opp_risk in ['medium', 'high']) or \
             (user_risk == 'medium' and opp_risk == 'medium'):
            score += 10
        
        # Goal alignment (max +20 points)
        goal_keywords = {
            'emergency fund': ['emergency fund', 'liquid fund', 'savings'],
            'retirement': ['ppf', 'nps', 'pension', 'retirement'],
            'wealth creation': ['index funds', 'equity', 'mutual fund', 'sip'],
            'buy house': ['debt', 'fixed deposit', 'bond', 'fd'],
            'travel': ['liquid', 'short-term', 'high liquidity']
        }
        
        for goal, keywords in goal_keywords.items():
            if goal in user_goal:
                for keyword in keywords:
                    if keyword in opp_category:
                        score += 20
                        break
                break
        
        # Affordability (max +10 points)
        if monthly_investment > 0 and opp_min_investment > 0:
            if monthly_investment >= opp_min_investment:
                score += 10
            elif monthly_investment >= opp_min_investment * 0.5:
                score += 5
        
        # Age-based adjustments (max +10 points)
        if user_age < 30:
            # Young investors can take more risks
            if opp_risk in ['high', 'medium']:
                score += 10
        elif user_age < 40:
            # Mid-career professionals
            if opp_risk in ['medium', 'low']:
                score += 10
        else:
            # Older investors should be conservative
            if opp_risk == 'low':
                score += 10
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        return score
    
    def generate_personalization_reason(self, opportunity: Dict[str, Any], 
                                        user_profile: Dict[str, Any],
                                        relevance_score: float) -> str:
        """
        Generate explanation for why opportunity matches user profile.
        
        Args:
            opportunity: Opportunity dictionary
            user_profile: User profile dictionary
            relevance_score: Calculated relevance score
        
        Returns:
            Explanation string
        """
        reasons = []
        
        user_risk = user_profile.get('risk', 'Medium')
        user_goal = user_profile.get('goal', '')
        user_age = user_profile.get('age', 30)
        monthly_investment = user_profile.get('monthly_investment', 0)
        
        opp_category = opportunity.get('category', '')
        opp_risk = opportunity.get('risk_level', 'Medium')
        opp_min_investment = opportunity.get('min_investment', 0)
        
        # Risk alignment reason
        if user_risk.lower() == opp_risk.lower():
            reasons.append(f"matches your {user_risk.lower()} risk appetite")
        elif user_risk.lower() == 'low' and opp_risk.lower() in ['low', 'medium']:
            reasons.append(f"aligns with your conservative risk profile")
        elif user_risk.lower() == 'high' and opp_risk.lower() in ['medium', 'high']:
            reasons.append(f"suits your aggressive investment style")
        
        # Goal alignment reason
        goal_keywords = {
            'emergency fund': ['emergency', 'liquid', 'safety'],
            'retirement': ['retirement', 'long-term', 'tax-saving'],
            'wealth creation': ['growth', 'wealth', 'appreciation'],
            'buy house': ['stable', 'secure', 'guaranteed'],
            'travel': ['liquid', 'flexible', 'short-term']
        }
        
        for goal, keywords in goal_keywords.items():
            if goal in user_goal.lower():
                for keyword in keywords:
                    if keyword in opp_category.lower():
                        reasons.append(f"supports your {goal} goal")
                        break
                break
        
        # Affordability reason
        if monthly_investment > 0 and opp_min_investment > 0:
            if monthly_investment >= opp_min_investment:
                reasons.append(f"affordable with your monthly investment capacity of ₹{monthly_investment:,.0f}")
            elif monthly_investment >= opp_min_investment * 0.5:
                reasons.append(f"within reach with your current savings")
        
        # Age-based reason
        if user_age < 30:
            reasons.append("ideal for young investors with long time horizon")
        elif user_age < 40:
            reasons.append("suitable for your life stage")
        else:
            reasons.append("appropriate for your conservative approach at this life stage")
        
        # Combine reasons
        if reasons:
            return "This opportunity " + ", ".join(reasons[:3]) + "."
        else:
            return f"This opportunity has a relevance score of {relevance_score:.0f}/100 based on your profile."
    
    def personalize_opportunities(self, 
                                  opportunities: List[Dict[str, Any]],
                                  user_profile: Dict[str, Any],
                                  top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Rank and personalize opportunities for a user.
        
        Args:
            opportunities: List of opportunity dictionaries
            user_profile: User profile dictionary
            top_n: Number of top opportunities to return
        
        Returns:
            List of top N personalized opportunities with scores and reasons
        """
        if not opportunities:
            logger.warning("No opportunities to personalize")
            return []
        
        logger.info(f"Personalizing {len(opportunities)} opportunities for user")
        
        # Calculate relevance score for each opportunity
        scored_opportunities = []
        for opp in opportunities:
            try:
                relevance_score = self.calculate_relevance_score(opp, user_profile)
                reason = self.generate_personalization_reason(opp, user_profile, relevance_score)
                
                # Create personalized opportunity
                personalized_opp = {
                    **opp,  # Include all original opportunity data
                    'relevance_score': relevance_score,
                    'personalization_reason': reason
                }
                
                scored_opportunities.append(personalized_opp)
                
            except Exception as e:
                logger.error(f"Error personalizing opportunity '{opp.get('title', 'Unknown')}': {e}")
                continue
        
        # Sort by relevance score (descending)
        scored_opportunities.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top N
        top_opportunities = scored_opportunities[:top_n]
        
        logger.info(f"Returning top {len(top_opportunities)} personalized opportunities")
        
        return top_opportunities
    
    def personalize_insights(self, 
                            insights: List[DiscoveryInsight],
                            user_profile: Dict[str, Any],
                            top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Rank and personalize insights for a user.
        
        Args:
            insights: List of DiscoveryInsight objects
            user_profile: User profile dictionary
            top_n: Number of top insights to return
        
        Returns:
            List of top N personalized insights with scores and reasons
        """
        if not insights:
            logger.warning("No insights to personalize")
            return []
        
        logger.info(f"Personalizing {len(insights)} insights for user")
        
        # Convert insights to dictionaries
        opportunities = []
        for insight in insights:
            opp = {
                'title': insight.summary,
                'description': insight.recommendation,
                'category': insight.reason.replace('Category: ', ''),
                'source': insight.source,
                'risk_level': 'Medium',  # Default, can be enhanced
                'min_investment': 0  # Default, can be enhanced
            }
            opportunities.append(opp)
        
        # Personalize using the same method
        return self.personalize_opportunities(opportunities, user_profile, top_n)
    
    def get_personalized_analysis(self, 
                                  analysis: Dict[str, Any],
                                  user_profile: Dict[str, Any],
                                  top_n: int = 5) -> Dict[str, Any]:
        """
        Personalize the complete analysis from InsightAnalyzer.
        
        Args:
            analysis: Analysis dictionary from InsightAnalyzer.analyze_collection()
            user_profile: User profile dictionary
            top_n: Number of top opportunities to return
        
        Returns:
            Personalized analysis dictionary
        """
        logger.info("Personalizing complete analysis")
        
        # Extract opportunities from analysis
        opportunities = analysis.get('top_opportunities', [])
        
        # Personalize opportunities
        personalized_opportunities = self.personalize_opportunities(
            opportunities, 
            user_profile, 
            top_n
        )
        
        # Create personalized analysis
        personalized_analysis = {
            'top_opportunities': personalized_opportunities,
            'market_summary': analysis.get('market_summary', ''),
            'important_policy_updates': analysis.get('important_policy_updates', []),
            'investment_recommendations': analysis.get('investment_recommendations', []),
            'risks': analysis.get('risks', []),
            'confidence_score': analysis.get('confidence_score', 0.0),
            'user_profile': user_profile
        }
        
        logger.info(f"Personalized analysis complete with {len(personalized_opportunities)} opportunities")
        
        return personalized_analysis


# Global personalization engine instance
personalization_engine = PersonalizationEngine()