import requests
import pandas as pd
from bs4 import BeautifulSoup

class InsiderScraper:
    def __init__(self, min_transaction_value=0, min_shares=0, lookback_days=30):
        self.base_url = "http://openinsider.com"
        self.lookback_days = lookback_days
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def build_url(self):
        return f"{self.base_url}/screener?s=&o=&pl=&ph=&ll=&lh=&fd={self.lookback_days}&td=0&sic1=&sic2=&t=&ql=&qh=&o1=0&o2=0&nop=50"

    def fetch(self) -> pd.DataFrame:
        url = self.build_url()
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"DEBUG: Failed to fetch page. Status: {response.status_code}")
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")  # Fallback to first table on the page

        if table is None:
            print("DEBUG: Could not find table in page.")
            return pd.DataFrame()

        headers = [th.get_text(strip=True) for th in table.find_all("th") if th.get_text(strip=True)]
        data = []

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            row_data = [td.get_text(strip=True) for td in cols]
            if len(row_data) == len(headers):
                data.append(row_data)

        if not data:
            print("DEBUG: Table found, but no data rows matched.")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=headers)
        return self.clean_data(df)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        value_col = next((col for col in df.columns if "Value" in col), None)
        qty_col = next((col for col in df.columns if "Qty" in col or "Shares" in col), None)

        if not value_col or not qty_col:
            print("DEBUG: Column names for 'Value' or 'Qty' not found.")
            return df

        try:
            df[value_col] = df[value_col].replace('[\$,]', '', regex=True).astype(float)
            df[qty_col] = df[qty_col].str.replace(",", "").astype(float)
            df = df[df[value_col] >= self.min_transaction_value]
            df = df[df[qty_col] >= self.min_shares]
        except Exception as e:
            print("DEBUG: Error cleaning data:", e)

        return df.reset_index(drop=True)






