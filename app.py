from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
import re

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # allows frontend to call this API

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'stock_predictor'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
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
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
    """Handle user registration"""
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Email validation
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Password validation
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed. Please try again later."}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.close()
                conn.close()
                return jsonify({
                    "error": "An account with this email already exists. Please login instead."
                }), 409
            
            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Insert new user
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, role, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, email, created_at
                """,
                (email, password_hash, 'user')
            )
            
            new_user = cursor.fetchone()
            conn.commit()
            
            print(f"✅ New user registered: {email} (ID: {new_user['id']})")
            
            cursor.close()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Registration successful! Redirecting to login...",
                "user": {
                    "id": new_user['id'],
                    "email": new_user['email'],
                    "created_at": new_user['created_at'].isoformat()
                }
            }), 201
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Email already registered. Please use a different email."
            }), 409
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            print(f"Registration error: {e}")
            return jsonify({
                "error": "Registration failed. Please try again."
            }), 500
            
    except Exception as e:
        print(f"Request error: {e}")
        return jsonify({"error": "Invalid request data"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get user from database
            cursor.execute(
                "SELECT id, email, password_hash, role FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()
                
                print(f"✅ User logged in: {email} (ID: {user['id']})")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    "success": True,
                    "message": "Login successful!",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "role": user['role']
                    }
                }), 200
            else:
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid email or password"}), 401
                
        except Exception as e:
            cursor.close()
            conn.close()
            print(f"Login error: {e}")
            return jsonify({"error": "Login failed. Please try again."}), 500
            
    except Exception as e:
        print(f"Request error: {e}")
        return jsonify({"error": "Invalid request data"}), 400

@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/api/users/count")
def users_count():
    """Get total number of registered users"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "total_users": result['count']
        }), 200
        
    except Exception as e:
        print(f"Error getting user count: {e}")
        return jsonify({"error": "Failed to get user count"}), 500

@app.get("/predict")
def predict():
    """Existing prediction endpoint"""
    ticker = (request.args.get("ticker") or "").upper()
    days = int(request.args.get("days") or 7)
    if not ticker:
        return jsonify(error="Missing ticker"), 400

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

@app.route("/stocks")
def get_stocks():
    """Get all defense sector stocks"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT symbol, name, sector, exchange FROM stocks ORDER BY symbol")
        stocks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "stocks": stocks,
            "count": len(stocks)
        }), 200
        
    except Exception as e:
        print(f"Error getting stocks: {e}")
        return jsonify({"error": "Failed to get stocks"}), 500

if __name__ == "__main__":
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Stock Predictor - Starting Flask Server")
    print("=" * 60)
    print(f"📊 Database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🔧 Debug Mode: {debug}")
    print("=" * 60)
    print("\n📝 Available Endpoints:")
    print(f"   - http://{host}:{port}/health")
    print(f"   - http://{host}:{port}/api/register (POST)")
    print(f"   - http://{host}:{port}/api/login (POST)")
    print(f"   - http://{host}:{port}/api/users/count")
    print(f"   - http://{host}:{port}/predict?ticker=LMT&days=7")
    print(f"   - http://{host}:{port}/stocks")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(host=host, port=port, debug=debug)