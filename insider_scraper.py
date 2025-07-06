import requests
import pandas as pd
from bs4 import BeautifulSoup

class InsiderScraper:
    def __init__(self, min_transaction_value=0, min_shares=0):
        self.base_url = "http://openinsider.com"
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self, lookback_days=5) -> pd.DataFrame:
        url = (
            f"{self.base_url}/screener?s=&o=&pl=&ph=&ll=&lh=&fd={lookback_days}&td=0"
            f"&sic1=&sic2=&t=&ql=&qh=&o1=0&o2=0&nop=50"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("DEBUG: Request failed with status:", response.status_code)
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", class_="tinytable")

        if table is None:
            print("DEBUG: Data table not found on OpenInsider page.")
            return pd.DataFrame()

        headers = [th.get_text(strip=True) for th in table.find_all("th") if th.get_text(strip=True)]
        data = []

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            row_data = [td.get_text(strip=True) for td in cols]
            if len(row_data) == len(headers):
                data.append(row_data)

        if not data:
            print("DEBUG: Table found, but no matching data rows.")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=headers)
        df = self.clean_data(df)
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        value_col = next((col for col in df.columns if "Value" in col), None)
        qty_col = next((col for col in df.columns if "Qty" in col or "Shares" in col), None)

        if not value_col or not qty_col:
            print("DEBUG: Missing required columns for filtering.")
            return df

        try:
            df[value_col] = df[value_col].replace('[\$,]', '', regex=True).astype(float)
            df[qty_col] = df[qty_col].str.replace(",", "").astype(float)
            df = df[df[value_col] >= self.min_transaction_value]
            df = df[df[qty_col] >= self.min_shares]
        except Exception as e:
            print("DEBUG: Error cleaning data:", e)

        return df.reset_index(drop=True)






