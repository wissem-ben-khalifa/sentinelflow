"""
SentinelFlow - Streamlit Dashboard
Main entry point for the dashboard application.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="SentinelFlow",
    page_icon="assets/logo.png" if False else "🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .metric-card {
            background-color: #1e1e2e;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
        }
        .alert-critical {
            background-color: #3d1a1a;
            border-left: 4px solid #ff4444;
            padding: 10px;
            border-radius: 4px;
            margin: 5px 0;
        }
        .alert-warning {
            background-color: #3d2e1a;
            border-left: 4px solid #ffaa00;
            padding: 10px;
            border-radius: 4px;
            margin: 5px 0;
        }
        .status-healthy { color: #00cc66; font-weight: bold; }
        .status-degraded { color: #ffaa00; font-weight: bold; }
        .status-critical { color: #ff4444; font-weight: bold; }
        section[data-testid="stSidebar"] {
            background-color: #13131f;
        }
    </style>
""", unsafe_allow_html=True)

from dashboard.components import overview, quality, anomalies, drift

PAGES = {
    "Overview": overview,
    "Data Quality": quality,
    "Anomalies": anomalies,
    "Drift Detection": drift
}

with st.sidebar:
    st.markdown("## SentinelFlow")
    st.markdown("AI-Powered Data Observability")
    st.markdown("---")
    selection = st.radio("Navigate", list(PAGES.keys()))
    st.markdown("---")
    st.markdown("**Pipeline Controls**")
    if st.button("Run Full Pipeline", use_container_width=True):
        with st.spinner("Running pipeline..."):
            from scripts.run_pipeline import run_full_pipeline
            report = run_full_pipeline(
                regenerate_data=True,
                run_autoencoder_detection=False
            )
            st.success(f"Pipeline complete in {report['total_elapsed']}s")
    st.markdown("---")
    st.caption("SentinelFlow v1.0.0")

st.write(f"Loading page: {selection}")
page = PAGES[selection]
try:
    page.render()
except Exception as e:
    st.error(f"Error loading page: {e}")
    import traceback
    st.code(traceback.format_exc())