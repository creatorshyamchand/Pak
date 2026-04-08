import os
import re
import time
import json
import requests
from flask import Flask, request, Response
from bs4 import BeautifulSoup

app = Flask(__name__)

# -------------------------
# Config
# -------------------------
TARGET_BASE = "https://pakistandatabase.com"
TARGET_PATH = "/databases/sim.php"
MIN_INTERVAL = 1.0
LAST_CALL = {"ts": 0.0}

COPYRIGHT_HANDLE = "@nexxonhackers"
DEVELOPER_NAME = "CREATOR SHYAMCHAND"
DISCLAIMER = f"This is Developed by {DEVELOPER_NAME} Only For Educational Purposes. Don't mis-use it."

# -------------------------
# Helpers
# -------------------------
def is_mobile(value: str) -> bool:
    return bool(re.fullmatch(r"92\d{9,12}", (value or "").strip()))

def is_cnic(value: str) -> bool:
    return bool(re.fullmatch(r"\d{13}", (value or "").strip()))

def classify_query(value: str):
    v = value.strip()
    if is_mobile(v): return "mobile", v
    if is_cnic(v): return "cnic", v
    raise ValueError("Invalid query. Use mobile with country code (92...) or CNIC (13 digits).")

def fetch_upstream(query_value: str):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": TARGET_BASE + "/",
    }
    url = TARGET_BASE + TARGET_PATH
    data = {"search_query": query_value}
    resp = session.post(url, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_table(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table: return []
    tbody = table.find("tbody")
    if not tbody: return []
    results = []
    for tr in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) >= 3:
            results.append({
                "mobile": cols[0],
                "name": cols[1],
                "cnic": cols[2],
                "address": cols[3] if len(cols) > 3 else "",
            })
    return results

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return {
        "api_name": "Pakistan Number Info API",
        "developer": DEVELOPER_NAME,
        "handle": COPYRIGHT_HANDLE,
        "disclaimer": DISCLAIMER,
        "status": "Running on Vercel"
    }

@app.route("/api/lookup", methods=["GET", "POST"])
def api_lookup():
    q = ""
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        q = data.get("query")
    else:
        q = request.args.get("query")

    if not q:
        return {"error": "Query parameter is missing"}, 400

    try:
        qtype, normalized = classify_query(q)
        html = fetch_upstream(normalized)
        results = parse_table(html)
        return {
            "status": "success",
            "query": normalized,
            "results": results,
            "credits": {
                "handle": COPYRIGHT_HANDLE,
                "developer": DEVELOPER_NAME,
                "disclaimer": DISCLAIMER
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

# Vercel এর জন্য এটি প্রয়োজন
def handler(event, context):
    return app(event, context)
