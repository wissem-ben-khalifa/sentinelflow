"""
SentinelFlow - Overview Page
Shows platform health score, quality scores,
anomaly counts and alert summary.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from metadata.tracker import get_pipeline_health_score
from sqlalchemy import create_engine
from config.settings import DATABASE_URL

def get_engine():
    return create_engine(DATABASE_URL)




def get_quality_summary() -> pd.DataFrame:

    df = pd.read_sql("""
        SELECT DISTINCT ON (dataset_name)
            dataset_name, quality_score, anomaly_count,
            drift_detected, run_date, status
        FROM pipeline_metadata
        ORDER BY dataset_name, run_date DESC
    """, get_engine())

    return df


def get_recent_alerts() -> pd.DataFrame:
    df = pd.read_sql("""
        SELECT alert_type, dataset_name, message,
               severity, triggered_at
        FROM alerts
        WHERE resolved = FALSE
        ORDER BY triggered_at DESC
        LIMIT 20
    """, get_engine())
    return df


def get_pipeline_runs() -> pd.DataFrame:
    df = pd.read_sql("""
        SELECT dataset_name, quality_score,
               anomaly_count, run_date
        FROM pipeline_metadata
        ORDER BY run_date DESC
        LIMIT 30
    """, get_engine())

    return df


def health_gauge(score: float) -> go.Figure:
    color = "#00cc66" if score >= 80 else "#ffaa00" if score >= 60 else "#ff4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Platform Health Score", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 60], "color": "#2d1a1a"},
                {"range": [60, 80], "color": "#2d2a1a"},
                {"range": [80, 100], "color": "#1a2d1a"}
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": score
            }
        }
    ))
    fig.update_layout(
        height=250,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"}
    )
    return fig


def render():
    st.title("Overview")
    st.markdown("Platform health, quality scores and active alerts.")

    health_score = get_pipeline_health_score()
    quality_df = get_quality_summary()
    alerts_df = get_recent_alerts()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.plotly_chart(health_gauge(health_score), use_container_width=True)

    with col2:
        avg_quality = quality_df["quality_score"].mean() if not quality_df.empty else 0
        st.metric("Avg Quality Score", f"{avg_quality:.1f}/100")
        total_anomalies = int(quality_df["anomaly_count"].sum()) if not quality_df.empty else 0
        st.metric("Total Anomalies", total_anomalies)

    with col3:
        drift_count = int(quality_df["drift_detected"].sum()) if not quality_df.empty else 0
        st.metric("Datasets with Drift", drift_count)
        active_alerts = len(alerts_df)
        st.metric("Active Alerts", active_alerts)

    with col4:
        critical_alerts = len(alerts_df[alerts_df["severity"] == "critical"]) if not alerts_df.empty else 0
        st.metric("Critical Alerts", critical_alerts)
        datasets_monitored = len(quality_df)
        st.metric("Datasets Monitored", datasets_monitored)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Dataset Quality Scores")
        if not quality_df.empty:
            fig = px.bar(
                quality_df,
                x="dataset_name",
                y="quality_score",
                color="quality_score",
                color_continuous_scale=["#ff4444", "#ffaa00", "#00cc66"],
                range_color=[60, 100],
                text="quality_score"
            )
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                showlegend=False,
                yaxis={"range": [0, 110]},
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline runs found. Run the pipeline first.")

    with col_right:
        st.subheader("Anomaly Counts by Dataset")
        if not quality_df.empty:
            fig = px.bar(
                quality_df,
                x="dataset_name",
                y="anomaly_count",
                color="anomaly_count",
                color_continuous_scale=["#1a2d1a", "#ff4444"],
                text="anomaly_count"
            )
            fig.update_traces(texttemplate="%{text}", textposition="outside")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Active Alerts")
    if not alerts_df.empty:
        for _, row in alerts_df.iterrows():
            css_class = "alert-critical" if row["severity"] == "critical" else "alert-warning"
            st.markdown(f"""
                <div class="{css_class}">
                    <strong>[{row['severity'].upper()}]</strong>
                    {row['dataset_name']} — {row['message']}
                    <br><small>{row['triggered_at']}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No active alerts.")