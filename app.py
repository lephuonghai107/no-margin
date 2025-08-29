from flask import Flask, render_template, send_file
from crawler import crawl_hnx, crawl_hose
from email_sender import send_email
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

app = Flask(__name__)
prev_tickers = set()
df_latest = pd.DataFrame()

@app.route("/")
def index():
    global df_latest, prev_tickers
    df_hnx = crawl_hnx()
    df_hose = crawl_hose()
    df_all = pd.concat([df_hnx, df_hose], ignore_index=True)
    df_all = df_all[df_all["Date"] >= datetime.now().date() - timedelta(days=7)]
    df_all = df_all.sort_values(by="Date", ascending=False)
    df_latest = df_all.copy()

    current_tickers = set(df_all["Ticker"])
    new_tickers = current_tickers - prev_tickers
    if prev_tickers and new_tickers:
        send_email(new_tickers)
    prev_tickers = current_tickers

    return render_template("index.html", records=df_all.to_dict(orient="records"))

@app.route("/export")
def export_excel():
    global df_latest
    output = BytesIO()
    df_latest.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="no_margin.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
