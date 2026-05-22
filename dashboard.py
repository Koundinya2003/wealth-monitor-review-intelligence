"""Streamlit dashboard for App Review Intelligence."""

from __future__ import annotations

import json
import pandas as pd
import plotly.express as px
import streamlit as st

from src import config
from src.clean_reviews import clean_reviews_df
from src.fetch_reviews import fetch_all_reviews
from src.generate_email import generate_email_draft
from src.generate_report import generate_weekly_pulse
from src.run_pipeline import run_pipeline
from src.theme_analysis import analyze_themes
from src.visualizations import build_sentiment_chart, load_analysis

st.set_page_config(
    page_title="Wealth Monitor · Review Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }
    h1 { font-weight: 700; letter-spacing: -0.02em; }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _load_reviews(upload) -> pd.DataFrame:
    if upload is not None:
        df = pd.read_csv(upload)
        return clean_reviews_df(df)
    if config.REVIEWS_CSV.exists():
        return pd.read_csv(config.REVIEWS_CSV)
    return pd.DataFrame()


def main() -> None:
    st.title("Wealth Monitor · App Review Intelligence")
    st.caption("Product pulse from App Store & Google Play — AI themes, sentiment, and weekly outputs.")

    with st.sidebar:
        st.header("Controls")
        use_sample = st.toggle("Use demo/sample data", value=config.use_sample_data())
        skip_fetch = st.toggle("Skip store fetch", value=False)
        uploaded = st.file_uploader("Upload reviews CSV", type=["csv"])
        if st.button("Fetch reviews from stores", type="primary"):
            with st.spinner("Fetching public reviews…"):
                fetch_all_reviews(use_sample=use_sample)
            st.success(f"Saved to {config.REVIEWS_CSV}")

        if st.button("Run full analysis pipeline"):
            with st.spinner("Analyzing reviews with AI…"):
                run_pipeline(skip_fetch=skip_fetch or uploaded is not None, use_sample=use_sample)
            st.success("Pipeline complete.")
            st.rerun()

    df = _load_reviews(uploaded)
    if uploaded is not None:
        config.ensure_dirs()
        clean_reviews_df(df).to_csv(config.REVIEWS_CSV, index=False)

    if df.empty:
        st.info("Upload a CSV or fetch reviews to get started.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Reviews", len(df))
    col2.metric("Avg rating", f"{df['rating'].mean():.2f}")
    col3.metric("Google Play", int((df["store"] == "google_play").sum()))
    col4.metric("App Store", int((df["store"] == "apple_app_store").sum()))

    analyzed_path = config.DATA_DIR / "reviews_analyzed.csv"
    if analyzed_path.exists():
        themed = pd.read_csv(analyzed_path)
    else:
        themed = None

    tab_overview, tab_themes, tab_reports, tab_email = st.tabs(
        ["Overview", "Themes & sentiment", "Reports", "Email draft"]
    )

    with tab_overview:
        st.subheader("Review volume by store")
        by_store = df.groupby("store").size().reset_index(name="count")
        fig_store = px.bar(by_store, x="store", y="count", color="store", text="count")
        fig_store.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig_store, use_container_width=True)

        st.dataframe(df.sort_values("review_date", ascending=False).head(50), use_container_width=True)

    with tab_themes:
        if themed is None:
            if st.button("Analyze themes (OpenAI)"):
                with st.spinner("Running theme analysis…"):
                    analyze_themes(df)
                    build_sentiment_chart(pd.read_csv(analyzed_path))
                st.rerun()
            st.warning("Run analysis to see themes and sentiment.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                sent = themed["sentiment"].value_counts().reset_index()
                sent.columns = ["sentiment", "count"]
                fig = px.pie(sent, names="sentiment", values="count", hole=0.45)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                th = themed["theme"].value_counts().head(5).reset_index()
                th.columns = ["theme", "count"]
                fig2 = px.bar(th, x="count", y="theme", orientation="h")
                st.plotly_chart(fig2, use_container_width=True)

            if config.SENTIMENT_CHART.exists():
                st.image(str(config.SENTIMENT_CHART), caption="Sentiment & theme snapshot")

            st.dataframe(
                themed[["store", "rating", "theme", "sentiment", "review_text", "review_date"]].head(100),
                use_container_width=True,
            )

    with tab_reports:
        if config.ANALYSIS_JSON.exists():
            analysis = load_analysis()
            st.subheader("Weekly pulse preview")
            if config.WEEKLY_PULSE_MD.exists():
                st.markdown(config.WEEKLY_PULSE_MD.read_text(encoding="utf-8"))
            c1, c2 = st.columns(2)
            if c1.download_button(
                "Download Markdown",
                config.WEEKLY_PULSE_MD.read_bytes(),
                file_name="weekly_pulse.md",
            ):
                pass
            if config.WEEKLY_PULSE_PDF.exists() and c2.download_button(
                "Download PDF",
                config.WEEKLY_PULSE_PDF.read_bytes(),
                file_name="weekly_pulse.pdf",
            ):
                pass
            if st.button("Regenerate report & PDF"):
                generate_weekly_pulse(analysis)
                st.rerun()
        else:
            st.info("Run the pipeline to generate reports.")

    with tab_email:
        if config.EMAIL_DRAFT_MD.exists():
            st.markdown(config.EMAIL_DRAFT_MD.read_text(encoding="utf-8"))
            st.download_button(
                "Download email draft",
                config.EMAIL_DRAFT_MD.read_bytes(),
                file_name="email_draft.md",
            )
        else:
            if st.button("Generate email draft") and config.ANALYSIS_JSON.exists():
                generate_email_draft(load_analysis())
                st.rerun()
            st.info("Run the pipeline to generate the email draft.")


if __name__ == "__main__":
    main()
