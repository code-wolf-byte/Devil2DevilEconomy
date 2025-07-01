#!/usr/bin/env python3
"""
Fix balance/points consistency issues in the database.
This script processes ALL users and ensures user.balance and user.points fields are identical.
Balance is used as the authoritative source since all user-facing commands display balance.

NOTE: This function is now automatically run on application startup.
      This standalone script is provided for manual database maintenance only.
"""

import os
import sys
from shared import User, db
from utils import fix_balance_consistency

def main():
    """Main function"""
    print("🔧 Devil2Devil Economy Balance Consistency Fix")
    print("📊 Processing ALL users to ensure balance/points consistency")
    print("-" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('models.py'):
        print("❌ Error: models.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Import the app context
    try:
        from main import app
        success = fix_balance_consistency(app, db, User)
        if success:
            print("\n🎉 Balance consistency fix completed successfully!")
            print("💡 All user-facing commands now display consistent balance values.")
            print("🔄 Note: This fix now runs automatically on application startup.")
        else:
            print("\n❌ Balance consistency fix failed!")
            sys.exit(1)
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)

if __name__ == "__main__":
    main() 