#!/usr/bin/env python3
"""
Test script to verify the Discord service migration from nextcord to py-cord.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_discord_imports():
    """Test that all Discord service modules can be imported successfully."""
    print("🧪 Testing Discord service imports...")
    
    try:
        # Test py-cord import
        import discord
        from discord.ext import commands
        print("✅ py-cord imported successfully")
        
        # Test our Discord services
        from services.discord import DiscordBot, EconomyCog, DiscordService
        print("✅ Discord services imported successfully")
        
        from services.discord.bot import DiscordBot
        print("✅ DiscordBot imported")
        
        from services.discord.economy_cog import EconomyCog
        print("✅ EconomyCog imported")
        
        from services.discord.service import DiscordService, discord_service
        print("✅ DiscordService imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_discord_bot_creation():
    """Test creating a Discord bot instance."""
    print("\n🧪 Testing Discord bot creation...")
    
    try:
        from services.discord.bot import DiscordBot
        from flask import Flask
        from models.base import init_db
        
        # Create test Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        
        # Initialize database
        init_db(app)
        
        # Create Discord bot
        discord_bot = DiscordBot(app=app, db=None)
        
        print("✅ Discord bot instance created")
        print(f"✅ Bot has {len(discord_bot.bot.cogs)} cogs loaded")
        
        # Test loading economy cog
        with app.app_context():
            economy_cog = discord_bot.load_economy_cog()
            if economy_cog:
                print("✅ Economy cog loaded successfully")
            else:
                print("⚠️ Economy cog failed to load (expected without database)")
        
        return True
        
    except Exception as e:
        print(f"❌ Discord bot creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_discord_service():
    """Test the Discord service wrapper."""
    print("\n🧪 Testing Discord service wrapper...")
    
    try:
        from services.discord.service import DiscordService
        from flask import Flask
        
        # Create test Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        
        # Create Discord service
        discord_service = DiscordService()
        
        print("✅ Discord service created")
        
        # Test initialization (without actually starting the bot)
        discord_service.initialize(app, None)
        
        print("✅ Discord service initialized")
        
        # Test status
        status = discord_service.get_status()
        print(f"✅ Service status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Discord service test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_compatibility():
    """Test that our configuration works with the new Discord services."""
    print("\n🧪 Testing configuration compatibility...")
    
    try:
        from config import EconomyPoints, ActivityLimits, TimeConfig, CustomEmojis, DiscordConfig
        print("✅ All config classes imported")
        
        # Test specific values
        print(f"✅ Daily reward points: {EconomyPoints.DAILY_REWARD}")
        print(f"✅ Max messages limit: {ActivityLimits.MAX_MESSAGES}")
        print(f"✅ Birthday check time: {TimeConfig.BIRTHDAY_CHECK_TIME}")
        print(f"✅ Campus picture emoji: {CustomEmojis.CAMPUS_PICTURE}")
        print(f"✅ Default guild ID: {DiscordConfig.GUILD_ID}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config compatibility error: {e}")
        return False

def test_requirements_compatibility():
    """Test that py-cord is properly installed."""
    print("\n🧪 Testing py-cord installation...")
    
    try:
        import discord
        print(f"✅ Discord.py version: {discord.__version__}")
        
        # Check if it's py-cord (should have certain features)
        if hasattr(discord, 'SlashCommandGroup'):
            print("✅ py-cord features detected")
        else:
            print("⚠️ Standard discord.py detected (py-cord recommended)")
        
        # Test slash command decorators
        from discord import slash_command
        print("✅ Slash command decorator available")
        
        return True
        
    except ImportError as e:
        print(f"❌ py-cord not installed: {e}")
        return False
    except Exception as e:
        print(f"❌ py-cord compatibility error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Discord Service Migration (nextcord → py-cord)")
    print("=" * 60)
    
    tests = [
        test_requirements_compatibility,
        test_discord_imports,
        test_config_compatibility,
        test_discord_bot_creation,
        test_discord_service
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Discord migration tests passed!")
        print("📝 Next steps:")
        print("   1. Install py-cord: pip install -r requirements.txt")
        print("   2. Update bot.py to use the new Discord service")
        print("   3. Remove the old cogs/ directory")
        print("   4. Test with a real Discord bot token")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 