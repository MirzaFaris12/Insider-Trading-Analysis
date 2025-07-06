import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re

class SECForm4Fetcher:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {
            "User-Agent": "InsiderTradingTracker/1.0 contact@example.com"  # Replace with real contact
        }

    def get_cik_from_ticker(self, ticker):
        url = "https://www.sec.gov/include/ticker.txt"
        try:
            resp = requests.get(url, headers=self.headers)
            lines = resp.text.strip().splitlines()
            mapping = dict(line.split() for line in lines if len(line.split()) == 2)
            cik = mapping.get(ticker.lower())
            return cik.zfill(10) if cik else None
        except Exception as e:
            print("DEBUG: Failed to fetch CIK:", e)
            return None

    def get_company_filings(self, cik: str, count: int = 10):
        cik = cik.zfill(10)
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            print(f"Failed to fetch data for CIK {cik}")
            return []

        data = r.json()
        accession_nums = data["filings"]["recent"]["accessionNumber"]
        forms = data["filings"]["recent"]["form"]
        dates = data["filings"]["recent"]["filingDate"]

        filings = []
        for i in range(len(forms)):
            if forms[i] == "4":
                acc = accession_nums[i].replace("-", "")
                filings.append({
                    "accession": acc,
                    "form": "4",
                    "filed": dates[i]
                })
            if len(filings) >= count:
                break
        return filings

    def parse_form4(self, cik: str, accession: str):
        cik = cik.zfill(10)
        index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}-index.html"
        r = requests.get(index_url, headers=self.headers)
        if r.status_code != 200:
            print("DEBUG: Failed to load index page")
            return None

        # Search for xml filename in index page
        xml_match = re.search(r'href="(.*?\.xml)"', r.text)
        if not xml_match:
            print("DEBUG: No XML file found in index")
            return None

        xml_filename = xml_match.group(1)
        xml_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{xml_filename}"
        r = requests.get(xml_url, headers=self.headers)
        if r.status_code != 200:
            print("DEBUG: Failed to fetch actual XML file")
            return None

        root = ET.fromstring(r.content)
        records = []

        try:
            name = root.findtext(".//reportingOwnerId/rptOwnerName", default="Unknown")
        except:
            name = "Unknown"

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
                print("DEBUG: Failed parsing a transaction:", e)
                continue

        return pd.DataFrame(records)




# Example usage
# fetcher = SECForm4Fetcher()
# filings = fetcher.get_company_filings("320193")  # AAPL CIK
# df = fetcher.parse_form4("320193", filings[0]['accession'])
# print(df)
