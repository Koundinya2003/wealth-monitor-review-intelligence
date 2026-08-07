"""
Investment Discovery Page

Displays AI-analyzed investment opportunities, market insights,
and personalized recommendations from the Discovery Engine.

Redesigned with beginner-friendly visualizations using native Streamlit components.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
# Static investment data for demo/fallback scenarios
# ---------------------------------------------------------------------------

DEMO_INVESTMENTS = [
    {
        "name": "Emergency Fund (Liquid Fund)",
        "icon": "🛡️",
        "category": "Emergency Fund",
        "expected_return": "4-6%",
        "risk": "Low",
        "liquidity": "Very High",
        "lock_in": "None",
        "tax_benefits": "Indexation after 3 yrs",
        "min_investment": "₹500",
        "why": "Build your safety net before investing. Covers 6 months of expenses for unexpected situations.",
        "pros": ["Instant access to funds", "Preserves capital", "Prevents breaking long-term investments"],
        "cons": ["Lower returns than equity", "Returns may barely beat inflation"],
    },
    {
        "name": "Index Fund SIP (Nifty 50)",
        "icon": "📈",
        "category": "Index Fund",
        "expected_return": "10-14%",
        "risk": "Medium",
        "liquidity": "High",
        "lock_in": "None (7+ yrs recommended)",
        "tax_benefits": "LTCG > ₹1L @ 10%",
        "min_investment": "₹500/month",
        "why": "Low-cost diversified equity exposure. Historically outperforms most actively managed funds.",
        "pros": ["Lowest expense ratios (0.05-0.5%)", "Diversified exposure", "No fund-manager risk"],
        "cons": ["No protection during downturns", "Returns capped at index"],
    },
    {
        "name": "ELSS (Tax Saving Equity)",
        "icon": "🧾",
        "category": "Tax Saving",
        "expected_return": "12-15%",
        "risk": "Medium",
        "liquidity": "Medium",
        "lock_in": "3 years",
        "tax_benefits": "80C deduction (₹1.5L)",
        "min_investment": "₹500/month",
        "why": "Best tax-saving instrument with equity returns. Shortest lock-in among 80C options.",
        "pros": ["Tax deduction under 80C", "Equity returns (12-15%)", "3-year lock-in"],
        "cons": ["Market-linked returns", "Lock-in period"],
    },
    {
        "name": "PPF (Public Provident Fund)",
        "icon": "🏦",
        "category": "Tax Saving",
        "expected_return": "7.1% (Guaranteed)",
        "risk": "Low",
        "liquidity": "Low",
        "lock_in": "15 years",
        "tax_benefits": "EEE (Exempt-Exempt-Exempt)",
        "min_investment": "₹500/year",
        "why": "Guaranteed risk-free returns with triple tax benefits. Essential for conservative investors.",
        "pros": ["Guaranteed 7.1% returns", "EEE tax benefits", "Government-backed"],
        "cons": ["15-year lock-in", "Returns capped at government rate"],
    },
    {
        "name": "Debt Fund (Short-term)",
        "icon": "💼",
        "category": "Debt Fund",
        "expected_return": "7-9%",
        "risk": "Low",
        "liquidity": "High",
        "lock_in": "None (exit load < 6-12 mo)",
        "tax_benefits": "Indexation after 3 yrs",
        "min_investment": "₹1,000",
        "why": "Stable returns with better tax efficiency than FDs. Ideal for medium-term goals.",
        "pros": ["Better than FD returns", "Indexation benefits", "Lower volatility"],
        "cons": ["Credit risk", "Exit loads", "Returns not guaranteed"],
    },
    {
        "name": "NPS (National Pension System)",
        "icon": "🏖️",
        "category": "Retirement",
        "expected_return": "9-12%",
        "risk": "Medium",
        "liquidity": "Very Low",
        "lock_in": "Till retirement (60 yrs)",
        "tax_benefits": "80C + 80CCD(1B) (₹50K extra)",
        "min_investment": "₹1,000/year",
        "why": "Retirement corpus with additional tax benefits. Low expense ratios and market-linked growth.",
        "pros": ["Additional ₹50K deduction", "Low expense ratios", "9-12% returns"],
        "cons": ["Locked till retirement", "Mandatory annuity purchase"],
    },
    {
        "name": "Gold ETF / SGB",
        "icon": "🥇",
        "category": "Gold",
        "expected_return": "8-12% (incl. interest)",
        "risk": "Low",
        "liquidity": "High (ETF) / Low (SGB)",
        "lock_in": "SGB: 8 years",
        "tax_benefits": "SGB: No capital gains tax",
        "min_investment": "₹1,000",
        "why": "Portfolio diversification and inflation hedge. 5-10% allocation recommended.",
        "pros": ["Inflation protection", "SGB pays 2.5% interest", "No capital gains tax on SGB"],
        "cons": ["No regular income (except SGB)", "SGB has 8-year lock-in"],
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


def _calculate_metrics(profile):
    """Calculate financial metrics from user profile"""
    salary = profile.salary
    expenses = profile.expenses
    money_available = salary - expenses
    savings_rate = (money_available / salary * 100) if salary > 0 else 0
    emergency_target = expenses * 6
    suggested_investment = money_available * 0.8
    
    return {
        'salary': salary,
        'expenses': expenses,
        'money_available': money_available,
        'savings_rate': savings_rate,
        'emergency_target': emergency_target,
        'suggested_investment': suggested_investment
    }


def _render_section_1_metrics(metrics):
    """
    SECTION 1: My Money at a Glance
    Display key financial metrics using native Streamlit components.
    """
    st.markdown("## 💰 My Money at a Glance")
    st.caption("Your financial snapshot at a glance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Monthly Salary",
            value=f"₹{metrics['salary']:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Monthly Expenses",
            value=f"₹{metrics['expenses']:,.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Savings Rate",
            value=f"{metrics['savings_rate']:.1f}%",
            delta=f"{'Good' if metrics['savings_rate'] >= 20 else 'Needs improvement'}"
        )
    
    with col4:
        st.metric(
            label="Monthly Investment Capacity",
            value=f"₹{metrics['money_available']:,.0f}",
            delta=None
        )
    
    st.divider()


def _render_section_2_allocation(metrics, investments):
    """
    SECTION 2: Where Your ₹ Goes
    Display horizontal allocation bar with exact rupee amounts.
    """
    st.markdown("## 📊 Where Your ₹ Goes")
    st.caption("Suggested monthly allocation based on your profile")
    
    # Calculate allocation based on savings rate
    money_available = metrics['money_available']
    savings_rate = metrics['savings_rate']
    
    if savings_rate < 10:
        # Very low saver - focus on emergency fund
        allocation = {
            'Emergency Fund': money_available * 0.5,
            'PPF': money_available * 0.3,
            'Debt Fund': money_available * 0.2,
        }
    elif savings_rate < 20:
        # Moderate saver
        allocation = {
            'Emergency Fund': money_available * 0.15,
            'Index Funds': money_available * 0.35,
            'ELSS': money_available * 0.25,
            'Debt Fund': money_available * 0.15,
            'Gold': money_available * 0.1,
        }
    else:
        # High saver
        allocation = {
            'Index Funds': money_available * 0.35,
            'ELSS': money_available * 0.2,
            'NPS': money_available * 0.15,
            'PPF': money_available * 0.15,
            'Gold': money_available * 0.1,
            'Debt Fund': money_available * 0.05,
        }
    
    # Create allocation dataframe
    allocation_data = []
    for category, amount in allocation.items():
        percentage = (amount / money_available * 100) if money_available > 0 else 0
        allocation_data.append({
            'Category': category,
            'Monthly Amount': f"₹{amount:,.0f}",
            'Percentage': f"{percentage:.1f}%",
            'Value': amount
        })
    
    df = pd.DataFrame(allocation_data)
    
    # Display allocation table
    st.dataframe(
        df[['Category', 'Monthly Amount', 'Percentage']],
        width="stretch",
        hide_index=True
    )
    
    # Display horizontal bar chart
    fig = go.Figure(go.Bar(
        x=df['Value'],
        y=df['Category'],
        orientation='h',
        marker=dict(
            color=['#22C55E', '#2563EB', '#60A5FA', '#F59E0B', '#8B5CF6', '#EF4444'][:len(df)],
            line=dict(color='#111827', width=1)
        ),
        text=df['Percentage'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>₹%{x:,.0f}<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title='',
        xaxis_title='Monthly Amount (₹)',
        yaxis_title='',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=300,
        showlegend=False,
        xaxis=dict(gridcolor='#1F2937', tickprefix='₹', tickformat=','),
        yaxis=dict(gridcolor='#1F2937')
    )
    
    st.plotly_chart(fig, width="stretch")
    st.divider()


def _render_section_3_wealth_journey(metrics):
    """
    SECTION 3: Your Wealth Journey
    Milestone timeline instead of simple line graph.
    """
    st.markdown("## 🗺️ Your Wealth Journey")
    st.caption("Projected wealth growth with key milestones")
    
    suggested_investment = metrics['suggested_investment']
    monthly_return = 0.12 / 12  # 12% annual return
    
    # Calculate values at key years
    years = [1, 3, 5, 7, 10]
    values = []
    milestones = []
    
    cumulative = 0
    for year in range(1, 11):
        for month in range(12):
            cumulative = cumulative * (1 + monthly_return) + suggested_investment
        if year in years:
            values.append(cumulative)
    
    # Define milestones
    milestone_texts = []
    for year, value in zip(years, values):
        milestone_text = f"Year {year}: ₹{value:,.0f}"
        
        # Add milestone annotations
        if year == 1:
            milestone_text += " (First year of investing)"
        elif value >= 1000000 and "₹10 lakh" not in milestone_texts:
            milestone_text += " 🎉 ₹10 lakh reached!"
        elif value >= 2500000 and "₹25 lakh" not in milestone_texts:
            milestone_text += " 🎉 ₹25 lakh reached!"
        elif year == 10:
            milestone_text += " (Goal achieved!)"
        
        milestone_texts.append(milestone_text)
    
    # Display milestones as cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    for idx, (col, year, value, text) in enumerate(zip([col1, col2, col3, col4, col5], years, values, milestone_texts)):
        with col:
            st.metric(
                label=f"Year {year}",
                value=f"₹{value/100000:.1f}L",
                delta=None
            )
            st.caption(text)
    
    # Create line chart
    year_range = list(range(1, 11))
    year_values = []
    cumulative = 0
    for year in range(1, 11):
        for month in range(12):
            cumulative = cumulative * (1 + monthly_return) + suggested_investment
        year_values.append(cumulative)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=year_range,
        y=year_values,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#2563EB', width=3),
        marker=dict(size=10, color='#2563EB'),
        hovertemplate='<b>Year %{x}</b><br>₹%{y:,.0f}<extra></extra>'
    ))
    
    # Add milestone markers
    for year, value in zip(years, values):
        fig.add_annotation(
            x=year,
            y=value,
            text=f"₹{value/100000:.1f}L",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#60A5FA",
            ax=0,
            ay=-40
        )
    
    fig.update_layout(
        title='',
        xaxis_title='Years',
        yaxis_title='Portfolio Value (₹)',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=400,
        showlegend=False,
        xaxis=dict(gridcolor='#1F2937', tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(gridcolor='#1F2937', tickprefix='₹', tickformat=',')
    )
    
    st.plotly_chart(fig, width="stretch")
    st.divider()


def _render_section_4_sip_comparison(metrics):
    """
    SECTION 4: What Happens If You Increase SIP?
    Interactive comparison table showing projected corpus for different monthly amounts.
    """
    st.markdown("## 📈 What Happens If You Increase SIP?")
    st.caption("See how increasing your monthly investment impacts your wealth")
    
    base_sip = max(1000, int(metrics['money_available'] * 0.2))
    sip_amounts = [
        base_sip,
        base_sip * 2,
        base_sip * 3,
        base_sip * 4
    ]
    
    monthly_return = 0.12 / 12  # 12% annual return
    years = [1, 3, 5, 10]
    
    # Calculate corpus for each SIP amount
    comparison_data = []
    for sip in sip_amounts:
        row = {'Monthly SIP': f"₹{sip:,.0f}"}
        for year in years:
            cumulative = 0
            for _ in range(year * 12):
                cumulative = cumulative * (1 + monthly_return) + sip
            row[f'Year {year}'] = f"₹{cumulative/100000:.1f}L"
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, width="stretch", hide_index=True)
    
    # Create comparison chart
    fig = go.Figure()
    
    colors = ['#22C55E', '#60A5FA', '#F59E0B', '#EF4444']
    for idx, sip in enumerate(sip_amounts):
        values = []
        cumulative = 0
        for year in range(1, 11):
            for _ in range(12):
                cumulative = cumulative * (1 + monthly_return) + sip
            values.append(cumulative)
        
        fig.add_trace(go.Scatter(
            x=list(range(1, 11)),
            y=values,
            mode='lines+markers',
            name=f'₹{sip:,.0f}/month',
            line=dict(color=colors[idx], width=2),
            marker=dict(size=6),
            hovertemplate=f'<b>₹{sip:,.0f}/month</b><br>Year %{{x}}<br>₹%{{y:,.0f}}<extra></extra>'
        ))
    
    fig.update_layout(
        title='',
        xaxis_title='Years',
        yaxis_title='Portfolio Value (₹)',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=400,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(gridcolor='#1F2937', tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(gridcolor='#1F2937', tickprefix='₹', tickformat=',')
    )
    
    st.plotly_chart(fig, width="stretch")
    st.divider()


def _render_section_5_investment_cards(investments):
    """
    SECTION 5: Investment Cards
    Display investment options with key information in card format.
    """
    st.markdown("## 💎 Investment Options")
    st.caption("Top investment choices for your profile")
    
    for idx, inv in enumerate(investments, 1):
        with st.container():
            # Header with icon and name
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.markdown(f"### {inv['icon']}")
            with col2:
                st.markdown(f"### {inv['name']}")
                st.caption(f"{inv['category']} · {inv['expected_return']}")
            with col3:
                risk_color = _get_risk_color(inv['risk'])
                st.markdown(f":{risk_color[1:]}[**{inv['risk']} Risk**]")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Expected Return", inv['expected_return'])
            with col2:
                liquidity_color = _get_liquidity_color(inv['liquidity'])
                st.markdown(f"**Liquidity:** :{liquidity_color[1:]}[{inv['liquidity']}]")
            with col3:
                st.markdown(f"**Lock-in:** {inv['lock_in']}")
            with col4:
                st.markdown(f"**Min Investment:** {inv['min_investment']}")
            
            # Why it suits you
            st.info(f"💡 **Why it suits you:** {inv['why']}")
            
            # Pros and Cons
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("✅ Pros"):
                    for pro in inv['pros']:
                        st.markdown(f"- {pro}")
            with col2:
                with st.expander("⚠️ Cons"):
                    for con in inv['cons']:
                        st.markdown(f"- {con}")
            
            # Tax benefits
            st.markdown(f"**Tax Benefits:** {inv['tax_benefits']}")
            
            if idx < len(investments):
                st.divider()


def _render_section_6_portfolio_breakdown(metrics, investments):
    """
    SECTION 6: Portfolio Breakdown
    100% stacked horizontal bar and allocation table.
    """
    st.markdown("## 🎯 Portfolio Breakdown")
    st.caption("Recommended portfolio allocation")
    
    # Calculate allocation
    money_available = metrics['money_available']
    savings_rate = metrics['savings_rate']
    
    if savings_rate < 10:
        allocation = {
            'Emergency Fund': (money_available * 0.5, '#22C55E'),
            'PPF': (money_available * 0.3, '#2563EB'),
            'Debt Fund': (money_available * 0.2, '#60A5FA'),
        }
    elif savings_rate < 20:
        allocation = {
            'Index Funds': (money_available * 0.35, '#2563EB'),
            'ELSS': (money_available * 0.25, '#22C55E'),
            'Emergency Fund': (money_available * 0.15, '#60A5FA'),
            'Debt Fund': (money_available * 0.15, '#F59E0B'),
            'Gold': (money_available * 0.1, '#8B5CF6'),
        }
    else:
        allocation = {
            'Index Funds': (money_available * 0.35, '#2563EB'),
            'ELSS': (money_available * 0.2, '#22C55E'),
            'NPS': (money_available * 0.15, '#60A5FA'),
            'PPF': (money_available * 0.15, '#F59E0B'),
            'Gold': (money_available * 0.1, '#8B5CF6'),
            'Debt Fund': (money_available * 0.05, '#EF4444'),
        }
    
    # Create 100% stacked horizontal bar chart
    fig = go.Figure()
    
    categories = list(allocation.keys())
    amounts = [allocation[cat][0] for cat in categories]
    colors = [allocation[cat][1] for cat in categories]
    percentages = [(amt / money_available * 100) if money_available > 0 else 0 for amt in amounts]
    
    fig.add_trace(go.Bar(
        y=['Portfolio'],
        x=percentages,
        orientation='h',
        marker=dict(color=colors, line=dict(color='#111827', width=1)),
        text=[f"{cat}<br>{pct:.1f}%" for cat, pct in zip(categories, percentages)],
        textposition='inside',
        hovertemplate='<b>%{text}</b><extra></extra>',
        name=''
    ))
    
    fig.update_layout(
        title='',
        xaxis_title='Allocation (%)',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=150,
        showlegend=False,
        xaxis=dict(gridcolor='#1F2937', range=[0, 100]),
        yaxis=dict(showticklabels=False)
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Allocation table
    allocation_data = []
    for category, (amount, _) in allocation.items():
        percentage = (amount / money_available * 100) if money_available > 0 else 0
        allocation_data.append({
            'Investment': category,
            'Monthly Amount': f"₹{amount:,.0f}",
            'Percentage': f"{percentage:.1f}%"
        })
    
    df = pd.DataFrame(allocation_data)
    st.dataframe(df, width="stretch", hide_index=True)
    st.divider()


def _render_section_7_action_plan(metrics):
    """
    SECTION 7: Action Plan
    Timeline of actionable steps instead of AI essays.
    """
    st.markdown("## ✅ Your Action Plan")
    st.caption("Simple steps to get started")
    
    actions = [
        {
            'timeline': 'Week 1',
            'action': 'Open emergency fund',
            'details': f"Set up a liquid fund with ₹{max(500, int(metrics['money_available'] * 0.1)):,.0f} monthly auto-debit",
            'icon': '🛡️'
        },
        {
            'timeline': 'Week 2',
            'action': 'Start SIP',
            'details': f"Begin SIP of ₹{max(1000, int(metrics['money_available'] * 0.3)):,.0f} in index fund",
            'icon': '📈'
        },
        {
            'timeline': 'Month 2',
            'action': 'Review expenses',
            'details': "Track spending for 30 days, identify areas to cut back",
            'icon': '📊'
        },
        {
            'timeline': 'Month 3',
            'action': 'Increase SIP',
            'details': f"Increase SIP to ₹{metrics['suggested_investment']:,.0f} if savings rate improved",
            'icon': '💰'
        },
    ]
    
    for action in actions:
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.markdown(f"### {action['icon']}")
                st.caption(action['timeline'])
            with col2:
                st.markdown(f"**{action['action']}**")
                st.caption(action['details'])
            with col3:
                if st.button("Mark Done", key=f"action_{action['timeline']}", width="stretch"):
                    st.success(f"✓ {action['action']} completed!")
    
    st.divider()


def _render_ai_insights_section(analysis):
    """
    Render AI insights section using native Streamlit components.
    """
    if not analysis:
        return
    
    opportunities = analysis.get('top_opportunities', [])
    market_summary = analysis.get('market_summary', '')
    recommendations = analysis.get('investment_recommendations', [])
    risks = analysis.get('risks', [])
    
    if not opportunities and not market_summary:
        return
    
    st.markdown("## 🤖 AI Insights")
    st.caption("Generated from available AI discovery data")
    
    # Market summary
    if market_summary and "Unable to" not in market_summary:
        with st.container():
            st.info(f"📊 **Market Summary:** {market_summary}")
    
    # AI recommendations
    if recommendations:
        st.markdown("### 💡 AI Recommendations")
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
        st.markdown("### ⚠️ Key Risks")
        for risk in risks[:3]:
            severity = risk.get('severity', 'Medium')
            severity_color = _get_risk_color(severity)
            
            with st.container():
                st.markdown(f"**{risk.get('risk', '')}**")
                st.caption(f":{severity_color[1:]}[Severity: {severity}] {risk.get('mitigation', '')}")


def show():
    """Display investment discovery page"""
    st.title("🔍 Investment Discovery")
    st.caption("AI-powered insights from trusted financial sources")

    # Get user profile
    profile = db.get_latest_profile()
    
    if not profile:
        st.warning("⚠️ Please complete onboarding to see personalized recommendations")
        return
    
    # Calculate metrics
    metrics = _calculate_metrics(profile)
    
    # Initialize session state for AI data
    if "discovery_data" not in st.session_state:
        st.session_state.discovery_data = None
    if "discovery_loading" not in st.session_state:
        st.session_state.discovery_loading = False

    # Refresh button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh Discovery", width="stretch", type="primary"):
            st.session_state.discovery_data = None
            st.session_state.discovery_loading = True
            st.rerun()

    # Load AI data if not already loaded
    if st.session_state.discovery_loading or st.session_state.discovery_data is None:
        with st.spinner("🔍 Analyzing investment opportunities..."):
            try:
                # Collect articles using orchestration layer
                all_articles = collect_all_articles()
                
                # If no articles collected, load fallback dataset
                if not all_articles:
                    all_articles = load_fallback_articles()
                    fallback_used = True
                else:
                    fallback_used = False
                
                # Clean articles
                cleaner = ContentCleaner()
                cleaned_articles = cleaner.process_batch(all_articles)
                
                # If no articles passed cleaning, use fallback dataset
                if not cleaned_articles:
                    all_articles = load_fallback_articles()
                    cleaned_articles = cleaner.process_batch(all_articles)
                    fallback_used = True
                
                # Analyze articles
                analyzer = InsightAnalyzer()
                analysis = analyzer.analyze_collection(cleaned_articles)
                
                # Personalize for user
                user_profile_dict = {
                    'salary': profile.salary,
                    'expenses': profile.expenses,
                    'age': profile.age,
                    'risk': profile.risk,
                    'goal': profile.goal,
                    'monthly_investment': profile.salary - profile.expenses
                }
                
                personalizer = PersonalizationEngine()
                personalized_analysis = personalizer.get_personalized_analysis(
                    analysis,
                    user_profile_dict,
                    top_n=5
                )
                
                # Store in session state
                st.session_state.discovery_data = {
                    'analysis': personalized_analysis,
                    'fallback_used': fallback_used,
                }
                st.session_state.discovery_loading = False
                
            except Exception as e:
                st.error(f"❌ Error during discovery: {str(e)}")
                st.session_state.discovery_loading = False
                return

    # Show fallback banner if demo data used
    if st.session_state.discovery_data and st.session_state.discovery_data.get('fallback_used'):
        st.info("📊 Live sources unavailable. Showing curated investment insights.")
    
    # ------------------------------------------------------------------
    # Render all sections
    # ------------------------------------------------------------------
    
    # Section 1: My Money at a Glance
    _render_section_1_metrics(metrics)
    
    # Section 2: Where Your ₹ Goes
    _render_section_2_allocation(metrics, DEMO_INVESTMENTS)
    
    # Section 3: Your Wealth Journey
    _render_section_3_wealth_journey(metrics)
    
    # Section 4: What Happens If You Increase SIP?
    _render_section_4_sip_comparison(metrics)
    
    # Section 5: Investment Cards
    _render_section_5_investment_cards(DEMO_INVESTMENTS)
    
    # Section 6: Portfolio Breakdown
    _render_section_6_portfolio_breakdown(metrics, DEMO_INVESTMENTS)
    
    # Section 7: Action Plan
    _render_section_7_action_plan(metrics)
    
    # AI Insights (if available)
    if st.session_state.discovery_data:
        _render_ai_insights_section(st.session_state.discovery_data.get('analysis'))
    
    # Disclaimer
    st.divider()
    st.caption("⚠️ **Disclaimer:** This is AI-generated analysis based on publicly available information. "
               "This is not financial advice. Always conduct your own research or consult a qualified financial advisor "
               "before making investment decisions.")


if __name__ == '__main__':
    show()