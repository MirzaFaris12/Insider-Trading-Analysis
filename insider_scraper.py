import requests
import pandas as pd
from bs4 import BeautifulSoup

class InsiderScraper:
    def __init__(self, min_transaction_value=0, min_shares=0):
        self.base_url = "http://openinsider.com"
        self.url = f"{self.base_url}/screener?s=&o=&pl=&ph=&ll=&lh=&fd=1&td=0&sic1=&sic2=&t=&ql=&qh=&o1=0&o2=0&nop=50"
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self) -> pd.DataFrame:
        response = requests.get(self.url)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to fetch data from OpenInsider: {response.status_code}")

        soup = BeautifulSoup(response.content, "html.parser")
    
        # Try known table class
        table = soup.find("table", {"class": "tinytable"})
    
        # Try fallback method if main table not found
        if not table:
            tables = soup.find_all("table")
            for t in tables:
                if "Filing Date" in t.text and "Trade Date" in t.text:
                    table = t
                    break

        if not table:
            raise ValueError("Could not find data table on OpenInsider.")

        headers = [th.text.strip() for th in table.find_all("th")]
        data = []

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue

        record = [td.text.strip() for td in cols]

        # Extract Form 4 link from <a> in first column
        a_tag = cols[0].find("a")
        form4_link = f"{self.base_url}{a_tag['href']}" if a_tag and 'href' in a_tag.attrs else None
        record.append(form4_link)

        data.append(record)

        headers.append("Form 4 Link")
        df = pd.DataFrame(data, columns=headers)
        return self.clean_data(df)


    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        value_col = next((col for col in df.columns if "Value" in col), None)
        qty_col = next((col for col in df.columns if "Qty" in col or "Shares" in col), None)

        if not value_col or not qty_col:
            print("DEBUG: Column names not found.")
            return df

        try:
            df[value_col] = df[value_col].replace('[\\$,]', '', regex=True).astype(float)
            df[qty_col] = df[qty_col].str.replace(",", "").astype(float)
            df = df[df[value_col] >= self.min_transaction_value]
            df = df[df[qty_col] >= self.min_shares]
        except Exception as e:
            print("DEBUG: Error cleaning data:", e)

        return df.reset_index(drop=True)



