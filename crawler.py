import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== HNX ====
def crawl_hnx():
    URL_HNX = "https://hnx.vn/ModuleReportStockETFs/Report_Stock_ETFs_ListStocks/SearchForChungKhoanKhongKyQuy_Listed"
    HEADERS_HNX = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    def get_page(page):
        payload = {
            "p_keysearch": "",
            "pColOrder": "STOCK_CODE",
            "pOrderType": "ASC",
            "pCurrentPage": page,
            "pRecordOnPage": 50,
            "pIsSearch": 0
        }
        r = requests.post(URL_HNX, headers=HEADERS_HNX, data=payload, verify=False)
        r.encoding = "utf-8"
        return r.text

    def parse_table(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "_tableDatas"})
        if not table:
            return []
        rows = table.find("tbody").find_all("tr")
        data = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            data.append(cols)
        return data

    all_data = []
    page = 1
    while True:
        html = get_page(page)
        data = parse_table(html)
        if not data:
            break
        all_data.extend(data)
        page += 1
        time.sleep(0.3)

    df = pd.DataFrame(all_data, columns=["STT", "Ticker", "Full_name", "Date", "Reason"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True).dt.date
    df = df[["Ticker", "Full_name", "Date", "Reason"]]
    df["Source"] = "HNX"
    return df

# ==== HOSE ====
def crawl_hose():
    BASE_URL = "https://api.hsx.vn/l/api/v1/1/securities/margin-trade"
    HEADERS = {"User-Agent": "Mozilla/5.0"}
    MAX_STOCKS = 300
    PAGE_SIZE = 40

    def ts_to_date(ts):
        try:
            return datetime.utcfromtimestamp(ts).date()
        except:
            return None

    def fetch_all():
        page = 1
        all_items = []
        while True:
            params = {"pageIndex": page, "pageSize": PAGE_SIZE}
            resp = requests.get(BASE_URL, headers=HEADERS, params=params, verify=False)
            if resp.status_code != 200:
                break
            data = resp.json().get("data", {}).get("list", [])
            if not data:
                break
            all_items.extend(data)
            if len(all_items) >= MAX_STOCKS:
                break
            page += 1
            time.sleep(0.2)
        return all_items

    items = fetch_all()
    data = []
    for it in items:
        data.append({
            "Ticker": it.get("securitiesCode"),
            "Full_name": it.get("name"),
            "Date": ts_to_date(it.get("datePublish")),
            "Reason": it.get("reason")
        })

    df = pd.DataFrame(data)
    df["Source"] = "HOSE"
    return df
