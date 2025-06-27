import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime
import altair as alt

# Setup
st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Track insider trades from [OpenInsider](http://openinsider.com). Uses real-time SEC Form 4 data.")

# Sidebar hybrid controls
st.sidebar.header("🔍 Search Options")
ticker_input = st.sidebar.text_input("Enter a ticker (optional)", "").upper()
days_back = st.sidebar.slider("Lookback window (days)", 1, 365, value=5 if not ticker_input else 180)

# Load data
scraper = InsiderScraper()
with st.spinner("🔄 Fetching insider trading data..."):
    if ticker_input:
        df = scraper.fetch(ticker=ticker_input, days_back=days_back)
    else:
        df = scraper.fetch(days_back=days_back)

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

# Sidebar filter inside results
search = st.sidebar.text_input("🔎 Filter results (company or ticker):")
if search:
    company_col = next((col for col in df.columns if "Company" in col), None)
    if company_col and "Ticker" in df.columns:
        df = df[
            df["Ticker"].astype(str).str.contains(search, case=False) |
            df[company_col].astype(str).str.contains(search, case=False)
        ]
    else:
        st.warning("⚠️ Filtering failed – missing 'Company' or 'Ticker' column.")

# Timestamp
st.caption(f"🕒 Data retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Column explanations
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

# Table display logic
if df.empty:
    st.warning("No insider trades found.")
else:
    if ticker_input:
        st.subheader(f"📄 Insider Trades for {ticker_input} (last {days_back} days)")
    elif search:
        st.subheader(f"🔎 Search results for '{search}'")
    else:
        st.subheader("🔥 Top Recent Insider Trades")

    st.dataframe(df, use_container_width=True)

# Chart for top trades
if "Value" in df.columns:
    chart_df = df.copy()
    chart_df["Value (USD)"] = chart_df["Value"].replace('[\$,]', '', regex=True).replace(',', '', regex=True)
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
        st.warning("⚠️ Chart cannot be displayed due to missing columns.")
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

# Download button
st.download_button("📥 Download CSV", df.to_csv(index=False), "insider_trades.csv")







