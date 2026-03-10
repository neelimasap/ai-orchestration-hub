"""
Analytics Dashboard — usage, latency, tokens across providers.
"""
import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core.database import init_db, get_runs, get_reports, get_stats

init_db()

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
st.title("📊 Analytics Dashboard")
st.markdown("Track usage, performance and costs across all AI providers.")

runs = get_runs(500)
reports = get_reports(50)

if not runs:
    st.info("No data yet — run some analyses from the main page first.")
    st.stop()

df = pd.DataFrame(runs)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["total_tokens"] = df["input_tokens"] + df["output_tokens"]
df["date"] = df["timestamp"].dt.date

# ── top metrics ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Runs", len(df))
c2.metric("Documents Analyzed", df["doc_name"].nunique())
c3.metric("Total Tokens Used", f"{df['total_tokens'].sum():,}")
c4.metric("Avg Latency", f"{df['latency_ms'].mean():.0f}ms")

st.markdown("---")

col1, col2 = st.columns(2)

# ── calls per provider ────────────────────────────────────────────────────────
with col1:
    st.subheader("Calls by Provider")
    provider_counts = df.groupby("provider").size().reset_index(name="calls")
    chart = alt.Chart(provider_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("provider:N", title="Provider"),
        y=alt.Y("calls:Q", title="Total Calls"),
        color=alt.Color("provider:N", scale=alt.Scale(
            domain=["Groq", "Claude", "Gemini"],
            range=["#f97316", "#8b5cf6", "#06b6d4"]
        )),
        tooltip=["provider", "calls"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

# ── avg latency per provider ──────────────────────────────────────────────────
with col2:
    st.subheader("Average Latency (ms)")
    latency_df = df.groupby("provider")["latency_ms"].mean().reset_index()
    latency_df.columns = ["provider", "avg_latency"]
    chart2 = alt.Chart(latency_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("provider:N", title="Provider"),
        y=alt.Y("avg_latency:Q", title="Avg Latency (ms)"),
        color=alt.Color("provider:N", scale=alt.Scale(
            domain=["Groq", "Claude", "Gemini"],
            range=["#f97316", "#8b5cf6", "#06b6d4"]
        )),
        tooltip=["provider", alt.Tooltip("avg_latency:Q", format=".0f")]
    ).properties(height=300)
    st.altair_chart(chart2, use_container_width=True)

col3, col4 = st.columns(2)

# ── tokens over time ──────────────────────────────────────────────────────────
with col3:
    st.subheader("Token Usage Over Time")
    tokens_by_date = df.groupby(["date", "provider"])["total_tokens"].sum().reset_index()
    chart3 = alt.Chart(tokens_by_date).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("total_tokens:Q", title="Tokens"),
        color=alt.Color("provider:N", scale=alt.Scale(
            domain=["Groq", "Claude", "Gemini"],
            range=["#f97316", "#8b5cf6", "#06b6d4"]
        )),
        tooltip=["date:T", "provider", "total_tokens"]
    ).properties(height=300)
    st.altair_chart(chart3, use_container_width=True)

# ── task breakdown ────────────────────────────────────────────────────────────
with col4:
    st.subheader("Tasks by Type")
    task_counts = df.groupby("task").size().reset_index(name="count").sort_values("count", ascending=False)
    chart4 = alt.Chart(task_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("count:Q", title="Count"),
        y=alt.Y("task:N", sort="-x", title="Task"),
        tooltip=["task", "count"]
    ).properties(height=300)
    st.altair_chart(chart4, use_container_width=True)

# ── recent runs table ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Recent Runs")
display_df = df[["timestamp", "doc_name", "task", "provider", "model",
                  "latency_ms", "total_tokens"]].head(20)
display_df.columns = ["Time", "Document", "Task", "Provider", "Model", "Latency (ms)", "Tokens"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── saved reports ─────────────────────────────────────────────────────────────
if reports:
    st.markdown("---")
    st.subheader("Saved Reports")
    for r in reports[:10]:
        with st.expander(f"📄 {r['doc_name']} — {r['timestamp'][:16]}"):
            st.markdown(r["summary"])
            import json
            data = json.loads(r["full_json"])
            for task, info in data.items():
                st.markdown(f"**{task}** via {info['provider']} ({info['latency_ms']}ms)")
