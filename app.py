from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# 1. ADD NEW IMPORTS: Import the required functions from stockFunctions.py
from mlSkeletons.stockFunctions import stockData_days, stockData_summary
from mlSkeletons.randomForestRegression import random_forest_regression_operations

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
    """Stock forecast endpoint: 7 days historical data + 1-day ML prediction"""
    ticker = (request.args.get("ticker") or "").upper().strip()
    days = request.args.get("days", "7")
    
    # Validation (Keep original validation logic)
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400
    
    try:
        # days parameter now defines the number of *historical* days to display
        days = int(days)
        if days < 1 or days > 30:
            return jsonify({"error": "days must be between 1 and 30"}), 400
    except ValueError:
        return jsonify({"error": "days must be an integer"}), 400
    
    # Validate ticker format
    if not ticker.isalnum() or len(ticker) > 10:
        return jsonify({"error": "ticker must be alphanumeric and <= 10 characters"}), 400
    
    # --- 1. Fetch Historical Data ---
    try:
        # Fetch N days of historical data (e.g., 7 days)
        raw_data = stockData_days(days, ticker) 
        
        if raw_data.empty:
            return jsonify({"error": f"No data found for ticker: {ticker}. Check the ticker symbol."}), 404
        
        # Calculate summary features and select AveragePrice
        summary_df = stockData_summary(raw_data) 
        historical_data = summary_df[['AveragePrice']].reset_index()
        
        # Format the DataFrame into the expected JSON structure for the frontend
        historical_data['date'] = historical_data['Date'].dt.strftime('%Y-%m-%d')
        historical_data['predicted_price'] = historical_data['AveragePrice'].round(2)
        
        # Convert the records to a list of dicts for jsonify
        predictions = historical_data[['date', 'predicted_price']].to_dict(orient='records')
            
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        return jsonify({"error": f"An error occurred while fetching historical data for {ticker}. Detail: {e}"}), 500

    # --- 2. Generate 1-Day Machine Learning Prediction ---
    predicted_next_avg_price = None
    try:
        # Use 5 years of data for model training
        predicted_next_avg_price = random_forest_regression_operations(ticker, years=5)
    except Exception as e:
        # ML prediction failed, but we must return an error because the request is a *forecast*.
        print(f"Error generating ML prediction for {ticker}: {e}")
        return jsonify({"error": f"ML prediction failed for {ticker}. Detail: {e}"}), 500

    # --- 3. Combine Historical Data and Prediction ---
    
    # Determine the date for the prediction point (The day *after* the last historical point)
    last_historical_date = historical_data['Date'].iloc[-1]
    
    # Start checking from the next calendar day until a non-weekend/holiday date is found
    next_day = last_historical_date + timedelta(days=1)
    
    # Simple check to skip weekend days: Monday=0 to Sunday=6
    while next_day.weekday() >= 5: # 5 is Saturday, 6 is Sunday
        next_day += timedelta(days=1)
        
    next_day_str = next_day.strftime('%Y-%m-%d')
    
    # Append the single prediction point to the list
    prediction_point = {
        'date': next_day_str,
        'predicted_price': round(predicted_next_avg_price, 2)
    }
    
    # Add a 'day' index to all points for the frontend list display
    for i, prediction in enumerate(predictions):
        prediction['day'] = i + 1
        
    # Append the prediction point with its 'day' index
    prediction_point['day'] = len(predictions) + 1
    predictions.append(prediction_point)


    # Return the combined data
    return jsonify({
        "ticker": ticker,
        "days": len(predictions), # Return the actual number of points (historical + 1 prediction)
        "model": "RF-1day-forecast", # Indicate that this is a forecast
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