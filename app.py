from flask import Flask, render_template
import requests

app = Flask(__name__)

API_URL = "https://signal-api-cp14.onrender.com/signals"

@app.route("/")
def home():
    try:
        data = requests.get(API_URL, timeout=10).json()
    except:
        data = []

    return render_template("index.html", stocks=data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
