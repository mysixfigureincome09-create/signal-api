from flask import Flask, render_template, jsonify
import requests
import threading
import time

app = Flask(__name__)

API_URL = "https://signal-api-cp14.onrender.com"

# ----------------------------
# GLOBAL CACHE (IMPORTANT)
# ----------------------------
CACHE = {
    "data": [],
    "last_update": 0
}

CACHE_TTL = 30  # seconds


# ----------------------------
# BACKGROUND REFRESH WORKER
# ----------------------------
def refresh_cache():
    while True:
        try:
            print("Refreshing signal cache...")

            r = requests.get(API_URL, timeout=25)

            if r.status_code == 200:
                data = r.json()

                if isinstance(data, dict):
                    data = [data]

                if isinstance(data, list):
                    CACHE["data"] = data
                    CACHE["last_update"] = time.time()

        except Exception as e:
            print("Cache refresh error:", e)

        time.sleep(CACHE_TTL)


# Start background thread ONCE
threading.Thread(target=refresh_cache, daemon=True).start()


# ----------------------------
# ENRICH FUNCTION (safe + lightweight)
# ----------------------------
def enrich(s):
    try:
        price = float(s.get("price", 0))
        score = float(s.get("score", 0))
        signal = s.get("signal", "HOLD")

        confidence = min(100, max(0, abs(score)))

        if price < 1:
            risk = "HIGH"
        elif price < 10:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if confidence < 30:
            signal = "HOLD"

        return {
            "ticker": s.get("ticker", "UNKNOWN"),
            "price": round(price, 4),
            "score": round(score, 2),
            "signal": signal,
            "confidence": round(confidence, 1),
            "risk": risk
        }

    except:
        return {
            "ticker": "ERROR",
            "price": 0,
            "score": 0,
            "signal": "HOLD",
            "confidence": 0,
            "risk": "HIGH"
        }


# ----------------------------
# INSTANT DASHBOARD (NO WAIT)
# ----------------------------
@app.route("/")
def dashboard():
    data = CACHE["data"]

    enriched = [enrich(s) for s in data]
    enriched.sort(key=lambda x: x["score"], reverse=True)

    return render_template("index.html", stocks=enriched)


# ----------------------------
# API VIEW (FAST CACHE RESPONSE)
# ----------------------------
@app.route("/api")
def api():
    data = CACHE["data"]
    enriched = [enrich(s) for s in data]
    return jsonify(enriched)


# ----------------------------
# HEALTH CHECK
# ----------------------------
@app.route("/health")
def health():
    return {
        "status": "ok",
        "cached_items": len(CACHE["data"]),
        "last_update": CACHE["last_update"]
    }


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
