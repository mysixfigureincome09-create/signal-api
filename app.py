import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob

TICKERS = ["NVDA", "TSLA", "AMD", "PLTR", "AAPL", "MSFT"]


# -------------------------
# INDICATORS
# -------------------------

def rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def candle_strength(df):
    body = abs(df["Close"] - df["Open"])
    range_ = df["High"] - df["Low"]
    return body / (range_ + 1e-9)


def momentum(df):
    return df["Close"].pct_change().rolling(5).mean()


# -------------------------
# SENTIMENT (SIMULATED AI SCRAPING LAYER)
# -------------------------

def sentiment_score(ticker):
    # placeholder for real news scraping
    # replace with news API later
    fake_news = f"{ticker} earnings growth strong outlook positive"
    return TextBlob(fake_news).sentiment.polarity


# -------------------------
# SIGNAL ENGINE
# -------------------------

def analyze(df, ticker):

    df = df.copy()

    df["rsi"] = rsi(df)
    df["mom"] = momentum(df)
    df["candle"] = candle_strength(df)

    rsi_val = df["rsi"].iloc[-1]
    mom_val = df["mom"].iloc[-1]
    candle_val = df["candle"].iloc[-1]
    price = df["Close"].iloc[-1]

    sentiment = sentiment_score(ticker)

    # -------------------------
    # SCORE MODEL (RISK + RETURN)
    # -------------------------

    score = (
        (mom_val * 120) +
        (sentiment * 50) +
        (candle_val * 80)
    ) - (rsi_val - 50) * 0.8

    confidence = min(100, abs(score))

    # -------------------------
    # SIGNAL LOGIC
    # -------------------------

    if mom_val > 0 and rsi_val < 70 and sentiment > 0:
        signal = "BUY"

    elif rsi_val > 75 or mom_val < 0:
        signal = "SELL"

    else:
        signal = "HOLD"

    # -------------------------
    # RISK FILTER
    # -------------------------

    risk = "LOW"

    if rsi_val > 80:
        risk = "HIGH"
    elif candle_val > 0.7:
        risk = "MEDIUM"

    return {
        "ticker": ticker,
        "price": float(price),
        "signal": signal,
        "confidence": round(confidence, 2),
        "risk": risk,
        "sentiment": round(sentiment, 3),
        "score": round(score, 3)
    }


# -------------------------
# DATA FETCH
# -------------------------

def get_stock(ticker):

    df = yf.download(ticker, period="5d", interval="15m")
    df = df.dropna()

    return analyze(df, ticker)


def rank_stocks():

    results = [get_stock(t) for t in TICKERS]

    # risk-adjusted ranking
    ranked = sorted(
        results,
        key=lambda x: x["confidence"] / (1 + (1 if x["risk"] == "HIGH" else 0)),
        reverse=True
    )

    return ranked
