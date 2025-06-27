import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime
import altair as alt

# Setup
st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Track insider trades from [OpenInsider](http://openinsider.com). Uses real-time SEC Form 4 data.")

# Load data
scraper = InsiderScraper()
with st.spinner("🔄 Fetching insider trading data..."):
    df = scraper.fetch()

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

# Sidebar: search filter
st.sidebar.header("🔍 Filter Options")
search = st.sidebar.text_input("Search by Company or Ticker:")
if search:
    df = df[df["Ticker"].str.contains(search, case=False) | df["Company Name"].str.contains(search, case=False)]

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
- **Price**: Price per share.
- **Qty**: Number of shares traded.
- **Owned**: Insider’s total holdings after the trade.
- **ΔOwn**: Ownership percentage change.
- **Value**: Total value of the trade in USD.
""")

# Main table
st.dataframe(df, use_container_width=True)

# Optional: Altair chart for top 10 trades
if "Value" in df.columns:
    chart_df = df.copy()

    # Clean and convert Value
    chart_df["Value (USD)"] = chart_df["Value"].replace('[\$,]', '', regex=True).replace(',', '', regex=True)
    chart_df["Value (USD)"] = pd.to_numeric(chart_df["Value (USD)"], errors='coerce')
    chart_df = chart_df.dropna(subset=["Value (USD)"])

    # Sanitize string fields to prevent Altair crash
    for col in ["Company Name", "Ticker", "Insider Name", "Trade Type", "Qty", "Value"]:
        if col in chart_df.columns:
            chart_df[col] = chart_df[col].astype(str).fillna("")

    chart_df = chart_df.sort_values(by="Value (USD)", ascending=False).head(10)

    try:
        top_chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('Company Name:N', sort='-y'),
            y='Value (USD):Q',
            color='Ticker:N',
            tooltip=['Company Name', 'Insider Name', 'Trade Type', 'Qty', 'Value']
        ).properties(
            title='Top 10 Insider Trades by Value',
            width=800,
            height=400
        )

        st.altair_chart(top_chart, use_container_width=True)

    except Exception as e:
        st.error(f"📉 Chart rendering failed: {e}")


