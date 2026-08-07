"""
Investment Comparison Page

Allows users to compare investment options across key metrics:
- Expected Return
- Risk
- Liquidity
- Lock-in
- Tax Benefits
- Expense Ratio
- Minimum Investment

Uses available AI data from the discovery engine and demo dataset.
"""

import streamlit as st
import pandas as pd
from config.theme import apply_theme
from database import db
from services.discovery import (
    InsightAnalyzer,
    PersonalizationEngine,
    ContentCleaner,
    collect_all_articles,
    load_fallback_articles,
)

apply_theme()


# ---------------------------------------------------------------------------
# Static comparison data derived from available AI/discovery data
# ---------------------------------------------------------------------------

INVESTMENT_PROFILES = [
    {
        "name": "Index Funds (Nifty 50)",
        "icon": "📈",
        "category": "equity",
        "expected_return": "10-14%",
        "risk": "Medium",
        "risk_score": 2,
        "liquidity": "High",
        "liquidity_score": 3,
        "lock_in": "None (recommend 7+ yrs)",
        "tax_benefits": "LTCG > ₹1L @ 10%",
        "expense_ratio": "0.05-0.5%",
        "min_investment": "₹500 (SIP)",
        "description": "Track market indices like Nifty 50 at low cost. Outperform most actively managed funds over the long term.",
        "source": "AI Discovery",
    },
    {
        "name": "ELSS (Tax Saving Equity)",
        "icon": "🧾",
        "category": "tax",
        "expected_return": "12-15%",
        "risk": "Medium",
        "risk_score": 2,
        "liquidity": "Medium",
        "liquidity_score": 2,
        "lock_in": "3 years (shortest 80C)",
        "tax_benefits": "Deduction u/s 80C (₹1.5L)",
        "expense_ratio": "0.5-1.5%",
        "min_investment": "₹500 (SIP)",
        "description": "Combines tax saving with equity returns. Best tax-saving instrument for long-term wealth creation.",
        "source": "AI Discovery",
    },
    {
        "name": "PPF (Public Provident Fund)",
        "icon": "🏦",
        "category": "retirement",
        "expected_return": "7.1% (Guaranteed)",
        "risk": "Low",
        "risk_score": 1,
        "liquidity": "Low",
        "liquidity_score": 1,
        "lock_in": "15 years (partial from yr 7)",
        "tax_benefits": "EEE (Exempt-Exempt-Exempt)",
        "expense_ratio": "0%",
        "min_investment": "₹500/year",
        "description": "Guaranteed returns with EEE tax benefits. Ideal for conservative investors building risk-free corpus.",
        "source": "AI Discovery",
    },
    {
        "name": "NPS (National Pension System)",
        "icon": "🏖️",
        "category": "retirement",
        "expected_return": "9-12%",
        "risk": "Medium",
        "risk_score": 2,
        "liquidity": "Very Low",
        "liquidity_score": 0,
        "lock_in": "Till retirement (60 yrs)",
        "tax_benefits": "80C (₹1.5L) + 80CCD(1B) (₹50K)",
        "expense_ratio": "0.01-0.09%",
        "min_investment": "₹1,000/year",
        "description": "Market-linked retirement corpus with additional tax deduction. Higher potential returns than PPF.",
        "source": "AI Discovery",
    },
    {
        "name": "Debt Funds (Short-term)",
        "icon": "💼",
        "category": "debt",
        "expected_return": "7-9%",
        "risk": "Low",
        "risk_score": 1,
        "liquidity": "High",
        "liquidity_score": 3,
        "lock_in": "None (exit load < 6-12 mo)",
        "tax_benefits": "Indexation after 3 yrs",
        "expense_ratio": "0.2-1.0%",
        "min_investment": "₹1,000",
        "description": "Fixed-income securities with lower volatility than equity. Better tax efficiency than FDs beyond 3 years.",
        "source": "AI Discovery",
    },
    {
        "name": "Gold ETF / SGB",
        "icon": "🥇",
        "category": "gold",
        "expected_return": "8-12% (incl. interest)",
        "risk": "Low",
        "risk_score": 1,
        "liquidity": "High (ETF) / Low (SGB)",
        "liquidity_score": 2,
        "lock_in": "SGB: 8 yrs (exit from yr 5)",
        "tax_benefits": "SGB: No capital gains tax",
        "expense_ratio": "0.5-1.0% (ETF)",
        "min_investment": "₹1,000 (ETF)",
        "description": "Gold allocation (5-10%) protects against inflation and provides portfolio stability during market downturns.",
        "source": "AI Discovery",
    },
    {
        "name": "Emergency Fund (Liquid Fund)",
        "icon": "🛡️",
        "category": "emergency_fund",
        "expected_return": "4-6%",
        "risk": "Low",
        "risk_score": 1,
        "liquidity": "Very High",
        "liquidity_score": 3,
        "lock_in": "None",
        "tax_benefits": "Indexation after 3 yrs",
        "expense_ratio": "0.1-0.3%",
        "min_investment": "₹500",
        "description": "6-12 months of expenses for unexpected situations. Foundation of financial security.",
        "source": "AI Discovery",
    },
    {
        "name": "Fixed Deposits (FD)",
        "icon": "🏛️",
        "category": "debt",
        "expected_return": "6-7.5%",
        "risk": "Low",
        "risk_score": 1,
        "liquidity": "Medium",
        "liquidity_score": 2,
        "lock_in": "1-5 years (premature penalty)",
        "tax_benefits": "80C (5-yr FD only)",
        "expense_ratio": "0%",
        "min_investment": "₹1,000",
        "description": "Guaranteed returns with bank safety. Less tax-efficient than debt funds for long-term investors.",
        "source": "AI Discovery",
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_risk_color(risk: str) -> str:
    """Get color for risk level"""
    risk_lower = risk.lower()
    if "low" in risk_lower:
        return "#22C55E"
    elif "medium" in risk_lower:
        return "#F59E0B"
    else:
        return "#EF4444"


def _get_liquidity_color(liquidity: str) -> str:
    """Get color for liquidity level"""
    liquidity_lower = liquidity.lower()
    if "very high" in liquidity_lower:
        return "#22C55E"
    elif "high" in liquidity_lower:
        return "#60A5FA"
    elif "medium" in liquidity_lower:
        return "#F59E0B"
    else:
        return "#EF4444"


def _get_tax_color(tax_benefits: str) -> str:
    """Get color for tax benefits"""
    tax_lower = tax_benefits.lower()
    if "eee" in tax_lower or "exempt" in tax_lower:
        return "#22C55E"
    elif "80c" in tax_lower or "deduction" in tax_lower:
        return "#60A5FA"
    else:
        return "#9CA3AF"


def _get_category_icon(category: str) -> str:
    """Get icon for investment category"""
    category_lower = category.lower()
    
    if 'index' in category_lower or 'equity' in category_lower:
        return "📈"
    elif 'debt' in category_lower or 'fixed' in category_lower:
        return "🏦"
    elif 'gold' in category_lower:
        return "🥇"
    elif 'sip' in category_lower or 'mutual' in category_lower:
        return "💼"
    elif 'tax' in category_lower:
        return "🧾"
    elif 'emergency' in category_lower or 'liquid' in category_lower:
        return "🛡️"
    elif 'retirement' in category_lower or 'ppf' in category_lower or 'nps' in category_lower:
        return "🏖️"
    else:
        return "💎"


def _get_ai_insights(profile):
    """
    Get AI insights from the discovery engine.
    Returns a dict with analysis data or None if unavailable.
    """
    try:
        # Collect articles using orchestration layer
        all_articles = collect_all_articles()
        
        # If no articles collected, load fallback dataset
        if not all_articles:
            all_articles = load_fallback_articles()
        
        # Clean articles
        cleaner = ContentCleaner()
        cleaned_articles = cleaner.process_batch(all_articles)
        
        if not cleaned_articles:
            return None
        
        # Analyze articles
        analyzer = InsightAnalyzer()
        analysis = analyzer.analyze_collection(cleaned_articles)
        
        # Personalize for user if profile exists
        if profile:
            user_profile_dict = {
                'salary': profile.salary,
                'expenses': profile.expenses,
                'age': profile.age,
                'risk': profile.risk,
                'goal': profile.goal,
                'monthly_investment': profile.salary - profile.expenses
            }
            
            personalizer = PersonalizationEngine()
            analysis = personalizer.get_personalized_analysis(
                analysis,
                user_profile_dict,
                top_n=5
            )
        
        return analysis
    except Exception:
        return None


def _render_comparison_table(profiles):
    """
    Render the main comparison table using native Streamlit.
    """
    # Prepare data for dataframe
    table_data = []
    for profile in profiles:
        table_data.append({
            "Investment": f"{profile['icon']} {profile['name']}",
            "Expected Return": profile['expected_return'],
            "Risk": profile['risk'],
            "Liquidity": profile['liquidity'],
            "Lock-in": profile['lock_in'],
            "Tax Benefits": profile['tax_benefits'],
            "Expense Ratio": profile['expense_ratio'],
            "Min Investment": profile['min_investment']
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, width="stretch", hide_index=True)


def _render_detail_cards(profiles):
    """
    Render detailed comparison cards for each investment using native Streamlit.
    """
    for idx, profile in enumerate(profiles):
        with st.container():
            st.markdown(f"### {profile['icon']} {profile['name']}")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**Category:** {profile['category'].replace('_', ' ').title()}")
                st.markdown(f"**Source:** {profile['source']}")
            with col2:
                st.metric("Expected Return", profile['expected_return'])
            with col3:
                st.metric("Expense Ratio", profile['expense_ratio'])
            
            st.markdown(f"**Description:** {profile['description']}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                risk_color = _get_risk_color(profile['risk'])
                st.markdown(f"**Risk:** :{risk_color[1:]}[{profile['risk']}]")
            with col2:
                liquidity_color = _get_liquidity_color(profile['liquidity'])
                st.markdown(f"**Liquidity:** :{liquidity_color[1:]}[{profile['liquidity']}]")
            with col3:
                st.markdown(f"**Lock-in:** {profile['lock_in']}")
            with col4:
                tax_color = _get_tax_color(profile['tax_benefits'])
                st.markdown(f"**Tax Benefits:** :{tax_color[1:]}[{profile['tax_benefits']}]")
            
            st.markdown(f"**Minimum Investment:** {profile['min_investment']}")
            st.divider()


def _render_ai_insights(analysis):
    """
    Render AI insights from the discovery engine using native Streamlit.
    """
    if not analysis:
        return
    
    opportunities = analysis.get('top_opportunities', [])
    market_summary = analysis.get('market_summary', '')
    recommendations = analysis.get('investment_recommendations', [])
    risks = analysis.get('risks', [])
    
    if not opportunities and not market_summary:
        return
    
    st.markdown("### 🤖 AI Insights")
    st.markdown("Generated from available AI discovery data")
    
    # Market summary
    if market_summary and "Unable to" not in market_summary:
        st.info(f"📊 **Market Summary:** {market_summary}")
    
    # AI recommendations
    if recommendations:
        st.markdown("#### 💡 AI Recommendations")
        for idx, rec in enumerate(recommendations[:3], 1):
            risk_level = rec.get('risk_level', 'Medium')
            risk_color = _get_risk_color(risk_level)
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{rec.get('recommendation', '')}**")
                    st.caption(rec.get('reasoning', ''))
                with col2:
                    st.markdown(f":{risk_color[1:]}[{risk_level}]")
    
    # Risks
    if risks:
        st.markdown("#### ⚠️ Key Risks")
        for risk in risks[:3]:
            severity = risk.get('severity', 'Medium')
            severity_color = _get_risk_color(severity)
            
            with st.container():
                st.markdown(f"**{risk.get('risk', '')}**")
                st.caption(f":{severity_color[1:]}[Severity: {severity}] {risk.get('mitigation', '')}")


def show():
    """Display investment comparison page"""
    st.title("⚖️ Investment Comparison")
    st.caption("Compare investment options across key metrics")

    # Get user profile for personalization
    profile = db.get_latest_profile()

    # Initialize session state for AI insights
    if "comparison_ai_data" not in st.session_state:
        st.session_state.comparison_ai_data = None
    if "comparison_loading" not in st.session_state:
        st.session_state.comparison_loading = False

    # Refresh button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh AI Insights", width="stretch", type="primary"):
            st.session_state.comparison_ai_data = None
            st.session_state.comparison_loading = True
            st.rerun()

    # Load AI insights if not already loaded
    if st.session_state.comparison_loading or st.session_state.comparison_ai_data is None:
        with st.spinner("🤖 Analyzing investment data..."):
            analysis = _get_ai_insights(profile)
            st.session_state.comparison_ai_data = analysis
            st.session_state.comparison_loading = False

    # ------------------------------------------------------------------
    # 1. Comparison Table
    # ------------------------------------------------------------------
    st.markdown("### 📋 Comparison Table")
    st.caption("Side-by-side comparison of all key investment metrics")

    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.multiselect(
            "Filter by Risk",
            ["Low", "Medium", "High"],
            default=["Low", "Medium", "High"]
        )
    with col2:
        liquidity_filter = st.multiselect(
            "Filter by Liquidity",
            ["Very High", "High", "Medium", "Low", "Very Low"],
            default=["Very High", "High", "Medium", "Low", "Very Low"]
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Name", "Expected Return", "Risk (Low → High)", "Liquidity (High → Low)"]
        )

    # Filter profiles
    filtered_profiles = [
        p for p in INVESTMENT_PROFILES
        if p["risk"] in risk_filter and p["liquidity"] in liquidity_filter
    ]

    # Sort profiles
    if sort_by == "Name":
        filtered_profiles.sort(key=lambda x: x["name"])
    elif sort_by == "Expected Return":
        filtered_profiles.sort(key=lambda x: x["expected_return"], reverse=True)
    elif sort_by == "Risk (Low → High)":
        filtered_profiles.sort(key=lambda x: x["risk_score"])
    elif sort_by == "Liquidity (High → Low)":
        filtered_profiles.sort(key=lambda x: x["liquidity_score"], reverse=True)

    if not filtered_profiles:
        st.warning("⚠️ No investments match your filters. Try adjusting the filter criteria.")
    else:
        _render_comparison_table(filtered_profiles)

    # ------------------------------------------------------------------
    # 2. AI Insights
    # ------------------------------------------------------------------
    if st.session_state.comparison_ai_data:
        _render_ai_insights(st.session_state.comparison_ai_data)

    # ------------------------------------------------------------------
    # 3. Detailed Comparison Cards
    # ------------------------------------------------------------------
    st.markdown("### 🔍 Detailed Comparison")
    st.caption("In-depth view of each investment option")

    _render_detail_cards(filtered_profiles)

    # ------------------------------------------------------------------
    # 4. Quick Reference Guide
    # ------------------------------------------------------------------
    st.markdown("### 📖 Quick Reference Guide")
    st.caption("Understanding the comparison metrics")

    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown("#### 📊 Key Metrics Explained")
            st.markdown(f"""
            - **Expected Return:** Annual return range based on historical data
            - **Risk:** Volatility and probability of loss
            - **Liquidity:** How quickly you can access your money
            - **Lock-in:** Minimum holding period required
            - **Tax Benefits:** Tax deductions or exemptions available
            - **Expense Ratio:** Annual fee charged by the fund
            - **Min Investment:** Minimum amount to start investing
            """)

    with col2:
        with st.container():
            st.markdown("#### 🎯 How to Choose")
            st.markdown(f"""
            - **Low Risk:** PPF, FD, Debt Funds, Emergency Fund
            - **Medium Risk:** Index Funds, ELSS, NPS, Gold
            - **High Risk:** Direct Stocks, Small-cap Funds
            
            💡 **Tip:** Diversify across risk levels. Start with an emergency fund, then build a balanced portfolio of index funds, debt funds, and tax-saving instruments.
            """)

    # Disclaimer
    st.divider()
    st.caption("⚠️ **Disclaimer:** This comparison is based on AI-generated analysis from available data sources. "
               "This is not financial advice. Always conduct your own research or consult a qualified financial advisor "
               "before making investment decisions.")


if __name__ == '__main__':
    show()