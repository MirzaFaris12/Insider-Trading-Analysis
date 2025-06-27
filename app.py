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

# If no data is found
if df.empty:
    st.warning("⚠️ No insider trades found in the past day.")
    st.stop()

# Remove "X" column if exists
if "X" in df.columns:
    df = df.drop(columns=["X"])

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
    company_col = next((col for col in df.columns if "Company" in col), None)
    if company_col and "Ticker" in df.columns:
        df = df[
            df["Ticker"].astype(str).str.contains(search, case=False) |
            df[company_col].astype(str).str.contains(search, case=False)
        ]
    else:
        st.warning("⚠️ Search could not apply — missing 'Ticker' or 'Company' column.")

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
- **Form 4 Link**: Direct link to the SEC Form 4 filing for more info.
""")

# Convert SEC Form 4 link to HTML for rendering
def make_clickable(val):
    return f'<a href="{val}" target="_blank">🔗 Form 4</a>' if pd.notnull(val) else ""

# Display table with clickable Form 4 links
display_df = df.copy()
if "Form 4 Link" in df.columns:
    display_df["Form 4 Link"] = display_df["Form 4 Link"].apply(make_clickable)

st.write("### Insider Trades Table")
st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Altair chart for top trades
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

    if None not in col_map.values():
        chart_df = chart_df.sort_values(by="Value (USD)", ascending=False).head(10)
        for col in col_map.values():
            chart_df[col] = chart_df[col].astype(str).fillna("")

        chart = alt.Chart(chart_df).mark_bar().encode(
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
        st.altair_chart(chart, use_container_width=True)

# Download button
csv_download = df.copy()
st.download_button("📥 Download CSV", csv_download.to_csv(index=False), file_name="insider_trades.csv")









