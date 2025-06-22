#!/usr/bin/env python3
"""
Test script to verify the refactored models work correctly.
This script will test importing and basic functionality of the new model structure.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all our new modules can be imported successfully."""
    print("🧪 Testing imports...")
    
    try:
        # Test config imports
        from config import Settings, EconomyPoints, ActivityLimits
        print("✅ Config imports successful")
        
        # Test model imports
        from models import db, User, Product, Purchase, Achievement, UserAchievement, EconomySettings
        print("✅ Model imports successful")
        
        # Test that constants are accessible
        print(f"✅ Daily reward points: {EconomyPoints.DAILY_REWARD}")
        print(f"✅ Max daily claims: {ActivityLimits.MAX_DAILY_CLAIMS}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_model_creation():
    """Test creating model instances."""
    print("\n🧪 Testing model creation...")
    
    try:
        from models import User, Product, Purchase
        from config import ProductTypes, PurchaseStatus
        
        # Test User model
        user = User(
            id="123456789",
            username="TestUser",
            discord_id="123456789"
        )
        print(f"✅ User created: {user}")
        print(f"✅ User display name: {user.display_name}")
        print(f"✅ User can claim daily: {user.can_claim_daily()}")
        
        # Test Product model
        product = Product(
            name="Test Product",
            description="A test product",
            price=100,
            product_type=ProductTypes.PHYSICAL
        )
        print(f"✅ Product created: {product}")
        print(f"✅ Product is digital: {product.is_digital}")
        print(f"✅ Product is available: {product.is_available}")
        
        # Test Purchase model
        purchase = Purchase(
            user_id="123456789",
            product_id=1,
            points_spent=100,
            status=PurchaseStatus.COMPLETED
        )
        print(f"✅ Purchase created: {purchase}")
        print(f"✅ Purchase is completed: {purchase.is_completed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings():
    """Test settings configuration."""
    print("\n🧪 Testing settings...")
    
    try:
        from config import Settings
        
        print(f"✅ Database URL: {Settings.DATABASE_URL}")
        print(f"✅ Discord configured: {Settings.is_properly_configured()}")
        
        missing = Settings.validate_required_settings()
        if missing:
            print(f"⚠️  Missing settings: {missing}")
        else:
            print("✅ All required settings present")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Refactored Economy Models")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_model_creation,
        test_settings
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
        print("🎉 All tests passed! Refactoring looks good.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 