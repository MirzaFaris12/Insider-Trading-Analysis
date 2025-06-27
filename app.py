import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime
import altair as alt

# Setup
st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Monitor recent insider trades reported to the SEC using data from [OpenInsider](http://openinsider.com).")

# Load data
scraper = InsiderScraper()
with st.spinner("🔄 Fetching insider trading data..."):
    df = scraper.fetch()

# Format numbers
def format_numeric_columns(df):
    for col in ["Qty", "Owned", "Value"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{int(float(x)):,}" if x else x)
    return df

df = format_numeric_columns(df)

# Sidebar filter
st.sidebar.header("🔎 Filter Options")
search = st.sidebar.text_input("Search by Company or Ticker:")

if search:
    df = df[df["Ticker"].str.contains(search, case=False) | df["Company Name"].str.contains(search, case=False)]

# Timestamp
st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Table tooltip help
with st.expander("ℹ️ What do these columns mean?"):
    st.markdown("""
- **Filing Date**: When the insider trade was reported to the SEC.
- **Trade Date**: When the trade actually happened.
- **Ticker**: Stock symbol.
- **Company Name**: Full company name.
- **Insider Name**: Person making the trade (exec, director, etc).
- **Title**: Role of insider (e.g., Director, CEO, 10% Owner).
- **Trade Type**: Type of transaction (P = Purchase, S = Sale).
- **Price**: Price per share.
- **Qty**: Number of shares traded.
- **Owned**: Total shares the insider owns after the trade.
- **ΔOwn**: Change in ownership percentage.
- **Value**: Total value of the trade in USD.
""")

# Data table
st.dataframe(df, use_container_width=True)

# Chart: Top trades by value
if "Value" in df.columns:
    chart_df = df.copy()
    chart_df["Value (USD)"] = chart_df["Value"].replace('[\$,]', '', regex=True).astype(float)
    top_chart = alt.Chart(chart_df.head(10)).mark_bar().encode(
        x=alt.X('Company Name:N', sort='-y'),
        y='Value (USD):Q',
        color='Ticker:N',
        tooltip=['Insider Name', 'Trade Type', 'Qty', 'Value']
    ).properties(
        title='Top 10 Insider Trades by Value',
        width=800,
        height=400
    )
    st.altair_chart(top_chart, use_container_width=True)

# Download
st.download_button("📥 Download CSV", df.to_csv(index=False), "insider_trades.csv")
