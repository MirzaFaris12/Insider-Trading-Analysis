import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

class SECForm4Fetcher:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {"User-Agent": "InsiderTradingTracker/1.0 contact@example.com"}  # Replace with real contact

    def get_cik_from_ticker(self, ticker):
        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            for entry in data:
                if entry["ticker"].lower() == ticker.lower():
                    return str(entry["cik"]).zfill(10)
                    
        except Exception as e:
            print("DEBUG: Failed to fetch CIK", e)
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
        ns = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}

        records = []

        for report in root.findall("reportingOwner"):  # Simplified for early version
            try:
                name = report.find("reportingOwnerId/rptOwnerName").text
            except:
                name = ""

        for txn in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
            try:
                security = txn.find("securityTitle/value").text
                date = txn.find("transactionDate/value").text
                code = txn.find("transactionCoding/transactionCode").text
                shares = txn.find("transactionAmounts/transactionShares/value").text
                price = txn.find("transactionAmounts/transactionPricePerShare/value").text
                records.append({
                    "Insider Name": name,
                    "Security": security,
                    "Date": date,
                    "Type": code,
                    "Shares": float(shares),
                    "Price": float(price)
                })
            except Exception as e:
                continue

        return pd.DataFrame(records)

# Example usage
# fetcher = SECForm4Fetcher()
# filings = fetcher.get_company_filings("320193")  # AAPL CIK
# df = fetcher.parse_form4("320193", filings[0]['accession'])
# print(df)
