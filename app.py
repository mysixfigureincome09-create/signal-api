from flask import Flask, jsonify
import random
import os

app = Flask(__name__)

@app.route("/")
def home():

    stocks = [
        {
            "ticker": "NVDA",
            "price": round(random.uniform(100, 140), 2),
            "score": random.randint(60, 95),
            "volume": random.randint(1000000, 5000000)
        },
        {
            "ticker": "TSLA",
            "price": round(random.uniform(150, 250), 2),
            "score": random.randint(50, 90),
            "volume": random.randint(2000000, 7000000)
        },
        {
            "ticker": "PLTR",
            "price": round(random.uniform(20, 40), 2),
            "score": random.randint(40, 85),
            "volume": random.randint(500000, 3000000)
        },
        {
            "ticker": "AMD",
            "price": round(random.uniform(90, 180), 2),
            "score": random.randint(55, 93),
            "volume": random.randint(800000, 4000000)
        }
    ]

    return jsonify(stocks)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
