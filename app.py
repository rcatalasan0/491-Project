from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

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
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({"error": "Invalid email format"}), 400
        
        # Password strength validation
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            existing_user = cursor.fetchone()
            
            if existing_user:
                return jsonify({
                    "error": "An account with this email already exists"
                }), 409
            
            # Hash password
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Insert new user
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, %s)
                RETURNING id, email, created_at
                """,
                (email, password_hash, 'user')
            )
            
            new_user = cursor.fetchone()
            conn.commit()
            
            return jsonify({
                "message": "Registration successful",
                "user": {
                    "id": new_user['id'],
                    "email": new_user['email'],
                    "created_at": new_user['created_at'].isoformat()
                }
            }), 201
            
        except psycopg2.IntegrityError:
            conn.rollback()
            return jsonify({
                "error": "Email already registered"
            }), 409
            
        except Exception as e:
            conn.rollback()
            print(f"Registration error: {e}")
            return jsonify({
                "error": "Registration failed. Please try again."
            }), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Request error: {e}")
        return jsonify({"error": "Invalid request"}), 400

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
                "SELECT id, email, password_hash FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()
                
                return jsonify({
                    "message": "Login successful",
                    "user": {
                        "id": user['id'],
                        "email": user['email']
                    }
                }), 200
            else:
                return jsonify({"error": "Invalid email or password"}), 401
                
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

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
    except:
        db_status = "error"
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    })

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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)