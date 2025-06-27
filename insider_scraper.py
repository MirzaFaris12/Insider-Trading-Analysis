import requests
from bs4 import BeautifulSoup
import pandas as pd

class InsiderScraper:
    def __init__(self, min_transaction_value=0, min_shares=0):
        self.base_url = "https://openinsider.com/screener"
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self, ticker: str = "", days_back: int = 5) -> pd.DataFrame:
        params = {
            "s": ticker,
            "o": "",
            "pl": "",
            "ph": "",
            "fd": days_back,
            "td": "0",
            "nop": "200"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Connection error:", e)
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"class": "tinytable"})
        if not table:
            return pd.DataFrame()

        headers = [th.text.strip() for th in table.find_all("th")]
        data = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue
            data.append([td.text.strip() for td in cols])

        df = pd.DataFrame(data, columns=headers)
        return self.clean_data(df)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Value" in df.columns:
            df["Value"] = df["Value"].replace('[\$,]', '', regex=True).replace(',', '', regex=True)
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
            df = df[df["Value"] >= self.min_transaction_value]
        if "Qty" in df.columns:
            df["Qty"] = df["Qty"].replace(",", "", regex=True)
            df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce")
            df = df[df["Qty"] >= self.min_shares]
        return df.reset_index(drop=True)

