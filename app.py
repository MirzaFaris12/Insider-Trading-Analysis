import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime
import altair as alt
import yfinance as yf

# Setup
st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Track insider trades from [OpenInsider](http://openinsider.com). Uses real-time SEC Form 4 data.")

# Sidebar: controls
st.sidebar.header("🔧 Controls")
lookback_days = st.sidebar.slider("Lookback period (days):", 1, 60, 30)
search = st.sidebar.text_input("Search by Company or Ticker:")

# Load data
scraper = InsiderScraper(lookback_days=lookback_days)
with st.spinner("🔄 Fetching insider trading data..."):
    df = scraper.fetch()

# Handle empty results
if df.empty:
    st.warning(f"⚠️ No insider trades found in the past {lookback_days} day(s).")
    st.stop()

# Format numeric columns
def format_numeric_columns(df):
    for col in ["Qty", "Owned", "Value"]:
        if col in df.columns:
            def safe_format(x):
                try:
                    x = str(x).replace(",", "").replace("$", "")
                    return f"{int(float(x)):,}"
                except:
                    return x
            df[col] = df[col].apply(safe_format)
    return df

df = format_numeric_columns(df)

# Drop unwanted column
if "X" in df.columns:
    df = df.drop(columns=["X"])

# Add current price and change vs. filing
if "Ticker" in df.columns and "Price" in df.columns:
    def get_current_price(ticker):
        try:
            return yf.Ticker(ticker).info.get("currentPrice", None)
        except:
            return None

    df["Current Price"] = df["Ticker"].apply(get_current_price)
    df["Price"] = pd.to_numeric(df["Price"].str.replace("$", ""), errors='coerce')
    df["Price Change (%)"] = ((df["Current Price"] - df["Price"]) / df["Price"] * 100).round(2)

# Filter by search
if search:
    company_col = next((col for col in df.columns if "Company" in col), None)
    if company_col and "Ticker" in df.columns:
        df = df[
            df["Ticker"].astype(str).str.contains(search, case=False) |
            df[company_col].astype(str).str.contains(search, case=False)
        ]
    else:
        st.warning("⚠️ Search could not apply — missing 'Ticker' or 'Company' column.")

# Smart Money Tracker
with st.expander("🧠 Smart Money Tracker: Top Insiders by Avg Gain (%)"):
    if all(col in df.columns for col in ["Insider Name", "Trade Type", "Price", "Ticker"]):
        smart_df = df[df["Trade Type"].str.startswith("P")].copy()
        smart_df["Price"] = pd.to_numeric(smart_df["Price"].replace('[\$,]', '', regex=True), errors='coerce')
        smart_df = smart_df.dropna(subset=["Price", "Ticker", "Insider Name"])

        tickers = smart_df["Ticker"].unique().tolist()
        current_prices = {}
        for ticker in tickers:
            try:
                hist = yf.Ticker(ticker).history(period="1d")
                if not hist.empty:
                    current_prices[ticker] = hist["Close"].iloc[-1]
            except:
                continue

        def compute_gain(row):
            current = current_prices.get(row["Ticker"], None)
            if current is None or row["Price"] <= 0:
                return None
            return ((current - row["Price"]) / row["Price"]) * 100

        smart_df["Gain (%)"] = smart_df.apply(compute_gain, axis=1)
        smart_df = smart_df.dropna(subset=["Gain (%)"])

        leaderboard = smart_df.groupby("Insider Name")["Gain (%)"].mean().sort_values(ascending=False).head(10)
        st.dataframe(leaderboard.reset_index().rename(columns={"Gain (%)": "Avg Gain (%)"}), use_container_width=True)
    else:
        st.warning("❗ Required columns missing to compute Smart Money Tracker.")

# Timestamp
st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Column Explanation
with st.expander("ℹ️ What do these columns mean?"):
    st.markdown("""
- **Filing Date**: When the insider trade was reported to the SEC.
- **Trade Date**: When the trade actually occurred.
- **Ticker**: Stock symbol of the company.
- **Company Name**: Full name of the company.
- **Insider Name**: Person who made the trade.
- **Title**: Role of the insider (e.g., Director, CEO, 10% Owner).
- **Trade Type**: P = Purchase, S = Sale.
- **Price**: Price per share at the time of the trade.
- **Current Price**: Latest stock price from Yahoo Finance.
- **Price Change (%)**: Change since filing.
- **Qty**: Shares traded.
- **Owned**: Insider’s total holdings after trade.
- **ΔOwn**: Ownership % change.
- **Value**: Total value of trade (USD).
""")

# Main Data Table
st.dataframe(df, use_container_width=True)

# Optional: Altair chart for top 10 trades by value
if "Value" in df.columns:
    chart_df = df.copy()
    chart_df["Value (USD)"] = chart_df["Value"].replace('[\$,]', '', regex=True)
    chart_df["Value (USD)"] = pd.to_numeric(chart_df["Value (USD)"], errors='coerce')
    chart_df = chart_df.dropna(subset=["Value (USD)"])

    col_map = {
        "company": next((col for col in chart_df.columns if "Company" in col), None),
        "insider": next((col for col in chart_df.columns if "Insider" in col), None),
        "ticker": next((col for col in chart_df.columns if "Ticker" in col), None),
        "type": next((col for col in chart_df.columns if "Type" in col), None),
        "qty": next((col for col in chart_df.columns if "Qty" in col), None),
        "value": "Value"
    }

    if None in col_map.values():
        st.warning("⚠️ One or more chart-required columns are missing. Chart will not render.")
    else:
        chart_df = chart_df.sort_values(by="Value (USD)", ascending=False).head(10)
        for col in col_map.values():
            chart_df[col] = chart_df[col].astype(str).fillna("")

        try:
            top_chart = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X(f'{col_map["company"]}:N', sort='-y'),
                y='Value (USD):Q',
                color=f'{col_map["ticker"]}:N',
                tooltip=[
                    col_map["company"],
                    col_map["insider"],
                    col_map["type"],
                    col_map["qty"],
                    col_map["value"]
                ]
            ).properties(
                title='Top 10 Insider Trades by Value',
                width=800,
                height=400
            )
            st.altair_chart(top_chart, use_container_width=True)
        except Exception as e:
            st.error(f"📉 Chart rendering failed: {e}")











