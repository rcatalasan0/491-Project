from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # allows index.html to call this API

@app.get("/predict")
def predict():
    ticker = (request.args.get("ticker") or "").upper()
    days = int(request.args.get("days") or 7)
    if not ticker:
        return jsonify(error="Missing ticker"), 400

    # just a fugazzi
    start_price = 420.0
    preds = []
    today = datetime.utcnow().date()
    for i in range(days):
        preds.append({
            "date": (today + timedelta(days=i+1)).isoformat(),
            "price": round(start_price + i * 1.8, 2)
        })

    return jsonify({
        "ticker": ticker,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "predictions": preds
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
