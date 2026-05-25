import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Fundamental Analysis Dashboard", layout="wide")

st.title("📊 Fundamental Analysis Dashboard")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Enter Stock Tickers (1–4)")

tickers_input = st.sidebar.text_input(
    "Tickers (comma separated)",
    value="NVDA,AAPL,TXN,MU"
)

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:4]

# -----------------------------
# Data Loader
# -----------------------------
@st.cache_data
def load_data(ticker):

    tk = yf.Ticker(ticker)

    data = {}

    try:
        data["Earnings Estimate"] = tk.earnings_estimate
    except:
        pass

    try:
        data["Revenue Estimate"] = tk.revenue_estimate
    except:
        pass

    try:
        data["Earnings History"] = tk.earnings_history
    except:
        pass

    try:
        data["Growth Estimates"] = tk.growth_estimates
    except:
        pass

    return data

# -----------------------------
# Load All Data
# -----------------------------
all_data = {}

for t in tickers:
    all_data[t] = load_data(t)

# -----------------------------
# Score System (simple alpha ranking)
# -----------------------------
def compute_score(df):
    try:
        nums = df.select_dtypes(include=[np.number]).mean().mean()
        return nums
    except:
        return 0

scores = {}

for t in tickers:
    growth = all_data[t].get("Growth Estimates")

    if growth is not None:
        scores[t] = compute_score(growth)
    else:
        scores[t] = 0

score_df = pd.DataFrame({
    "Ticker": list(scores.keys()),
    "Score": list(scores.values())
}).sort_values("Score", ascending=False)

# -----------------------------
# Layout: Scoreboard
# -----------------------------
st.subheader("🏆 Company Ranking (Growth Score)")

fig = px.bar(score_df, x="Ticker", y="Score", color="Score", text="Score")
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Helper: Heat Coloring
# -----------------------------
def style_growth(df):
    def color(val):
        try:
            v = float(str(val).replace("%",""))
            if v > 0:
                return "background-color: #c6f6c6"
            elif v < 0:
                return "background-color: #f6c6c6"
        except:
            return ""
        return ""

    return df.style.applymap(color)

# -----------------------------
# Main Tables (Side-by-Side)
# -----------------------------
st.subheader("📊 Side-by-Side Fundamental Comparison")

sections = ["Revenue Estimate", "Earnings Estimate", "Earnings History", "Growth Estimates"]

for section in sections:

    st.markdown(f"### {section}")

    cols = st.columns(len(tickers))

    for i, t in enumerate(tickers):

        df = all_data[t].get(section)

        with cols[i]:
            st.markdown(f"**{t}**")

            if df is not None and not df.empty:
                if section == "Growth Estimates":
                    st.dataframe(style_growth(df), use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.write("No data")

# -----------------------------
# Growth Chart
# -----------------------------
st.subheader("📈 Growth Comparison Chart")

growth_frames = []

for t in tickers:
    df = all_data[t].get("Growth Estimates")
    if df is not None and not df.empty:
        df = df.copy()
        df["Ticker"] = t
        growth_frames.append(df)

if growth_frames:

    combined = pd.concat(growth_frames)

    numeric_cols = combined.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) > 0:
        col = numeric_cols[0]

        chart_df = combined.groupby("Ticker")[col].mean().reset_index()

        fig = px.bar(chart_df, x="Ticker", y=col, color="Ticker", text=col)
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Footer
# -----------------------------
st.caption("Data source: Yahoo Finance via yfinance")
