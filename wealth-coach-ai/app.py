import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from config.theme import apply_theme
from database import db
from services.finance.planner import planner
from services.ai import ai

load_dotenv()


def main():
    st.set_page_config(
        page_title="Wealth Coach AI",
        page_icon="💰",
        layout="wide"
    )
    apply_theme()

    # Check if user has a profile
    profile = db.get_latest_profile()
    
    if not profile:
        show_onboarding()
    else:
        show_dashboard(profile)


def show_onboarding():
    """Display simple onboarding form"""
    st.title("💰 Wealth Coach AI")
    st.caption("Turn every paycheck into a personalized wealth plan")
    
    st.markdown("---")
    
    # Input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        salary = st.number_input(
            "Monthly Salary (₹)",
            min_value=20000,
            max_value=500000,
            value=50000,
            step=5000,
            format="%d"
        )
    
    with col2:
        expenses = st.number_input(
            "Monthly Expenses (₹)",
            min_value=0,
            max_value=salary,
            value=30000,
            step=5000,
            format="%d"
        )
    
    with col3:
        age = st.number_input(
            "Age",
            min_value=18,
            max_value=80,
            value=25,
            step=1
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        goal = st.selectbox(
            "Financial Goal",
            ["Emergency Fund", "Buy House", "Travel", "Retirement", "Wealth Creation"]
        )
    
    with col5:
        risk = st.selectbox(
            "Risk Appetite",
            ["Low", "Medium", "High"]
        )
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate My Wealth Plan", width="stretch", type="primary"):
            # Save profile
            db.save_profile(salary, expenses, age, goal, risk)
            
            # Calculate plan
            plan = planner.calculate_plan(salary, expenses, goal, risk)
            
            # Save plan
            db.save_plan(
                plan['money_available'],
                plan['savings_percent'],
                plan['emergency_fund_target'],
                plan['suggested_investment']
            )
            
            st.rerun()


def show_dashboard(profile):
    """Display dashboard with results - redesigned with native Streamlit components"""
    st.title("👋 Welcome Back!")
    st.caption("Here's your personalized wealth plan")
    
    st.markdown("---")
    
    # Calculate metrics
    metrics = planner.calculate_plan(profile.salary, profile.expenses, profile.goal, profile.risk)
    
    # Get AI recommendation
    try:
        ai_recommendation = ai.generate_summary(profile, metrics)
    except Exception:
        ai_recommendation = (
            f"Based on your profile, you're saving {metrics['savings_percent']:.1f}% of your income. "
            f"With ₹{metrics['money_available']:,.0f} available monthly, "
            f"I recommend investing ₹{metrics['suggested_investment']:,.0f} in a diversified portfolio. "
            f"Start with an emergency fund of ₹{metrics['emergency_fund_target']:,.0f} (6 months of expenses), "
            f"then focus on {profile.goal.lower()} through low-cost index funds. "
            f"Your {profile.risk.lower()} risk appetite suggests a balanced approach to wealth building."
        )
    
    # ------------------------------------------------------------------
    # SECTION 1: My Money at a Glance
    # ------------------------------------------------------------------
    st.markdown("## 💰 My Money at a Glance")
    st.caption("Your financial snapshot at a glance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Monthly Salary",
            value=f"₹{profile.salary:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Monthly Expenses",
            value=f"₹{profile.expenses:,.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Savings Rate",
            value=f"{metrics['savings_percent']:.1f}%",
            delta=f"{'Good' if metrics['savings_percent'] >= 20 else 'Needs improvement'}"
        )
    
    with col4:
        st.metric(
            label="Monthly Investment Capacity",
            value=f"₹{metrics['money_available']:,.0f}",
            delta=None
        )
    
    st.divider()
    
    # ------------------------------------------------------------------
    # SECTION 2: Where Your ₹ Goes
    # ------------------------------------------------------------------
    st.markdown("## 📊 Where Your ₹ Goes")
    st.caption("Suggested monthly allocation based on your profile")
    
    money_available = metrics['money_available']
    savings_rate = metrics['savings_percent']
    
    if savings_rate < 10:
        allocation = {
            'Emergency Fund': money_available * 0.5,
            'PPF': money_available * 0.3,
            'Debt Fund': money_available * 0.2,
        }
    elif savings_rate < 20:
        allocation = {
            'Emergency Fund': money_available * 0.15,
            'Index Funds': money_available * 0.35,
            'ELSS': money_available * 0.25,
            'Debt Fund': money_available * 0.15,
            'Gold': money_available * 0.1,
        }
    else:
        allocation = {
            'Index Funds': money_available * 0.35,
            'ELSS': money_available * 0.2,
            'NPS': money_available * 0.15,
            'PPF': money_available * 0.15,
            'Gold': money_available * 0.1,
            'Debt Fund': money_available * 0.05,
        }
    
    # Display allocation table
    allocation_data = []
    for category, amount in allocation.items():
        percentage = (amount / money_available * 100) if money_available > 0 else 0
        allocation_data.append({
            'Category': category,
            'Monthly Amount': f"₹{amount:,.0f}",
            'Percentage': f"{percentage:.1f}%"
        })
    
    df = pd.DataFrame(allocation_data)
    st.dataframe(df, width="stretch", hide_index=True)
    
    # Display horizontal bar chart
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=list(allocation.values()),
        y=list(allocation.keys()),
        orientation='h',
        marker=dict(
            color=['#22C55E', '#2563EB', '#60A5FA', '#F59E0B', '#8B5CF6', '#EF4444'][:len(allocation)],
            line=dict(color='#111827', width=1)
        ),
        text=[f"{(amt/money_available*100):.1f}%" for amt in allocation.values()] if money_available > 0 else [],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>'
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
    
    # ------------------------------------------------------------------
    # SECTION 3: Your Wealth Journey
    # ------------------------------------------------------------------
    st.markdown("## 🗺️ Your Wealth Journey")
    st.caption("Projected wealth growth with key milestones")
    
    suggested_investment = metrics['suggested_investment']
    monthly_return = 0.12 / 12  # 12% annual return
    
    # Calculate values at key years
    years = [1, 3, 5, 7, 10]
    values = []
    
    cumulative = 0
    for year in range(1, 11):
        for month in range(12):
            cumulative = cumulative * (1 + monthly_return) + suggested_investment
        if year in years:
            values.append(cumulative)
    
    # Display milestones as metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    for col, year, value in zip([col1, col2, col3, col4, col5], years, values):
        with col:
            st.metric(
                label=f"Year {year}",
                value=f"₹{value/100000:.1f}L",
                delta=None
            )
    
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
    
    # ------------------------------------------------------------------
    # SECTION 4: What Happens If You Increase SIP?
    # ------------------------------------------------------------------
    st.markdown("## 📈 What Happens If You Increase SIP?")
    st.caption("See how increasing your monthly investment impacts your wealth")
    
    base_sip = max(1000, int(metrics['money_available'] * 0.2))
    sip_amounts = [base_sip, base_sip * 2, base_sip * 3, base_sip * 4]
    
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
    
    # ------------------------------------------------------------------
    # SECTION 5: Investment Readiness Score
    # ------------------------------------------------------------------
    score = calculate_investment_score(metrics)
    score_color = "#22C55E" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"
    
    st.markdown("## 🎯 Investment Readiness Score")
    st.caption("How ready are you to start investing?")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(
            label="Your Score",
            value=f"{score}/100",
            delta=None
        )
        
        if score >= 70:
            st.success("✅ Excellent! You're ready to start investing.")
        elif score >= 40:
            st.warning("⚠️ You're on the right track. Build your emergency fund first.")
        else:
            st.error("❌ Focus on increasing your savings rate before investing.")
    
    st.divider()
    
    # ------------------------------------------------------------------
    # SECTION 6: AI Recommendation
    # ------------------------------------------------------------------
    st.markdown("## 🤖 AI Recommendation")
    st.caption("Personalized advice based on your profile")
    
    st.info(f"**AI Recommendation:** {ai_recommendation}")
    
    st.divider()
    
    # ------------------------------------------------------------------
    # SECTION 7: Action Plan
    # ------------------------------------------------------------------
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
                if st.button("Mark Done", key=f"dashboard_action_{action['timeline']}", width="stretch"):
                    st.success(f"✓ {action['action']} completed!")
    
    st.divider()
    
    # ------------------------------------------------------------------
    # Navigation to other pages
    # ------------------------------------------------------------------
    st.markdown("## 📚 Explore More")
    st.caption("Dive deeper into investment options")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Investment Discovery", width="stretch", type="primary"):
            st.switch_page("pages/investment_discovery.py")
    with col2:
        if st.button("⚖️ Investment Comparison", width="stretch", type="primary"):
            st.switch_page("pages/investment_comparison.py")
    
    st.divider()
    
    # Update profile button
    if st.button("🔄 Update My Profile", width="stretch"):
        db.delete_latest_profile()
        st.rerun()
    
    # Disclaimer
    st.caption("⚠️ **Disclaimer:** This is AI-generated analysis based on publicly available information. "
               "This is not financial advice. Always conduct your own research or consult a qualified financial advisor "
               "before making investment decisions.")


def calculate_investment_score(metrics: dict) -> int:
    """Calculate investment readiness score (0-100)"""
    score = 0
    savings_percent = metrics.get('savings_percent', 0)
    
    # Savings rate contribution (up to 40)
    if savings_percent >= 30:
        score += 40
    elif savings_percent >= 20:
        score += 30
    elif savings_percent >= 10:
        score += 20
    elif savings_percent >= 5:
        score += 10
    
    # Emergency fund progress (up to 30)
    money_available = metrics.get('money_available', 0)
    emergency_target = metrics.get('emergency_fund_target', 0)
    if emergency_target > 0:
        monthly_progress = min(1.0, money_available / emergency_target)
        score += int(monthly_progress * 30)
    
    # Investment capacity (up to 30)
    suggested = metrics.get('suggested_investment', 0)
    if suggested >= money_available * 0.8:
        score += 30
    elif suggested >= money_available * 0.6:
        score += 20
    else:
        score += 10
    
    return max(0, min(100, score))


if __name__ == '__main__':
    main()