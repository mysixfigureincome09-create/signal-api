from flask import Flask, render_template
import requests

app = Flask(__name__)

API_URL = "https://signal-api-cp14.onrender.com/signals"


@app.route("/")
def home():
    try:
        stocks = requests.get(API_URL, timeout=10).json()
        if not isinstance(stocks, list):
            stocks = []
    except:
        stocks = []

    return render_template("index.html", stocks=stocks)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
