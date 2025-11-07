from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
import re

app = Flask(__name__)
CORS(app)  # allows index.html to call this API

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'stock_predictor'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            return jsonify(error="Email and password are required"), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify(error="Invalid email format"), 400
        
        # Validate password strength
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify(error=msg), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify(error="Database connection failed"), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            
            if existing_user:
                cur.close()
                conn.close()
                return jsonify(error="An account with this email already exists"), 409
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert new user
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, created_at
                """,
                (email, password_hash, 'user', datetime.utcnow())
            )
            
            new_user = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                "message": "Registration successful",
                "user": {
                    "id": new_user['id'],
                    "email": new_user['email'],
                    "created_at": new_user['created_at'].isoformat()
                }
            }), 201
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
                conn.close()
            print(f"Database error: {e}")
            return jsonify(error="Registration failed. Please try again."), 500
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify(error="An unexpected error occurred"), 500

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user and return session info"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            return jsonify(error="Email and password are required"), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify(error="Database connection failed"), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get user by email
            cur.execute(
                "SELECT id, email, password_hash, role FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            
            if not user:
                cur.close()
                conn.close()
                return jsonify(error="Invalid email or password"), 401
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                cur.close()
                conn.close()
                return jsonify(error="Invalid email or password"), 401
            
            # Update last login time
            cur.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.utcnow(), user['id'])
            )
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "role": user['role']
                }
            }), 200
            
        except psycopg2.Error as e:
            if conn:
                conn.close()
            print(f"Database error: {e}")
            return jsonify(error="Login failed. Please try again."), 500
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify(error="An unexpected error occurred"), 500

@app.route("/api/predict", methods=["GET"])
def predict():
    """Get stock price predictions"""
    ticker = (request.args.get("ticker") or "").upper()
    days = int(request.args.get("days") or 7)
    
    if not ticker:
        return jsonify(error="Missing ticker"), 400
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return jsonify(error="Database connection failed"), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if ticker exists
        cur.execute("SELECT symbol, name FROM stocks WHERE symbol = %s", (ticker,))
        stock = cur.fetchone()
        
        if not stock:
            cur.close()
            conn.close()
            return jsonify(error=f"Ticker '{ticker}' not found in database"), 404
        
        # Get recent price data (last 7 days)
        cur.execute(
            """
            SELECT price_date, close_price
            FROM prices
            WHERE symbol = %s
            ORDER BY price_date DESC
            LIMIT 7
            """,
            (ticker,)
        )
        
        historical_prices = cur.fetchall()
        cur.close()
        conn.close()
        
        if not historical_prices:
            return jsonify(error=f"No historical data available for {ticker}"), 404
        
        # Simple prediction logic: linear trend from last prices
        prices = [float(p['close_price']) for p in reversed(historical_prices)]
        
        # Calculate simple moving average trend
        if len(prices) >= 2:
            trend = (prices[-1] - prices[0]) / len(prices)
        else:
            trend = 0
        
        # Generate predictions
        last_price = prices[-1]
        last_date = historical_prices[0]['price_date']
        
        predictions = []
        for i in range(1, days + 1):
            pred_date = last_date + timedelta(days=i)
            pred_price = last_price + (trend * i)
            predictions.append({
                "date": pred_date.isoformat(),
                "price": round(pred_price, 2)
            })
        
        return jsonify({
            "ticker": ticker,
            "name": stock['name'],
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "historical": [
                {
                    "date": p['price_date'].isoformat(),
                    "price": float(p['close_price'])
                }
                for p in reversed(historical_prices)
            ],
            "predictions": predictions
        }), 200
        
    except psycopg2.Error as e:
        if conn:
            conn.close()
        print(f"Database error: {e}")
        return jsonify(error="Failed to fetch predictions"), 500
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify(error="An unexpected error occurred"), 500

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    """Get list of available stocks"""
    conn = get_db_connection()
    if not conn:
        return jsonify(error="Database connection failed"), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT symbol, name, sector, exchange FROM stocks ORDER BY symbol")
        stocks = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            "stocks": [dict(s) for s in stocks],
            "count": len(stocks)
        }), 200
        
    except psycopg2.Error as e:
        if conn:
            conn.close()
        print(f"Database error: {e}")
        return jsonify(error="Failed to fetch stocks"), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)