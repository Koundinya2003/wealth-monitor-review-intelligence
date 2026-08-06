"""
Investment Discovery Page

Displays AI-analyzed investment opportunities, market insights,
and personalized recommendations from the Discovery Engine.
"""

import streamlit as st
from config.theme import apply_theme
from database import db
from services.discovery import (
    InsightAnalyzer,
    PersonalizationEngine,
    ContentCleaner,
    collect_all_articles,
    load_fallback_articles,
    get_collection_stats,
)

apply_theme()


def show():
    """Display investment discovery page"""
    st.markdown(
        """
    <div style="text-align: center; padding: 24px 0;">
        <h1 style="font-size: 36px; margin-bottom: 8px;">🔍 Investment Discovery</h1>
        <p style="font-size: 18px; color: #9CA3AF;">AI-powered insights from trusted financial sources</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get user profile for personalization
    profile = db.get_latest_profile()
    
    if not profile:
        st.warning("⚠️ Please complete onboarding to see personalized recommendations")
        return
    
    # Initialize session state
    if "discovery_data" not in st.session_state:
        st.session_state.discovery_data = None
    if "discovery_loading" not in st.session_state:
        st.session_state.discovery_loading = False

    # Refresh button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh Discovery", use_container_width=True, type="primary"):
            st.session_state.discovery_data = None
            st.session_state.discovery_loading = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Load data if not already loaded
    if st.session_state.discovery_loading or st.session_state.discovery_data is None:
        with st.spinner("🔍 Analyzing investment opportunities from multiple sources..."):
            try:
                # Collect articles using orchestration layer
                all_articles = collect_all_articles()
                
                # If no articles collected, load fallback dataset
                if not all_articles:
                    st.info("📊 Using demo data for analysis (external sources unavailable)")
                    all_articles = load_fallback_articles()
                    fallback_used = True
                else:
                    fallback_used = False
                
                # Clean articles
                cleaner = ContentCleaner()
                cleaned_articles = cleaner.process_batch(all_articles)
                
                if not cleaned_articles:
                    st.error("❌ No articles passed cleaning filters. Try again later.")
                    st.session_state.discovery_loading = False
                    return
                
                # Analyze articles
                analyzer = InsightAnalyzer()
                analysis = analyzer.analyze_collection(cleaned_articles)
                
                # Personalize for user
                user_profile_dict = {
                    'salary': profile.salary,
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
                
                # Get collection stats for debugging
                collection_stats = get_collection_stats()
                
                # Store in session state
                st.session_state.discovery_data = {
                    'analysis': personalized_analysis,
                    'total_articles': len(all_articles),
                    'cleaned_articles': len(cleaned_articles),
                    'fallback_used': fallback_used,
                    'collection_stats': collection_stats
                }
                st.session_state.discovery_loading = False
                
            except Exception as e:
                st.error(f"❌ Error during discovery: {str(e)}")
                st.session_state.discovery_loading = False
                return

    # Display results
    if st.session_state.discovery_data:
        data = st.session_state.discovery_data
        analysis = data['analysis']
        
        # Show collection source stats
        if data.get('fallback_used'):
            st.info("📊 Live sources unavailable. Showing curated investment insights.")
        
        # Display collection statistics
        collection_stats = data.get('collection_stats', {})
        if collection_stats:
            st.markdown("### 📈 Data Sources")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rss_count = collection_stats.get('rss', {}).get('count', 0)
                st.metric("RSS Articles", rss_count)
            
            with col2:
                newsapi_count = collection_stats.get('newsapi', {}).get('count', 0)
                st.metric("NewsAPI Articles", newsapi_count)
            
            with col3:
                reddit_count = collection_stats.get('reddit', {}).get('count', 0)
                st.metric("Reddit Posts", reddit_count)
            
            with col4:
                if data.get('fallback_used'):
                    st.metric("Fallback Articles", data['total_articles'])
                else:
                    st.metric("Total Articles", data['total_articles'])
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Show processing stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Articles Analyzed", data['total_articles'])
        with col2:
            st.metric("After Cleaning", data['cleaned_articles'])
        with col3:
            st.metric("Opportunities Found", len(analysis.get('top_opportunities', [])))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Top Personalized Opportunities
        if analysis.get('top_opportunities'):
            st.markdown("### 🎯 Top Personalized Opportunities")
            st.markdown("Curated based on your profile and risk appetite")
            
            for idx, opp in enumerate(analysis['top_opportunities'], 1):
                with st.expander(
                    f"#{idx} {opp.get('title', 'Untitled')} - {opp.get('category', 'General')}",
                    expanded=(idx == 1)
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Relevance Score", f"{opp.get('relevance_score', 0):.0f}/100")
                    with col2:
                        st.metric("Category", opp.get('category', 'General'))
                    with col3:
                        confidence = analysis.get('confidence_score', 0) * 100
                        st.metric("AI Confidence", f"{confidence:.0f}%")
                    
                    st.markdown(f"**Why it matters:** {opp.get('description', 'No description available')}")
                    st.markdown(f"**💡 Why this fits you:** {opp.get('personalization_reason', 'Based on your profile')}")
                    
                    # Recommended Action
                    recommendations = analysis.get('investment_recommendations', [])
                    if recommendations:
                        st.markdown(f"**📋 Recommended Action:** {recommendations[0].get('recommendation', 'N/A')}")
                        st.markdown(f"*Reasoning: {recommendations[0].get('reasoning', 'N/A')}*")
                    
                    # Source link
                    source_url = opp.get('source', '')
                    if source_url:
                        st.markdown(f"**🔗 Source:** [{opp.get('source', 'Unknown')}]({source_url})")
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Market Summary
        if analysis.get('market_summary'):
            st.markdown("### 📊 Market Highlights")
            st.info(analysis['market_summary'])
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Government Updates
        if analysis.get('important_policy_updates'):
            st.markdown("### 🏛️ Government Updates")
            for update in analysis['important_policy_updates']:
                with st.expander(f"📢 {update.get('policy', 'Policy Update')}"):
                    st.markdown(f"**Impact:** {update.get('impact', 'No impact details')}")
                    st.markdown(f"**Source:** {update.get('source', 'Unknown')}")
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Investment Recommendations
        if analysis.get('investment_recommendations'):
            st.markdown("### 💡 Investment Recommendations")
            for idx, rec in enumerate(analysis['investment_recommendations'], 1):
                risk_level = rec.get('risk_level', 'Medium')
                risk_color = "#22C55E" if risk_level == "Low" else "#F59E0B" if risk_level == "Medium" else "#EF4444"
                
                st.markdown(f"""
                <div class="custom-card" style="border-left: 4px solid {risk_color};">
                    <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px;">{idx}. {rec.get('recommendation', 'N/A')}</div>
                    <div style="color: #9CA3AF; font-size: 14px; margin-bottom: 8px;">{rec.get('reasoning', 'No reasoning provided')}</div>
                    <div style="display: inline-block; background-color: {risk_color}20; color: {risk_color}; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600;">
                        Risk: {risk_level}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Risks Section
        if analysis.get('risks'):
            st.markdown("### ⚠️ Risks to Consider")
            for risk in analysis['risks']:
                severity = risk.get('severity', 'Medium')
                severity_color = "#22C55E" if severity == "Low" else "#F59E0B" if severity == "Medium" else "#EF4444"
                
                st.markdown(f"""
                <div class="custom-card" style="border-left: 4px solid {severity_color};">
                    <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px;">{risk.get('risk', 'Unknown Risk')}</div>
                    <div style="color: #9CA3AF; font-size: 14px; margin-bottom: 8px;">
                        <strong>Severity:</strong> {severity}<br>
                        <strong>Mitigation:</strong> {risk.get('mitigation', 'No mitigation strategy provided')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Recommended Mutual Funds (from opportunities)
        mutual_funds = [opp for opp in analysis.get('top_opportunities', []) 
                       if 'mutual fund' in opp.get('category', '').lower() or 'sip' in opp.get('category', '').lower()]
        
        if mutual_funds:
            st.markdown("### 💰 Recommended Mutual Funds")
            for idx, fund in enumerate(mutual_funds[:3], 1):
                with st.expander(f"#{idx} {fund.get('title', 'Mutual Fund')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Category", fund.get('category', 'N/A'))
                        st.metric("Relevance", f"{fund.get('relevance_score', 0):.0f}/100")
                    with col2:
                        confidence = analysis.get('confidence_score', 0) * 100
                        st.metric("AI Confidence", f"{confidence:.0f}%")
                    
                    st.markdown(f"**Why it matters:** {fund.get('description', 'No description')}")
                    st.markdown(f"**💡 Why this fits you:** {fund.get('personalization_reason', 'Based on your profile')}")
                    
                    source_url = fund.get('source', '')
                    if source_url:
                        st.markdown(f"**🔗 Learn More:** [{fund.get('source', 'Unknown')}]({source_url})")
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("---")
        st.caption("⚠️ **Disclaimer:** This is AI-generated analysis based on publicly available information. "
                  "This is not financial advice. Always conduct your own research or consult a qualified financial advisor "
                  "before making investment decisions.")
    
    else:
        st.info("👆 Click 'Refresh Discovery' to analyze the latest investment opportunities")


if __name__ == '__main__':
    show()