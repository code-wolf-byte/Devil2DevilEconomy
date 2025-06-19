#!/usr/bin/env python3
"""
Reset Economy Settings Script
This script resets the first_time_enabled flag so the verified achievement assignment works
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db, EconomySettings

def reset_economy_settings():
    """Reset the economy settings to allow first-time setup"""
    with app.app_context():
        print("🔧 Resetting economy settings...")
        
        # Get the current settings
        settings = EconomySettings.query.first()
        if settings:
            print(f"Current settings: economy_enabled={settings.economy_enabled}, first_time_enabled={settings.first_time_enabled}")
            
            # Reset the flags
            settings.economy_enabled = False
            settings.first_time_enabled = False  # This will make it trigger first-time logic
            
            db.session.commit()
            print("✅ Economy settings reset successfully!")
            print("Now you can run '/economy enable' and it will trigger the first-time setup")
        else:
            print("❌ No economy settings found in database")

if __name__ == "__main__":
    reset_economy_settings() 