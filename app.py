import streamlit as st
from insider_scraper import InsiderScraper
import pandas as pd
from datetime import datetime

# Page setup
st.set_page_config(page_title="Insider Tracker", layout="wide")
st.title("🕵️‍♂️ Insider Trading Tracker")
st.markdown("Visualize recent insider trades reported to the SEC. Clean. Modern. Minimal.")

# Load data
scraper = InsiderScraper()
with st.spinner("Fetching fresh insider data..."):
    df = scraper.fetch()

# Format numeric columns
def safe_format(x):
    try:
        x = str(x).replace(",", "").replace("$", "")
        return f"{int(float(x)):,}"
    except:
        return x

for col in ["Qty", "Owned", "Value"]:
    if col in df.columns:
        df[col] = df[col].apply(safe_format)

# Company search
st.sidebar.markdown("### 🔎 Filter")
search = st.sidebar.text_input("Search by Ticker or Company")
company_col = next((c for c in df.columns if "Company" in c), None)
if search and company_col and "Ticker" in df.columns:
    df = df[
        df["Ticker"].astype(str).str.contains(search, case=False) |
        df[company_col].astype(str).str.contains(search, case=False)
    ]

# Timestamp
st.caption(f"⏱️ Data as of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Top trades summary
st.subheader("🔥 Top 5 Insider Purchases")
top_trades = df.sort_values(by="Value", ascending=False).head(5)

for idx, row in top_trades.iterrows():
    st.markdown(f"""
    <div style="border:1px solid #eee; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; background-color: #fafafa;">
        <strong>{row['Company'] if 'Company' in row else row.get('Company Name', 'N/A')} ({row['Ticker']})</strong><br>
        <span style="color:gray;">{row['Insider Name']}, {row['Title']}</span><br>
        💰 <strong>{row['Trade Type']}</strong> — {row['Qty']} shares @ ${row['Price']}<br>
        📦 <strong>Total Value:</strong> ${row['Value']}<br>
        🧾 Filed: {row['Filing Date']} | Traded: {row['Trade Date']}
    </div>
    """, unsafe_allow_html=True)

# Expandable full table
with st.expander("📄 View Full Insider Trade Table"):
    st.dataframe(df, use_container_width=True)

# CSV Export
st.download_button("📥 Download as CSV", df.to_csv(index=False), "insider_trades.csv")





