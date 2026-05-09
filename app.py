from flask import Flask, render_template, jsonify
import requests
import threading
import time
import math
import os
import logging

app = Flask(__name__)

# ----------------------------
# CONFIG
# ----------------------------
API_URL = "https://signal-api-cp14.onrender.com/signals"
CACHE_TTL = 30  # seconds

# ----------------------------
# LOGGING
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------------------
# GLOBAL CACHE
# ----------------------------
CACHE = {
    "data": [],
    "last_update": 0
}

cache_lock = threading.Lock()

# Prevent duplicate threads
thread_started = False


# ----------------------------
# SIGNAL ENGINE
# ----------------------------
def compute_signal(stock):
    try:
        price = float(stock.get("price", 0) or 0)
        score = float(stock.get("score", 0) or 0)
        volume = float(stock.get("volume", 0) or 0)

        # Momentum formula
        momentum = score * (1 + math.log1p(max(volume, 0)))

        # Risk levels
        if price < 1:
            risk = "HIGH"
        elif price < 10:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        # Confidence score
        confidence = max(0, min(100, abs(momentum)))

        # Trading signal
        if momentum > 0 and confidence >= 70:
            signal = "BUY"
        elif momentum < 0 and confidence >= 70:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "ticker": stock.get("ticker", "UNKNOWN"),
            "price": round(price, 4),
            "score": round(score, 2),
            "volume": int(volume),
            "momentum": round(momentum, 2),
            "confidence": round(confidence, 1),
            "risk": risk,
            "signal": signal
        }

    except Exception as e:
        logging.error(f"Signal compute error: {e}")

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


# ----------------------------
# FETCH SIGNALS
# ----------------------------
def fetch_signals():
    try:
        logging.info(f"Fetching signals from {API_URL}")

        response = requests.get(API_URL, timeout=20)

        if response.status_code != 200:
            logging.error(
                f"API error {response.status_code}: {response.text}"
            )
            return []

        try:
            data = response.json()
        except Exception:
            logging.error("Invalid JSON response")
            logging.error(response.text)
            return []

        # Normalize response
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            logging.error("API did not return a list")
            return []

        processed = []

        for item in data:
            if isinstance(item, dict):
                processed.append(compute_signal(item))

        logging.info(f"Loaded {len(processed)} signals")

        return processed

    except requests.exceptions.Timeout:
        logging.error("Request timeout")
        return []

    except requests.exceptions.ConnectionError:
        logging.error("Connection error")
        return []

    except Exception as e:
        logging.error(f"Fetch error: {e}")
        return []


# ----------------------------
# CACHE REFRESH LOOP
# ----------------------------
def refresh_cache():
    while True:
        try:
            logging.info("Refreshing signal cache...")

            fresh_data = fetch_signals()

            with cache_lock:
                CACHE["data"] = fresh_data
                CACHE["last_update"] = time.time()

            logging.info("Cache updated")

        except Exception as e:
            logging.error(f"Cache refresh error: {e}")

        time.sleep(CACHE_TTL)


# ----------------------------
# START BACKGROUND THREAD
# ----------------------------
def start_background_thread():
    global thread_started

    if not thread_started:
        thread = threading.Thread(
            target=refresh_cache,
            daemon=True
        )

        thread.start()

        thread_started = True

        logging.info("Background cache thread started")


# Start once
start_background_thread()

# Initial preload
with cache_lock:
    CACHE["data"] = fetch_signals()
    CACHE["last_update"] = time.time()


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def dashboard():
    with cache_lock:
        data = list(CACHE["data"])

    sorted_data = sorted(
        data,
        key=lambda x: x.get("momentum", 0),
        reverse=True
    )

    return render_template(
        "index.html",
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


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
