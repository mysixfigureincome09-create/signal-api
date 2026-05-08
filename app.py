from flask import Flask, jsonify
import requests
import pandas as pd

app = Flask(__name__)

TICKERS = ["SNDL","MULN","BBIG","ATER","OCGN","SOFI","PLTR","AMD","NVDA"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=3mo&interval=1d"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        result = data["chart"]["result"][0]
        close = result["indicators"]["quote"][0]["close"]
        volume = result["indicators"]["quote"][0]["volume"]

        df = pd.DataFrame({"close": close, "volume": volume}).dropna()
        return df

    except:
        return None


def score(df):
    close = df["close"]

    sma5 = close.rolling(5).mean().iloc[-1]
    sma10 = close.rolling(10).mean().iloc[-1]
    sma20 = close.rolling(20).mean().iloc[-1]

    score = 50

    if sma5 > sma10 > sma20:
        score += 25
    else:
        score -= 15

    momentum = (sma5 - sma20) / sma20
    score += momentum * 100

    score = max(0, min(100, score))

    if score >= 72:
        signal = "BUY"
    elif score <= 40:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, round(score, 2)


@app.route("/signals")
def signals():

    results = []

    for t in TICKERS:
        df = fetch(t)

        if df is None or len(df) < 25:
            continue

        sig, sc = score(df)

        results.append({
            "ticker": t,
            "signal": sig,
            "score": sc,
            "price": float(df["close"].iloc[-1])
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify(results)


@app.route("/")
def home():
    return "Signal API running"


if __name__ == "__main__":
    app.run()
