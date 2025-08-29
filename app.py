from flask import Flask, render_template, send_file
from crawler import crawl_hnx, crawl_hose
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import threading
import time

app = Flask(__name__)

df_latest = pd.DataFrame()
prev_tickers = set()

# ========== Hàm crawl và cập nhật cache ==========
def update_data_periodically():
    global df_latest, prev_tickers
    while True:
        try:
            print("⏳ Crawling dữ liệu mới...")
            df_hnx = crawl_hnx()
            df_hose = crawl_hose()
            df_all = pd.concat([df_hnx, df_hose], ignore_index=True)
            df_all = df_all[df_all["Date"] >= datetime.now().date() - timedelta(days=7)]
            df_all = df_all.sort_values(by="Date", ascending=False)
            df_latest = df_all.copy()

            current_tickers = set(df_all["Ticker"])
            new_tickers = current_tickers - prev_tickers
            if new_tickers:
                print(f"🔔 Có {len(new_tickers)} mã mới: {', '.join(sorted(new_tickers))}")
            prev_tickers = current_tickers
        except Exception as e:
            print("❌ Lỗi khi cập nhật dữ liệu:", e)

        time.sleep(5800)  # chờ 30 phút

# ========== Giao diện chính ==========
@app.route("/")
def index():
    global df_latest
    return render_template("index.html", records=df_latest.to_dict(orient="records"))

@app.route("/export")
def export_excel():
    global df_latest
    output = BytesIO()
    df_latest.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="no_margin.xlsx", as_attachment=True)

# ========== Chạy app và luồng cập nhật ==========
if __name__ == "__main__":
    # Crawl lần đầu
    thread = threading.Thread(target=update_data_periodically, daemon=True)
    thread.start()

    app.run(debug=True)
