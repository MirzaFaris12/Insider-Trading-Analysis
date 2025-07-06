import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

class InsiderScraper:

    def __init__(self, min_transaction_value=0, min_shares=0, lookback_days=30):
        self.base_url = "http://openinsider.com"
        self.lookback_days = lookback_days
        self.url = (
            f"{self.base_url}/screener?s=&o=&pl=&ph=&ll=&lh="
            f"&fd={self.lookback_days}&td=0&sic1=&sic2=&t=&ql=&qh="
            f"&o1=0&o2=0&nop=50"
        )
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self) -> pd.DataFrame:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        try:
            response = requests.get(self.url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"DEBUG: Failed to fetch page. Status: {response.status_code}")
                return pd.DataFrame()

            soup = BeautifulSoup(response.content, "html.parser")

            if "google_vignette" in response.url or "OpenInsider" not in soup.text:
                print("DEBUG: Interstitial page or bot blocker detected. Try again later.")
                return pd.DataFrame()

            table = soup.find("table")
            if table is None:
                print("DEBUG: Table not found. Printing first 1000 chars of page:\n")
                print(soup.prettify()[:1000])
                return pd.DataFrame()

            headers = [th.get_text(strip=True) for th in table.find_all("th") if th.get_text(strip=True)]
            data = []

            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                row_data = [td.get_text(strip=True) for td in cols]
                if len(row_data) == len(headers):
                    data.append(row_data)

            if not data:
                print("DEBUG: Table found but no data rows matched.")
                return pd.DataFrame()

            df = pd.DataFrame(data, columns=headers)
            df = self.clean_data(df)
            return df

        except Exception as e:
            print(f"DEBUG: Exception occurred during fetch: {e}")
            return pd.DataFrame()

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        value_col = next((col for col in df.columns if "Value" in col), None)
        qty_col = next((col for col in df.columns if "Qty" in col or "Shares" in col), None)

        if not value_col or not qty_col:
            print("DEBUG: Column names not found for Value or Qty.")
            return df

        try:
            df[value_col] = df[value_col].replace('[\$,]', '', regex=True).astype(float)
            df[qty_col] = df[qty_col].str.replace(",", "").astype(float)
            df = df[df[value_col] >= self.min_transaction_value]
            df = df[df[qty_col] >= self.min_shares]
        except Exception as e:
            print("DEBUG: Error cleaning data:", e)

        return df.reset_index(drop=True)






