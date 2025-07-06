import requests
import pandas as pd
import xml.etree.ElementTree as ET

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
            if cik:
                return cik.zfill(10)
            return None
        except Exception as e:
            print("DEBUG: Failed to fetch CIK from ticker.txt:", e)
            return None

    def get_company_filings(self, cik: str, count: int = 10):
        cik = cik.zfill(10)
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        try:
            r = requests.get(url, headers=self.headers)
            if r.status_code != 200:
                print(f"DEBUG: Failed to fetch data for CIK {cik}. Status code: {r.status_code}")
                return []
            data = r.json()
            filings = []
            accession_nums = data.get("filings", {}).get("recent", {}).get("accessionNumber", [])
            forms = data.get("filings", {}).get("recent", {}).get("form", [])
            dates = data.get("filings", {}).get("recent", {}).get("filingDate", [])
            for i, form in enumerate(forms):
                if form == "4":
                    acc = accession_nums[i].replace("-", "")
                    filings.append({
                        "accession": acc,
                        "form": form,
                        "filed": dates[i]
                    })
                if len(filings) >= count:
                    break
            return filings
        except Exception as e:
            print("DEBUG: Exception in get_company_filings:", e)
            return []

    def parse_form4(self, cik: str, accession: str):
        cik = cik.zfill(10)
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/primary_doc.xml"
        try:
            r = requests.get(url, headers=self.headers)
            if r.status_code != 200:
                print(f"⚠️ Could not fetch XML. Status: {r.status_code}")
                return pd.DataFrame()

            try:
                root = ET.fromstring(r.content)
            except ET.ParseError as e:
                print("⚠️ XML parse error:", e)
                return pd.DataFrame()

            print("DEBUG: root tags =", [child.tag for child in root][:5])
            records = []

            # Get reporter name
            name = root.findtext(".//reportingOwnerId/rptOwnerName", default="Unknown")
            print("DEBUG: Reporter name:", name)

            # Get transactions
            non_txns = root.findall(".//nonDerivativeTransaction")
            deriv_txns = root.findall(".//derivativeTransaction")
            print(f"DEBUG: Found {len(non_txns)} non-derivative, {len(deriv_txns)} derivative records")

            for txn in non_txns + deriv_txns:
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

            print("DEBUG: Parsed records count:", len(records))
            return pd.DataFrame(records)
        except Exception as e:
            print("DEBUG: parse_form4 failed completely:", e)
            return pd.DataFrame()



# Example usage
# fetcher = SECForm4Fetcher()
# filings = fetcher.get_company_filings("320193")  # AAPL CIK
# df = fetcher.parse_form4("320193", filings[0]['accession'])
# print(df)
