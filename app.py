
from flask import Flask, render_template, jsonify
import requests
import threading
import time
import math

app = Flask(__name__)

# ----------------------------
# CONFIG
# ----------------------------
API_URL = "https://signal-api-cp14.onrender.com/signals"
CACHE_TTL = 30  # seconds

CACHE = {
    "data": [],
    "last_update": 0
}

# Prevent multiple threads in Gunicorn
thread_started = False


# ----------------------------
# SIGNAL ENGINE (INLINE)
# ----------------------------
def compute_signal(stock):
    try:
        price = float(stock.get("price", 0))
        score = float(stock.get("score", 0))
        volume = float(stock.get("volume", 0))

        momentum = score * (1 + math.log1p(volume))

        if price < 1:
            risk = "HIGH"
        elif price < 10:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        confidence = max(0, min(100, abs(momentum)))

        if confidence > 70 and momentum > 0:
            signal = "BUY"
        elif confidence < 30:
            signal = "HOLD"
        else:
            signal = "HOLD"

        return {
            "ticker": stock.get("ticker", "UNKNOWN"),
            "price": round(price, 4),
            "score": round(score, 2),
            "momentum": round(momentum, 2),
            "confidence": round(confidence, 1),
            "risk": risk,
            "signal": signal
        }

    except Exception:
        return {
            "ticker": "ERROR",
            "price": 0,
            "score": 0,
            "momentum": 0,
            "confidence": 0,
            "risk": "HIGH",
            "signal": "HOLD"
        }


# ----------------------------
# SAFE API FETCH
# ----------------------------
def fetch_signals():
    try:
        r = requests.get(API_URL, timeout=20)

        if r.status_code != 200:
            print("API error:", r.status_code, r.text)
            return []

        try:
            data = r.json()
        except ValueError:
            print("Invalid JSON response:", r.text)
            return []

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return []

        return [compute_signal(x) for x in data]

    except Exception as e:
        print("Fetch error:", e)
        return []


# ----------------------------
# BACKGROUND CACHE WORKER
# ----------------------------
def refresh_cache():
    while True:
        print("Refreshing signal cache...")
        CACHE["data"] = fetch_signals()
        CACHE["last_update"] = time.time()
        time.sleep(CACHE_TTL)


# ----------------------------
# START THREAD SAFELY
# ----------------------------
if not thread_started:
    thread = threading.Thread(target=refresh_cache, daemon=True)
    thread.start()
    thread_started = True


# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
def dashboard():
    data = CACHE["data"]
    data.sort(key=lambda x: x.get("momentum", 0), reverse=True)
    return render_template("index.html", stocks=data)


@app.route("/api")
def api():
    return jsonify(CACHE["data"])


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "cached_items": len(CACHE["data"]),
        "last_update": CACHE["last_update"]
    })


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
