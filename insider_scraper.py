import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class InsiderScraper:
    def __init__(self, min_transaction_value=10000, min_shares=1000):
        self.url = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=1&td=0&sic1=&sic2=&t=&ql=&qh=&o1=0&o2=0&nop=50"
        self.min_transaction_value = min_transaction_value
        self.min_shares = min_shares

    def fetch(self) -> pd.DataFrame:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"class": "tinytable"})
        headers = [th.text.strip() for th in table.find_all("th")]

        data = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue
            record = [td.text.strip() for td in cols]
            data.append(record)

        df = pd.DataFrame(data, columns=headers)
        df = self.clean_data(df)
        return df

    def clean_data(self, df):
        df["Value ($)"] = df["Value ($)"].replace('[\$,]', '', regex=True).astype(float)
        df["Qty"] = df["Qty"].str.replace(",", "").astype(float)
        df = df[df["Value ($)"] >= self.min_transaction_value]
        df = df[df["Qty"] >= self.min_shares]
        return df.reset_index(drop=True)
