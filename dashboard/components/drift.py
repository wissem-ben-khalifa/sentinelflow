"""
SentinelFlow - Drift Detection Page
Shows PSI scores, KS-test results and distribution comparisons.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from config.settings import DATABASE_URL
from config.settings import DATABASE_URL, SAMPLES_DIR, RAW_DATA_DIR

def get_engine():
    return create_engine(DATABASE_URL)




def get_drift_results() -> pd.DataFrame:
    df = pd.read_sql("""
        SELECT DISTINCT ON (dataset_name, column_name, detection_method)
            dataset_name, column_name, detection_method,
            drift_score, drift_detected,
            baseline_mean, current_mean,
            baseline_std, current_std, run_date
        FROM drift_results
        ORDER BY dataset_name, column_name, detection_method, run_date DESC
    """, get_engine())
    return df


def render():
    st.title("Drift Detection")

    drift_df = get_drift_results()

    if drift_df.empty:
        st.info("No drift results found. Run the pipeline first.")
        return

    total_checks = len(drift_df)
    drift_detected = len(drift_df[drift_df["drift_detected"] == True])
    datasets_with_drift = drift_df[drift_df["drift_detected"] == True]["dataset_name"].nunique()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Drift Checks", total_checks)
    with col2:
        st.metric("Drift Detected", drift_detected)
    with col3:
        st.metric("Datasets Affected", datasets_with_drift)

    st.subheader("Drift Scores by Dataset and Method")

    fig = px.bar(
        drift_df,
        x="column_name",
        y="drift_score",
        color="detection_method",
        facet_col="dataset_name",
        barmode="group",
        title="Drift Scores Across All Datasets"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Distribution Comparison")
    st.markdown("Comparing baseline (clean) vs current (raw) distributions for orders amount.")

    try:
        baseline = pd.read_csv(SAMPLES_DIR / "orders_clean.csv")["amount"]
        current = pd.read_csv(RAW_DATA_DIR / "orders_drifted.csv")["amount"]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=baseline,
            name="Baseline (clean)",
            marker_color="#00cc66",
            opacity=0.6,
            nbinsx=40
        ))
        fig.add_trace(go.Histogram(
            x=current,
            name="Current (drifted)",
            marker_color="#ff4444",
            opacity=0.6,
            nbinsx=40
        ))
        fig.update_layout(
            title="Orders Amount Distribution: Baseline vs Current",
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Baseline Statistics**")
            st.write(f"Mean: {baseline.mean():.2f}")
            st.write(f"Std: {baseline.std():.2f}")
            st.write(f"Min: {baseline.min():.2f}")
            st.write(f"Max: {baseline.max():.2f}")
        with col2:
            st.markdown("**Current Statistics**")
            st.write(f"Mean: {current.mean():.2f}")
            st.write(f"Std: {current.std():.2f}")
            st.write(f"Min: {current.min():.2f}")
            st.write(f"Max: {current.max():.2f}")

    except Exception as e:
        st.warning(f"Could not load distribution data: {e}")

    st.subheader("Full Drift Results Table")
    display_df = drift_df[[
        "dataset_name", "column_name", "detection_method",
        "drift_score", "drift_detected", "baseline_mean", "current_mean"
    ]].copy()
    display_df["drift_detected"] = display_df["drift_detected"].map(
        {True: "YES", False: "no"}
    )
    st.dataframe(display_df, use_container_width=True)