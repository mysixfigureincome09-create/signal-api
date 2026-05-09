from flask import Flask, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import os
import time
import threading

app = Flask(__name__)

TICKERS = ["NVDA", "TSLA", "AMD", "PLTR"]

CACHE = {
    "prices": {},
    "portfolio": {
        "cash": 10000,
        "positions": {},
        "trades": []
    }
}

# -----------------------------
# INDICATORS
# -----------------------------

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def volatility(series):
    return series.pct_change().rolling(10).std()


def momentum(series):
    return series.pct_change().rolling(5).mean()


# -----------------------------
# SIGNAL ENGINE (FUSION)
# -----------------------------

def generate_signal(df):
    df = df.copy()

    df["rsi"] = rsi(df["Close"])
    df["vol"] = volatility(df["Close"])
    df["mom"] = momentum(df["Close"])

    rsi_val = df["rsi"].iloc[-1]
    mom_val = df["mom"].iloc[-1]
    vol_val = df["vol"].iloc[-1]

    score = (mom_val * 100) - (rsi_val - 50) * 0.5

    confidence = min(100, abs(score) * 5)

    if mom_val > 0 and rsi_val < 70:
        signal = "BUY"
    elif mom_val < 0 or rsi_val > 75:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, confidence, score


# -----------------------------
# DATA FETCH
# -----------------------------

def fetch(symbol):
    df = yf.download(symbol, period="5d", interval="15m")
    df = df.dropna()

    signal, confidence, score = generate_signal(df)

    price = float(df["Close"].iloc[-1])

    candles = [
        {
            "time": int(row.Index.timestamp()),
            "open": float(row.Open),
            "high": float(row.High),
            "low": float(row.Low),
            "close": float(row.Close)
        }
        for row in df.itertuples()
    ]

    return {
        "ticker": symbol,
        "price": price,
        "signal": signal,
        "confidence": round(confidence, 2),
        "score": round(score, 4),
        "candles": candles
    }


# -----------------------------
# PAPER TRADING ENGINE
# -----------------------------

def execute_trade(symbol, signal, price, confidence):

    portfolio = CACHE["portfolio"]

    position_size = (portfolio["cash"] * (confidence / 100)) * 0.1

    if signal == "BUY" and portfolio["cash"] > position_size:

        qty = position_size / price

        portfolio["cash"] -= position_size

        portfolio["positions"][symbol] = portfolio["positions"].get(symbol, 0) + qty

        portfolio["trades"].append({
            "type": "BUY",
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "time": time.time()
        })

    elif signal == "SELL" and symbol in portfolio["positions"]:

        qty = portfolio["positions"][symbol]

        proceeds = qty * price

        portfolio["cash"] += proceeds

        del portfolio["positions"][symbol]

        portfolio["trades"].append({
            "type": "SELL",
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "time": time.time()
        })


# -----------------------------
# LIVE UPDATE LOOP
# -----------------------------

def update_loop():

    while True:

        for t in TICKERS:

            data = fetch(t)

            CACHE["prices"][t] = data

            execute_trade(
                t,
                data["signal"],
                data["price"],
                data["confidence"]
            )

        time.sleep(30)


threading.Thread(target=update_loop, daemon=True).start()


# -----------------------------
# API ROUTES
# -----------------------------

@app.route("/")
def dashboard():
    return jsonify(CACHE["prices"])


@app.route("/portfolio")
def portfolio():
    return jsonify(CACHE["portfolio"])


@app.route("/health")
def health():
    return jsonify({"status": "running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
