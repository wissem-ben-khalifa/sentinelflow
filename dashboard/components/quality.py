"""
SentinelFlow - Data Quality Page
Shows profiling metrics and validation results.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
from config.settings import DATABASE_URL

def get_engine():
    return create_engine(DATABASE_URL)




def get_profiling_results(dataset_name: str) -> pd.DataFrame:

    df = pd.read_sql("""
        SELECT DISTINCT ON (column_name)
            column_name, row_count, null_count,
            missing_percentage, duplicate_count,
            duplicate_ratio, mean, median, std,
            min_value, max_value, skewness, kurtosis
        FROM profiling_results
        WHERE dataset_name = %(dataset_name)s
        ORDER BY column_name, run_date DESC
    """, get_engine(), params={"dataset_name": dataset_name})

    return df


def get_validation_results(dataset_name: str) -> pd.DataFrame:

    df = pd.read_sql("""
        SELECT DISTINCT ON (expectation_type, column_name)
            expectation_type, column_name, success,
            observed_value, expected_value, severity
        FROM validation_results
        WHERE dataset_name = %(dataset_name)s
        ORDER BY expectation_type, column_name, run_date DESC
    """, get_engine(), params={"dataset_name": dataset_name})

    return df


def render():
    st.title("Data Quality")

    dataset = st.selectbox("Select Dataset", ["users", "products", "orders"])

    profiling_df = get_profiling_results(dataset)
    validation_df = get_validation_results(dataset)

    st.subheader("Profiling Results")

    if not profiling_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total Rows",
                int(profiling_df["row_count"].iloc[0])
            )
        with col2:
            avg_missing = profiling_df["missing_percentage"].mean()
            st.metric("Avg Missing %", f"{avg_missing:.2f}%")
        with col3:
            total_duplicates = int(profiling_df["duplicate_count"].sum())
            st.metric("Total Duplicates", total_duplicates)

        st.markdown("**Missing Values by Column**")
        fig = px.bar(
            profiling_df,
            x="column_name",
            y="missing_percentage",
            color="missing_percentage",
            color_continuous_scale=["#1a2d1a", "#ffaa00", "#ff4444"],
            text="missing_percentage"
        )
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Full Profiling Table**")
        display_cols = [
            "column_name", "null_count", "missing_percentage",
            "duplicate_count", "mean", "median", "std",
            "min_value", "max_value"
        ]
        st.dataframe(
            profiling_df[display_cols].style.format({
                "missing_percentage": "{:.2f}%",
                "duplicate_count": "{:.0f}",
                "mean": "{:.2f}",
                "median": "{:.2f}",
                "std": "{:.2f}",
                "min_value": "{:.2f}",
                "max_value": "{:.2f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No profiling results found. Run the pipeline first.")

    st.subheader("Validation Results")

    if not validation_df.empty:
        passed = len(validation_df[validation_df["success"] == True])
        failed = len(validation_df[validation_df["success"] == False])
        critical = len(validation_df[
            (validation_df["success"] == False) &
            (validation_df["severity"] == "critical")
        ])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Passed", passed)
        with col2:
            st.metric("Failed", failed)
        with col3:
            st.metric("Critical Failures", critical)

        for _, row in validation_df.iterrows():
            icon = "✓" if row["success"] else "✗"
            color = "green" if row["success"] else (
                "red" if row["severity"] == "critical" else "orange"
            )
            st.markdown(
                f":{color}[{icon}] **{row['expectation_type']}** "
                f"on `{row['column_name']}` — "
                f"observed: {row['observed_value']} | "
                f"expected: {row['expected_value']}"
            )
    else:
        st.info("No validation results found. Run the pipeline first.")