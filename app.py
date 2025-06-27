import streamlit as st
from insider_scraper import InsiderScraper

st.set_page_config(page_title="Insider Trading Tracker", layout="wide")
st.title("📊 Insider Trading Tracker")
st.markdown("Fetch recent insider trades using data from OpenInsider.")

scraper = InsiderScraper()
with st.spinner("Fetching insider trading data..."):
    df = scraper.fetch()

# Filters
search = st.text_input("Search by Company or Ticker:")
if search:
    df = df[df["Ticker"].str.contains(search, case=False) | df["Company"].str.contains(search, case=False)]

st.dataframe(df)
st.download_button("📥 Download CSV", df.to_csv(index=False), "insider_trades.csv")
