#!/usr/bin/env python3
"""
Test script to verify the refactored routes work correctly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_route_imports():
    """Test that all route modules can be imported successfully."""
    print("🧪 Testing route imports...")
    
    try:
        from routes import register_routes
        print("✅ Route registration function imported")
        
        from routes.auth import auth_bp
        print("✅ Auth blueprint imported")
        
        from routes.shop import shop_bp
        print("✅ Shop blueprint imported")
        
        from routes.user import user_bp
        print("✅ User blueprint imported")
        
        from routes.admin import admin_bp
        print("✅ Admin blueprint imported")
        
        from routes.api import api_bp
        print("✅ API blueprint imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_flask_app_creation():
    """Test creating a Flask app with our routes."""
    print("\n🧪 Testing Flask app creation with routes...")
    
    try:
        from flask import Flask
        from config import Settings
        from models.base import init_db
        from routes import register_routes
        
        # Create test Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        
        # Initialize database
        init_db(app)
        
        # Register routes
        register_routes(app)
        
        print(f"✅ Flask app created with {len(app.blueprints)} blueprints")
        
        # Test that blueprints are registered
        expected_blueprints = ['auth', 'shop', 'user', 'admin', 'api']
        for bp_name in expected_blueprints:
            if bp_name in app.blueprints:
                print(f"✅ Blueprint '{bp_name}' registered")
            else:
                print(f"❌ Blueprint '{bp_name}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_url_generation():
    """Test that routes can generate URLs correctly."""
    print("\n🧪 Testing route URL generation...")
    
    try:
        from flask import Flask, url_for
        from routes import register_routes
        
        # Create test Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        
        # Register routes
        register_routes(app)
        
        with app.test_request_context():
            # Test generating URLs for key routes
            urls = {
                'shop.index': url_for('shop.index'),
                'auth.login': url_for('auth.login'),
                'user.my_purchases': url_for('user.my_purchases'),
                'admin.admin_panel': url_for('admin.admin_panel'),
                'api.file_manager': url_for('api.file_manager'),
            }
            
            for route_name, url in urls.items():
                print(f"✅ {route_name}: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Refactored Routes")
    print("=" * 50)
    
    tests = [
        test_route_imports,
        test_flask_app_creation,
        test_route_url_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All route tests passed! Refactoring looks good.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 