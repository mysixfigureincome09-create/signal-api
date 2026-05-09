from flask import Flask, jsonify, render_template_string
import requests
import threading
import time
import math
import os
import logging

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================

# CHANGE THIS TO YOUR API URL
API_URL = "https://signal-api-cp14.onrender.com"

CACHE_TTL = 30

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =====================================================
# CACHE
# =====================================================

CACHE = {
    "data": [],
    "last_update": 0
}

cache_lock = threading.Lock()

# =====================================================
# HTML TEMPLATE
# =====================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Dashboard</title>

    <meta http-equiv="refresh" content="30">

    <style>
        body{
            background:#0f172a;
            color:white;
            font-family:Arial;
            padding:20px;
        }

        h1{
            color:#38bdf8;
        }

        .card{
            background:#1e293b;
            padding:20px;
            margin-bottom:15px;
            border-radius:10px;
            border:1px solid #334155;
        }

        .buy{
            color:#22c55e;
            font-weight:bold;
        }

        .sell{
            color:#ef4444;
            font-weight:bold;
        }

        .hold{
            color:#facc15;
            font-weight:bold;
        }

        .small{
            color:#94a3b8;
            font-size:12px;
        }
    </style>
</head>

<body>

<h1>📈 AI Trading Dashboard</h1>

<p class="small">
Auto-refresh every 30 seconds
</p>

{% if stocks %}

    {% for stock in stocks %}

    <div class="card">

        <h2>{{ stock.ticker }}</h2>

        <p>Price: ${{ stock.price }}</p>

        <p>Momentum: {{ stock.momentum }}</p>

        <p>Confidence: {{ stock.confidence }}%</p>

        <p>Risk: {{ stock.risk }}</p>

        <p>
            Signal:

            {% if stock.signal == "BUY" %}
                <span class="buy">BUY</span>
            {% elif stock.signal == "SELL" %}
                <span class="sell">SELL</span>
            {% else %}
                <span class="hold">HOLD</span>
            {% endif %}
        </p>

    </div>

    {% endfor %}

{% else %}

    <div class="card">
        <h2>No Data Available</h2>

        <p>
        Your API may be offline or returning invalid JSON.
        </p>
    </div>

{% endif %}

</body>
</html>
"""

# =====================================================
# SIGNAL ENGINE
# =====================================================

def compute_signal(stock):
    try:

        ticker = stock.get("ticker", "UNKNOWN")

        price = float(stock.get("price", 0) or 0)

        score = float(stock.get("score", 0) or 0)

        volume = float(stock.get("volume", 0) or 0)

        momentum = score * (1 + math.log1p(max(volume, 0)))

        confidence = max(0, min(100, abs(momentum)))

        if price < 1:
            risk = "HIGH"
        elif price < 10:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if momentum > 0 and confidence >= 70:
            signal = "BUY"
        elif momentum < 0 and confidence >= 70:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "ticker": ticker,
            "price": round(price, 4),
            "score": round(score, 2),
            "volume": int(volume),
            "momentum": round(momentum, 2),
            "confidence": round(confidence, 1),
            "risk": risk,
            "signal": signal
        }

    except Exception as e:

        logging.error(f"compute_signal error: {e}")

        return {
            "ticker": "ERROR",
            "price": 0,
            "score": 0,
            "volume": 0,
            "momentum": 0,
            "confidence": 0,
            "risk": "HIGH",
            "signal": "HOLD"
        }

# =====================================================
# FETCH API DATA
# =====================================================

def fetch_signals():

    try:

        logging.info(f"Fetching: {API_URL}")

        response = requests.get(API_URL, timeout=20)

        logging.info(f"STATUS CODE: {response.status_code}")

        if response.status_code != 200:

            logging.error(response.text)

            return []

        try:
            data = response.json()

        except Exception:

            logging.error("INVALID JSON RESPONSE")
            logging.error(response.text)

            return []

        logging.info(f"RAW DATA: {data}")

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            logging.error("API did not return list")
            return []

        results = []

        for item in data:

            if isinstance(item, dict):

                processed = compute_signal(item)

                results.append(processed)

        logging.info(f"Loaded {len(results)} stocks")

        return results

    except Exception as e:

        logging.error(f"FETCH ERROR: {e}")

        return []

# =====================================================
# CACHE REFRESH THREAD
# =====================================================

def refresh_cache():

    while True:

        try:

            logging.info("Refreshing cache...")

            fresh_data = fetch_signals()

            with cache_lock:

                CACHE["data"] = fresh_data

                CACHE["last_update"] = time.time()

            logging.info("Cache updated")

        except Exception as e:

            logging.error(f"CACHE ERROR: {e}")

        time.sleep(CACHE_TTL)

# =====================================================
# START THREAD
# =====================================================

thread = threading.Thread(
    target=refresh_cache,
    daemon=True
)

thread.start()

# Initial preload
CACHE["data"] = fetch_signals()
CACHE["last_update"] = time.time()

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def dashboard():

    with cache_lock:

        data = list(CACHE["data"])

    sorted_data = sorted(
        data,
        key=lambda x: x.get("momentum", 0),
        reverse=True
    )

    return render_template_string(
        HTML,
        stocks=sorted_data
    )

@app.route("/api")
def api():

    with cache_lock:

        return jsonify(CACHE["data"])

@app.route("/health")
def health():

    with cache_lock:

        return jsonify({
            "status": "ok",
            "cached_items": len(CACHE["data"]),
            "last_update": CACHE["last_update"]
        })

# =====================================================
# LOCAL TEST DATA
# =====================================================

@app.route("/test")
def test():

    sample = [
        {
            "ticker": "NVDA",
            "price": 120.55,
            "score": 88,
            "volume": 1000000
        },
        {
            "ticker": "TSLA",
            "price": 177.22,
            "score": 72,
            "volume": 2000000
        },
        {
            "ticker": "PLTR",
            "price": 28.12,
            "score": 63,
            "volume": 900000
        }
    ]

    return jsonify(sample)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
