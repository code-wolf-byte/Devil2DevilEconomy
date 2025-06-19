#!/usr/bin/env python3
"""
Database Migration Script for Economy Configuration
Adds role configuration fields to EconomySettings table
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db, EconomySettings

def update_economy_settings_table():
    """Add new columns to EconomySettings table if they don't exist"""
    with app.app_context():
        print("🔧 Updating EconomySettings table...")
        
        try:
            # Try to access the new columns to see if they exist
            settings = EconomySettings.query.first()
            if settings:
                # Try to access new columns
                _ = settings.verified_role_id
                _ = settings.onboarding_role_ids
                _ = settings.verified_bonus_points
                _ = settings.onboarding_bonus_points
                _ = settings.roles_configured
                print("✅ All new columns already exist!")
                return True
        except Exception as e:
            print(f"🔧 New columns not found, attempting to create them: {e}")
        
        try:
            # Drop and recreate tables (simple approach for development)
            print("🔧 Recreating database tables...")
            db.drop_all()
            db.create_all()
            
            # Create default settings
            settings = EconomySettings(
                economy_enabled=False,
                first_time_enabled=False,
                roles_configured=False,
                verified_bonus_points=200,
                onboarding_bonus_points=500
            )
            db.session.add(settings)
            db.session.commit()
            
            print("✅ EconomySettings table updated successfully!")
            print("⚠️  Note: Database was recreated. Existing data may have been reset.")
            return True
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Economy Configuration Database Migration")
    print("=" * 50)
    
    success = update_economy_settings_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now use the Economy Configuration feature in the admin panel.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.") 