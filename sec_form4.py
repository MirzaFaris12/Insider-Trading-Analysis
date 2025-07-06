import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

class SECForm4Fetcher:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {"User-Agent": "InsiderTradingTracker/1.0 contact@example.com"}  # Replace with real contact

    def get_cik_from_ticker(self, ticker):
        url = "https://www.sec.gov/include/ticker.txt"
        try:
            resp = requests.get(url, headers=self.headers)
            lines = resp.text.strip().splitlines()
            mapping = dict(line.split() for line in lines if len(line.split()) == 2)

            cik = mapping.get(ticker.lower())
            if cik:
                return cik.zfill(10)
            return None
        
        except Exception as e:
            print("DEBUG: Failed to fetch CIK from ticker.txt:", e)
            return None

    def get_company_filings(self, cik: str, count: int = 10):
        cik = cik.zfill(10)
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            print(f"Failed to fetch data for CIK {cik}")
            return []

        data = r.json()
        form4_filings = [f for f in data.get("filings", {}).get("recent", {}).get("form", []) if f == "4"]
        accession_nums = data.get("filings", {}).get("recent", {}).get("accessionNumber", [])
        filings = []

        for i, form in enumerate(data["filings"]["recent"]["form"]):
            if form == "4":
                acc = accession_nums[i].replace("-", "")
                filings.append({
                    "accession": acc,
                    "form": form,
                    "filed": data["filings"]["recent"]["filingDate"][i]
                })
            if len(filings) >= count:
                break

        return filings

    def parse_form4(self, cik: str, accession: str):
        cik = cik.zfill(10)
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/primary_doc.xml"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            return None

        root = ET.fromstring(r.content)
        records = []

        # Extract reporter name once
        try:
            name = root.findtext(".//reportingOwnerId/rptOwnerName")
        except:
            name = "Unknown"

        # Parse transactions
        for txn in root.findall(".//nonDerivativeTransaction"):
            try:
                security = txn.findtext(".//securityTitle/value", default="")
                date = txn.findtext(".//transactionDate/value", default="")
                code = txn.findtext(".//transactionCoding/transactionCode", default="")
                shares = txn.findtext(".//transactionAmounts/transactionShares/value", default="0")
                price = txn.findtext(".//transactionAmounts/transactionPricePerShare/value", default="0")

                records.append({
                    "Insider Name": name,
                    "Security": security,
                    "Date": date,
                    "Type": code,
                    "Shares": float(shares.replace(",", "")),
                    "Price": float(price.replace(",", ""))
                })
            except Exception as e:
                print("DEBUG: Transaction parse failed:", e)
                continue

        return pd.DataFrame(records)


# Example usage
# fetcher = SECForm4Fetcher()
# filings = fetcher.get_company_filings("320193")  # AAPL CIK
# df = fetcher.parse_form4("320193", filings[0]['accession'])
# print(df)
