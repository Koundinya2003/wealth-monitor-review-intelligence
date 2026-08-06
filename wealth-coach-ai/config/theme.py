import streamlit as st


def apply_theme():
    """Apply custom dark theme"""
    st.markdown("""
    <style>
    /* Main Theme */
    .stApp {
        background-color: #0B1220;
        color: #F9FAFB;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Typography */
    h1, h2, h3 {
        color: #F9FAFB;
        font-weight: 600;
    }

    /* Cards */
    .custom-card {
        background-color: #111827;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px 32px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
    }

    /* Inputs */
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        background-color: #111827;
        color: #F9FAFB;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
    }

    /* Slider */
    .stSlider>div>div>div>div {
        background-color: #2563EB;
    }

    /* Metrics */
    .metric-container {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #F9FAFB;
        margin: 8px 0;
    }

    .metric-label {
        font-size: 14px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Success message */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid #22C55E;
        color: #22C55E;
    }

    /* Info message */
    .stInfo {
        background-color: rgba(37, 99, 235, 0.1);
        border: 1px solid #2563EB;
        color: #2563EB;
    }
    </style>
    """, unsafe_allow_html=True)
