import streamlit as st
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
    st.markdown(
        """
    <div style="text-align: center; padding: 48px 24px;">
        <h1 style="font-size: 48px; margin-bottom: 16px;">💰 Wealth Coach AI</h1>
        <p style="font-size: 20px; color: #9CA3AF;">Turn every paycheck into a personalized wealth plan.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Generate button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Generate My Wealth Plan", use_container_width=True, type="primary"):
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
    """Display dashboard with results"""
    # Hero section
    st.markdown(
        """
    <div style="text-align: center; padding: 24px 0;">
        <h1 style="font-size: 36px; margin-bottom: 8px;">👋 Welcome Back!</h1>
        <p style="font-size: 18px; color: #9CA3AF;">Here's your personalized wealth plan</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

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

    # Metrics section
    st.markdown("### 📊 Your Financial Metrics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly Salary", f"₹{profile.salary:,.0f}")
        st.metric("Monthly Expenses", f"₹{profile.expenses:,.0f}")
    
    with col2:
        st.metric("Money Available", f"₹{metrics['money_available']:,.0f}")
        st.metric("Savings Rate", f"{metrics['savings_percent']:.1f}%")
    
    with col3:
        st.metric("Emergency Fund Target", f"₹{metrics['emergency_fund_target']:,.0f}")
        st.metric("Suggested Investment", f"₹{metrics['suggested_investment']:,.0f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Investment Readiness Score
    score = calculate_investment_score(metrics)
    score_color = "#22C55E" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"
    st.markdown(f"""
    <div style="text-align: center; padding: 24px; background-color: #111827; border-radius: 12px; margin: 16px 0;">
        <div style="font-size: 14px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px;">Investment Readiness Score</div>
        <div style="font-size: 48px; font-weight: 700; color: {score_color}; margin: 8px 0;">{score}/100</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # AI Recommendation
    st.markdown("### 🤖 AI Recommendation")
    st.markdown(f"""
    <div class="custom-card" style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%); border: 1px solid rgba(37, 99, 235, 0.3);">
        <p style="font-size: 16px; line-height: 1.6; color: #F9FAFB;">{ai_recommendation}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Projected Wealth Growth (10 Years)")
        render_wealth_projection_chart(metrics['suggested_investment'])
    
    with col2:
        st.markdown("### 💰 Investment Allocation")
        render_allocation_chart(profile.goal, metrics['suggested_investment'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Update profile button
    if st.button("🔄 Update My Profile", use_container_width=True):
        db.delete_latest_profile()
        st.rerun()


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


def render_wealth_projection_chart(suggested_investment: float):
    """Render 10-year wealth projection chart"""
    import plotly.graph_objects as go
    
    years = list(range(1, 11))
    values = []
    cumulative = 0
    monthly_return = 0.12 / 12  # 12% annual return
    
    for year in years:
        for month in range(12):
            cumulative = cumulative * (1 + monthly_return) + suggested_investment
        values.append(cumulative)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=values,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#2563EB', width=3),
        marker=dict(size=8, color='#2563EB')
    ))
    
    fig.update_layout(
        title='',
        xaxis_title='Years',
        yaxis_title='Amount (₹)',
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=400,
        showlegend=False
    )
    
    fig.update_xaxes(gridcolor='#1F2937')
    fig.update_yaxes(gridcolor='#1F2937', tickprefix='₹', tickformat=',')
    
    st.plotly_chart(fig, width='stretch')


def render_allocation_chart(goal: str, suggested_investment: float):
    """Render investment allocation pie chart"""
    import plotly.graph_objects as go
    
    # Simple allocation based on goal
    if goal == "Emergency Fund":
        labels = ['Emergency Fund', 'Liquid Fund', 'Short-term FD']
        values = [suggested_investment * 0.5, suggested_investment * 0.3, suggested_investment * 0.2]
        colors = ['#22C55E', '#2563EB', '#F59E0B']
    elif goal == "Retirement":
        labels = ['Equity Funds', 'Debt Funds', 'PPF/NPS']
        values = [suggested_investment * 0.6, suggested_investment * 0.3, suggested_investment * 0.1]
        colors = ['#2563EB', '#22C55E', '#F59E0B']
    else:
        labels = ['Index Funds', 'ELSS', 'Debt Funds', 'Gold ETF']
        values = [suggested_investment * 0.4, suggested_investment * 0.3, suggested_investment * 0.2, suggested_investment * 0.1]
        colors = ['#2563EB', '#22C55E', '#F59E0B', '#EF4444']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='#111827', width=2)),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title='',
        template='plotly_dark',
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#F9FAFB'),
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch')


if __name__ == '__main__':
    main()