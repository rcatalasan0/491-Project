from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

# ML imports
from mlSkeletons.stockFunctions import stockData_days, stockData_summary
from mlSkeletons.randomForestRegression import random_forest_regression_operations

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Allow Destinate (React) dev server
CORS(app, resources={r"/*": {"origins": ["http://localhost:5002"]}})

# =========================================================
# HTML PAGES (served by Flask)
# =========================================================

@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")

@app.route("/prediction-tool")
def prediction_tool():
    return send_from_directory(".", "prediction-tool.html")

# Serve CSS / JS / images
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# =========================================================
# API ENDPOINTS
# =========================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/stocks")
def get_stocks():
    stocks = [
        {"symbol": "LMT", "name": "Lockheed Martin Corporation", "sector": "defense"},
        {"symbol": "RTX", "name": "Raytheon Technologies Corporation", "sector": "defense"},
        {"symbol": "BA", "name": "The Boeing Company", "sector": "defense"},
        {"symbol": "NOC", "name": "Northrop Grumman Corporation", "sector": "defense"},
        {"symbol": "GD", "name": "General Dynamics Corporation", "sector": "defense"},
    ]
    return jsonify({"stocks": stocks, "count": len(stocks)})

@app.route("/predict")
def predict():
    ticker = (request.args.get("ticker") or "").upper().strip()
    days = request.args.get("days", "7")

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    try:
        days = int(days)
        if not (1 <= days <= 30):
            return jsonify({"error": "days must be between 1 and 30"}), 400
    except ValueError:
        return jsonify({"error": "days must be an integer"}), 400

    if not ticker.isalnum() or len(ticker) > 10:
        return jsonify({"error": "invalid ticker"}), 400

    try:
        raw = stockData_days(days, ticker)
        if raw.empty:
            return jsonify({"error": "no data found"}), 404

        summary = stockData_summary(raw)
        hist = summary[["AveragePrice"]].reset_index()
        hist["date"] = hist["Date"].dt.strftime("%Y-%m-%d")
        hist["predicted_price"] = hist["AveragePrice"].round(2)
        predictions = hist[["date", "predicted_price"]].to_dict(orient="records")
    except Exception as e:
        return jsonify({"error": f"data fetch failed: {e}"}), 500

    try:
        next_price = random_forest_regression_operations(ticker, years=5)
    except Exception as e:
        return jsonify({"error": f"ML prediction failed: {e}"}), 500

    last_date = hist["Date"].iloc[-1]
    next_day = last_date + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    predictions.append({
        "date": next_day.strftime("%Y-%m-%d"),
        "predicted_price": round(next_price, 2),
        "day": len(predictions) + 1
    })

    for i, p in enumerate(predictions):
        p["day"] = i + 1

    return jsonify({
        "ticker": ticker,
        "model": "RandomForest-1day",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "predictions": predictions
    })

# =========================================================
# SERVER START
# =========================================================

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000

    print("=" * 60)
    print("Stock Predictor Flask Server")
    print("=" * 60)
    print(f"Login Page:       http://{host}:{port}/login")
    print(f"Prediction Tool:  http://{host}:{port}/prediction-tool")
    print(f"Health Check:     http://{host}:{port}/health")
    print("=" * 60)

    app.run(host=host, port=port, debug=True)
