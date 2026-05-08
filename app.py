from flask import Flask, render_template, jsonify
import requests
import math

app = Flask(__name__)

API_URL = "https://signal-api-cp14.onrender.com/signals"


# ----------------------------
# SAFE DATA FETCH
# ----------------------------
def fetch_signals():
    try:
        r = requests.get(API_URL, timeout=10)
        data = r.json()

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:
        print("API fetch error:", e)
        return []


# ----------------------------
# INSTITUTIONAL-STYLE ENRICHMENT
# ----------------------------
def enrich_signal(s):
    price = float(s.get("price", 0))
    score = float(s.get("score", 0))
    signal = s.get("signal", "HOLD")

    # ---- Confidence model (scaled score)
    confidence = min(100, max(0, abs(score)))

    # ---- Risk model (simple but effective)
    if price < 1:
        risk = "HIGH"
    elif price < 10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    # ---- Adjust signal quality (stability filter)
    if confidence < 30:
        signal = "HOLD"

    # ---- Institutional-style adjustment
    adjusted_score = score

    if risk == "HIGH":
        adjusted_score *= 0.85  # penalize penny volatility

    if signal == "BUY" and confidence < 40:
        signal = "HOLD"

    if signal == "SELL" and confidence < 40:
        signal = "HOLD"

    return {
        "ticker": s.get("ticker", "UNKNOWN"),
        "price": round(price, 4),
        "score": round(adjusted_score, 2),
        "signal": signal,
        "confidence": round(confidence, 1),
        "risk": risk
    }


# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
def dashboard():
    raw = fetch_signals()
    enriched = [enrich_signal(s) for s in raw]

    # Sort by strongest signal first
    enriched.sort(key=lambda x: x["score"], reverse=True)

    return render_template("index.html", stocks=enriched)


@app.route("/api")
def api():
    raw = fetch_signals()
    enriched = [enrich_signal(s) for s in raw]
    return jsonify(enriched)


@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Trading Dashboard",
        "signals_loaded": len(fetch_signals())
    }


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
