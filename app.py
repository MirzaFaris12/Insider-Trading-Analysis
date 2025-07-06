import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import yfinance as yf

# Page Setup
st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Track insider trades from [OpenInsider](http://openinsider.com). Uses real-time SEC Form 4 data.")

# Sidebar Controls
st.sidebar.header("🔧 Controls")
lookback_days = st.sidebar.slider("Lookback period (days):", 1, 60, 7)
search = st.sidebar.text_input("Search by Company or Ticker:")

# Load Data
scraper = InsiderScraper()
with st.spinner("🔄 Fetching insider trading data..."):
    df = scraper.fetch(lookback_days=lookback_days)

# Handle empty results
if df.empty:
    st.warning("⚠️ No insider trades found in the selected period.")
    st.stop()

# Format numeric columns safely
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

# Drop unwanted columns
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

# Apply Search Filter
if search:
    company_col = next((col for col in df.columns if "Company" in col), None)
    if company_col and "Ticker" in df.columns:
        df = df[
            df["Ticker"].astype(str).str.contains(search, case=False) |
            df[company_col].astype(str).str.contains(search, case=False)
        ]

# Timestamp
st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Tooltip explanation
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
- **Current Price**: Latest stock price pulled from Yahoo Finance.
- **Price Change (%)**: Percent difference between filing and current price.
- **Qty**: Number of shares traded.
- **Owned**: Insider’s total holdings after the trade.
- **ΔOwn**: Ownership percentage change.
- **Value**: Total value of the trade in USD.
""")

# Display main data table
st.dataframe(df, use_container_width=True)

# Altair Chart for Top Trades by Value
if "Value" in df.columns:
    chart_df = df.copy()
    chart_df["Value (USD)"] = chart_df["Value"].replace('[\\$,]', '', regex=True)
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

# Insider Win Rate Feature
with st.expander("🧠 Insider Win Rate (30-day Gain Frequency)"):
    if all(col in df.columns for col in ["Insider Name", "Ticker", "Price"]):
        win_df = df[df["Trade Type"].str.startswith("P")].copy()
        win_df["Price"] = pd.to_numeric(win_df["Price"].replace("$", "").replace(",", ""), errors='coerce')
        win_df = win_df.dropna(subset=["Price", "Ticker", "Insider Name"])

        win_counts = []
        for idx, row in win_df.iterrows():
            ticker = row["Ticker"]
            price_at_trade = row["Price"]
            try:
                hist = yf.Ticker(ticker).history(period="30d")
                if not hist.empty:
                    price_after_30d = hist["Close"].iloc[-1]
                    win = price_after_30d > price_at_trade
                    win_counts.append((row["Insider Name"], win))
            except:
                continue

        if win_counts:
            win_df_summary = pd.DataFrame(win_counts, columns=["Insider", "Win"])
            stats = win_df_summary.groupby("Insider")["Win"].agg(["sum", "count"])
            stats["Win Rate (%)"] = (stats["sum"] / stats["count"] * 100).round(2)
            stats = stats.rename(columns={"sum": "Wins", "count": "Total Trades"})
            stats = stats.sort_values(by="Win Rate (%)", ascending=False).head(10)
            st.dataframe(stats.reset_index(), use_container_width=True)
        else:
            st.info("No valid win rate data available for the selected period.")
    else:
        st.warning("❗ Required columns missing to compute Insider Win Rate.")












