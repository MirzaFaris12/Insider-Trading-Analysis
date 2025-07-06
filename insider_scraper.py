import requests
import pandas as pd
from bs4 import BeautifulSoup

class InsiderScraper:
    def __init__(self, min_transaction_value=0, min_shares=0, lookback_days=30):
        self.base_url = "http://openinsider.com"
        self.url = f"{self.base_url}/screener?fd={lookback_days}&td=0&nop=100"
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self) -> pd.DataFrame:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(self.url, headers=headers)

        print("DEBUG: Fetching URL:", self.url)
        print("DEBUG: Status code:", response.status_code)

        if response.status_code != 200:
            print("ERROR: Failed to fetch the page")
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        if table is None:
            print("ERROR: No table found on page")
            print(soup.prettify()[:1000])
            return pd.DataFrame()

        headers = [th.get_text(strip=True) for th in table.find_all("th") if th.get_text(strip=True)]
        print("DEBUG: Table headers:", headers)

        data = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            row_data = [td.get_text(strip=True) for td in cols]
            print("DEBUG: Row data:", row_data)
            if len(row_data) == len(headers):
                data.append(row_data)
            else:
                print("WARNING: Row skipped due to column mismatch")

        if not data:
            print("ERROR: No valid rows found in table")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=headers)
        df = self.clean_data(df)
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        value_col = next((col for col in df.columns if "Value" in col), None)
        qty_col = next((col for col in df.columns if "Qty" in col or "Shares" in col), None)

        if not value_col or not qty_col:
            print("WARNING: Required columns not found for filtering")
            return df

        print(f"DEBUG: Filtering rows with value >= {self.min_transaction_value} and qty >= {self.min_shares}")

        try:
            df[value_col] = df[value_col].replace('[\\$,]', '', regex=True).astype(float)
            df[qty_col] = df[qty_col].str.replace(",", "").astype(float)
            before_filter = len(df)
            df = df[df[value_col] >= self.min_transaction_value]
            df = df[df[qty_col] >= self.min_shares]
            after_filter = len(df)
            print(f"DEBUG: Rows before filter: {before_filter}, after filter: {after_filter}")
        except Exception as e:
            print("ERROR: Exception during data cleaning:", e)

        return df.reset_index(drop=True)





