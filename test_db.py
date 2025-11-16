import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'stock_predictor',
    'user': 'postgres',  # or 'stock_app_user' if you created one
    'password': 'your_password_here'  # REPLACE with your actual password
}

def test_connection():
    """Test database connection and query data"""
    print("🔄 Testing PostgreSQL connection...")
    
    try:
        # Establish connection
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL!")
        
        # Create cursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test query 1: Count tables
        cursor.execute("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        result = cursor.fetchone()
        print(f"✅ Found {result['table_count']} tables in database")
        
        # Test query 2: List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print("\n📋 Tables in database:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Test query 3: Count users
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        result = cursor.fetchone()
        print(f"\n✅ Found {result['user_count']} users in database")
        
        # Test query 4: Count stocks
        cursor.execute("SELECT COUNT(*) as stock_count FROM stocks")
        result = cursor.fetchone()
        print(f"✅ Found {result['stock_count']} stocks in database")
        
        # Test query 5: List stock symbols
        cursor.execute("SELECT symbol, name FROM stocks ORDER BY symbol")
        stocks = cursor.fetchall()
        print("\n📈 Defense sector stocks:")
        for stock in stocks:
            print(f"   - {stock['symbol']}: {stock['name']}")
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        print("\n🎉 All tests passed! Database is ready to use.")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if PostgreSQL service is running")
        print("   2. Verify your password in DB_CONFIG")
        print("   3. Ensure database 'stock_predictor' exists")
        print("   4. Check if user has permission to connect")
        return False
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()