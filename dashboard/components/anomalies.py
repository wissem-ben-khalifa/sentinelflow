"""
SentinelFlow - Anomalies Page
Shows anomaly detection results by method with charts.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from config.settings import DATABASE_URL

def get_engine():
    return create_engine(DATABASE_URL)



def get_anomaly_summary() -> pd.DataFrame:

    df = pd.read_sql("""
        SELECT
            dataset_name,
            detection_method,
            COUNT(*) as total_records,
            SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomaly_count,
            ROUND(AVG(anomaly_score)::numeric, 4) as avg_score
        FROM anomaly_results
        GROUP BY dataset_name, detection_method
        ORDER BY dataset_name, detection_method
    """, get_engine())

    return df



def get_anomaly_details(dataset_name: str, method: str) -> pd.DataFrame:
    return pd.read_sql("""
        SELECT record_id, anomaly_score, is_anomaly, explanation
        FROM anomaly_results
        WHERE dataset_name = %(dataset_name)s
        AND detection_method = %(method)s
        ORDER BY anomaly_score DESC
        LIMIT 500
    """, get_engine(), params={"dataset_name": dataset_name, "method": method})


def render():
    st.title("Anomaly Detection")

    summary_df = get_anomaly_summary()

    if summary_df.empty:
        st.info("No anomaly results found. Run the pipeline first.")
        return

    st.subheader("Detection Summary")

    methods = summary_df["detection_method"].unique().tolist()
    datasets = summary_df["dataset_name"].unique().tolist()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            summary_df,
            x="dataset_name",
            y="anomaly_count",
            color="detection_method",
            barmode="group",
            title="Anomaly Count by Dataset and Method"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            summary_df,
            x="detection_method",
            y="avg_score",
            color="dataset_name",
            barmode="group",
            title="Average Anomaly Score by Method"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Drill Down")

    col1, col2 = st.columns(2)
    with col1:
        selected_dataset = st.selectbox("Dataset", datasets)
    with col2:
        available_methods = summary_df[
            summary_df["dataset_name"] == selected_dataset
        ]["detection_method"].unique().tolist()
        selected_method = st.selectbox("Detection Method", available_methods)

    details_df = get_anomaly_details(selected_dataset, selected_method)

    if not details_df.empty:
        anomalies_only = details_df[details_df["is_anomaly"] == True]
        normal_only = details_df[details_df["is_anomaly"] == False]

        st.markdown(
            f"Showing top results for **{selected_dataset}** "
            f"using **{selected_method}**: "
            f"{len(anomalies_only)} anomalies, {len(normal_only)} normal"
        )

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=normal_only["anomaly_score"],
            name="Normal",
            marker_color="#00cc66",
            opacity=0.7,
            nbinsx=30
        ))
        fig.add_trace(go.Histogram(
            x=anomalies_only["anomaly_score"],
            name="Anomaly",
            marker_color="#ff4444",
            opacity=0.7,
            nbinsx=30
        ))
        fig.update_layout(
            title="Anomaly Score Distribution",
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        if not anomalies_only.empty:
            st.markdown("**Top Anomalous Records**")
            st.dataframe(
                anomalies_only[["record_id", "anomaly_score", "explanation"]].head(20),
                use_container_width=True
            )