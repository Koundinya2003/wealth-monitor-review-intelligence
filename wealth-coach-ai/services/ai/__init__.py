import os
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class AIService:
    """AI Service wrapper for Wealth Coach AI"""
    
    @staticmethod
    def generate_summary(profile, metrics: dict) -> str:
        """Generate AI-powered financial recommendation"""
        api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        
        # Get model from environment, default to DeepSeek free model
        model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3-0324:free')
        
        # Build comprehensive prompt
        prompt = (
            f"User Profile:\n"
            f"- Monthly Salary: ₹{profile.salary:,.0f}\n"
            f"- Monthly Expenses: ₹{profile.expenses:,.0f}\n"
            f"- Age: {profile.age}\n"
            f"- Financial Goal: {profile.goal}\n"
            f"- Risk Appetite: {profile.risk}\n\n"
            f"Financial Metrics:\n"
            f"- Money Available: ₹{metrics.get('money_available', 0):,.0f}\n"
            f"- Savings Rate: {metrics.get('savings_percent', 0):.1f}%\n"
            f"- Emergency Fund Target: ₹{metrics.get('emergency_fund_target', 0):,.0f}\n"
            f"- Suggested Monthly Investment: ₹{metrics.get('suggested_investment', 0):,.0f}\n\n"
            "Provide a comprehensive financial recommendation with the following sections:\n\n"
            "1. Executive Summary (1-2 sentences)\n"
            "2. Investment Recommendation (specific actionable advice)\n"
            "3. Risk Analysis (explain risks based on their profile)\n"
            "4. Suggested Allocation (breakdown of where money should go)\n"
            "5. Things To Improve (2-3 specific areas)\n"
            "6. Expected Long-Term Outcome (what they can expect in 5-10 years)\n\n"
            "Keep it simple, encouraging, and actionable for someone with zero financial knowledge. "
            "Use ₹ for all amounts. Format with clear section headers."
        )

        # Try OpenRouter API if key is available
        if api_key:
            try:
                url = "https://api.openrouter.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                body = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500,
                }
                response = requests.post(url, headers=headers, json=body, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                choices = data.get('choices', [])
                if choices and len(choices) > 0:
                    content = choices[0].get('message', {}).get('content')
                    if content:
                        return content.strip()
            except requests.exceptions.ConnectionError:
                logger.warning("OpenRouter unavailable: connection error")
            except requests.exceptions.Timeout:
                logger.warning("OpenRouter unavailable: timeout")
            except requests.exceptions.RequestException as e:
                logger.warning(f"OpenRouter unavailable: {str(e)}")
            except Exception:
                # Fall through to default response
                pass

        # Fallback recommendation based on metrics
        savings_percent = metrics.get('savings_percent', 0)
        money_available = metrics.get('money_available', 0)
        suggested = metrics.get('suggested_investment', 0)
        emergency_target = metrics.get('emergency_fund_target', 0)
        
        recommendation = f"""**Executive Summary**
You're saving {savings_percent:.1f}% of your income (₹{money_available:,.0f} monthly). 
Focus on building an emergency fund first, then invest ₹{suggested:,.0f} monthly towards your {profile.goal.lower()} goal.

**Investment Recommendation**
Start with a ₹{emergency_target:,.0f} emergency fund (6 months of expenses) in a liquid fund or high-yield savings account. 
Once that's in place, invest ₹{suggested:,.0f} monthly through a diversified portfolio of low-cost index funds. 
Set up an automated SIP to ensure consistency.

**Risk Analysis**
With {profile.risk.lower()} risk appetite, you should maintain a balanced portfolio. 
Avoid high-risk investments until you have a solid emergency fund. 
Diversification is key to managing risk while achieving your goals.

**Suggested Allocation**
- Emergency Fund: 20% (₹{money_available * 0.2:,.0f})
- Index Funds/ETFs: 50% (₹{money_available * 0.5:,.0f})
- Debt Funds: 20% (₹{money_available * 0.2:,.0f})
- Gold/Alternatives: 10% (₹{money_available * 0.1:,.0f})

**Things To Improve**
1. Track expenses for 30 days to identify areas to cut back
2. Increase savings rate to 30% by reducing discretionary spending
3. Review and rebalance your portfolio quarterly

**Expected Long-Term Outcome**
If you invest ₹{suggested:,.0f} monthly at 12% annual returns for 10 years, you could build a corpus of ₹{suggested * 12 * 12 * 3.1:,.0f}. 
This will significantly help you achieve your {profile.goal.lower()} goal and build long-term wealth.
"""
        
        return recommendation


# Create singleton instance
ai = AIService()