from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/predict")
def predict():
    """Stock prediction endpoint"""
    ticker = (request.args.get("ticker") or "").upper().strip()
    days = request.args.get("days", "7")
    
    # Validation
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400
    
    try:
        days = int(days)
        if days < 1 or days > 30:
            return jsonify({"error": "days must be between 1 and 30"}), 400
    except ValueError:
        return jsonify({"error": "days must be an integer"}), 400
    
    # Validate ticker format
    if not ticker.isalnum() or len(ticker) > 10:
        return jsonify({"error": "ticker must be alphanumeric and <= 10 characters"}), 400
    
    # Demo data for supported tickers
    demo_data = {
        "LMT": {"base": 429.85, "trend": 0.8},
        "RTX": {"base": 114.90, "trend": 0.5},
        "BA": {"base": 180.35, "trend": 0.9},
        "NOC": {"base": 450.00, "trend": 0.7},
        "GD": {"base": 246.50, "trend": 0.6},
    }
    
    if ticker not in demo_data:
        return jsonify({"error": f"Ticker '{ticker}' not available in demo data"}), 404
    
    # Generate predictions
    base_price = demo_data[ticker]["base"]
    trend = demo_data[ticker]["trend"]
    
    predictions = []
    today = datetime.utcnow().date()
    
    for i in range(days):
        day_num = i + 1
        predicted_price = round(base_price + (day_num * trend), 2)
        predictions.append({
            "day": day_num,
            "date": (today + timedelta(days=day_num)).isoformat(),
            "predicted_price": predicted_price
        })
    
    return jsonify({
        "ticker": ticker,
        "days": days,
        "model": "baseline-linear-demo",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "predictions": predictions
    })

@app.route("/stocks")
def get_stocks():
    """Get list of available stocks"""
    stocks = [
        {"symbol": "LMT", "name": "Lockheed Martin Corporation", "sector": "defense"},
        {"symbol": "RTX", "name": "Raytheon Technologies Corporation", "sector": "defense"},
        {"symbol": "BA", "name": "The Boeing Company", "sector": "defense"},
        {"symbol": "NOC", "name": "Northrop Grumman Corporation", "sector": "defense"},
        {"symbol": "GD", "name": "General Dynamics Corporation", "sector": "defense"},
    ]
    
    return jsonify({
        "stocks": stocks,
        "count": len(stocks)
    })

if __name__ == "__main__":
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Stock Predictor - Starting Server")
    print("=" * 60)
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🔧 Debug Mode: {debug}")
    print("=" * 60)
    print("\n📝 Available Endpoints:")
    print(f"   - http://{host}:{port}/health")
    print(f"   - http://{host}:{port}/predict?ticker=LMT&days=7")
    print(f"   - http://{host}:{port}/stocks")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(host=host, port=port, debug=debug)