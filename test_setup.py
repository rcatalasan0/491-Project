"""
Test script to verify virtual environment setup
Run: python test_setup.py
"""

import sys
import os

def test_virtual_env():
    """Check if running in virtual environment"""
    print("=" * 60)
    print("🔍 VIRTUAL ENVIRONMENT CHECK")
    print("=" * 60)
    
    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ Running in virtual environment")
        print(f"   Virtual env path: {sys.prefix}")
    else:
        print("❌ NOT running in virtual environment")
        print("   Please activate venv first:")
        print("   Windows: venv\\Scripts\\activate")
        print("   Linux/Mac: source venv/bin/activate")
        return False
    
    print()
    return True

def test_packages():
    """Check if required packages are installed"""
    print("=" * 60)
    print("📦 PACKAGE INSTALLATION CHECK")
    print("=" * 60)
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'psycopg2': 'PostgreSQL adapter',
        'bcrypt': 'Password hashing',
        'dotenv': 'Environment variables'
    }
    
    all_installed = True
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {description:20} - Installed")
        except ImportError:
            print(f"❌ {description:20} - NOT INSTALLED")
            all_installed = False
    
    print()
    return all_installed

def test_env_file():
    """Check if .env file exists"""
    print("=" * 60)
    print("🔧 CONFIGURATION CHECK")
    print("=" * 60)
    
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask password
                display_value = '*' * len(value) if 'PASSWORD' in var else value
                print(f"   {var}: {display_value}")
            else:
                missing_vars.append(var)
                print(f"   ❌ {var}: NOT SET")
        
        if missing_vars:
            print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
            return False
        
    else:
        print("❌ .env file NOT FOUND")
        print("   Create a .env file with database credentials")
        return False
    
    print()
    return True

def test_database_connection():
    """Test PostgreSQL connection"""
    print("=" * 60)
    print("🗄️  DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Successfully connected to PostgreSQL")
        print(f"   Version: {version[0].split(',')[0]}")
        
        cursor.close()
        conn.close()
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("🚀 STOCK PREDICTOR - ENVIRONMENT SETUP TEST")
    print()
    
    results = []
    
    results.append(("Virtual Environment", test_virtual_env()))
    results.append(("Required Packages", test_packages()))
    results.append(("Configuration File", test_env_file()))
    results.append(("Database Connection", test_database_connection()))
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print()
    
    if all(result[1] for result in results):
        print("🎉 ALL TESTS PASSED! Your environment is ready!")
        print("\nNext steps:")
        print("   1. Run: python app.py")
        print("   2. Open: http://127.0.0.1:5000/health")
        print("   3. Test registration at: register.html")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    
    print()

if __name__ == "__main__":
    main()