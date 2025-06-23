"""
Discord bot entry point using the new Discord service.
Migrated from nextcord to py-cord with improved service architecture.
Includes fallback mode for Python 3.13 compatibility issues.
"""

import os
import logging
import threading
import signal
import sys
from dotenv import load_dotenv

from config import Settings

# Load environment variables
load_dotenv()

# Set up logging for bot
bot_logger = logging.getLogger('economy.bot')

# Global Discord service instance - will be None if Discord imports fail
discord_service = None
discord_import_error = None

# Try to import Discord service, fallback gracefully if it fails
try:
    from services.discord import DiscordService
    discord_service = DiscordService()
    bot_logger.info("Discord service imported successfully")
except ImportError as e:
    discord_import_error = str(e)
    bot_logger.warning(f"Discord service unavailable due to import error: {e}")
    bot_logger.warning("Running in web-only mode. Discord bot functionality disabled.")
    
    # Create a dummy Discord service for compatibility
    class DummyDiscordService:
        def __init__(self):
            self.is_ready = False
            
        def initialize(self, app, db):
            bot_logger.info("Dummy Discord service initialized (Discord disabled)")
            
        def start_bot(self, token):
            bot_logger.warning("Discord bot start requested but Discord is disabled")
            return False
            
        def stop_bot(self):
            bot_logger.info("Discord bot stop requested but Discord is disabled")
            
        def get_status(self):
            return {
                'running': False,
                'ready': False,
                'guild_count': 0,
                'bot_user': 'Disabled (Python 3.13 compatibility issue)',
                'error': discord_import_error
            }
    
    discord_service = DummyDiscordService()

# Global variables to store app and db instances
app_instance = None
db_instance = None


def init_bot_with_app(app, db):
    """Initialize bot with app and database instances."""
    global app_instance, db_instance, discord_service
    
    app_instance = app
    db_instance = db
    
    if discord_service:
        # Initialize the Discord service
        discord_service.initialize(app, db)
        bot_logger.info("Bot initialized with Flask app and database")
    else:
        bot_logger.warning("Bot initialization skipped - Discord service unavailable")


def start_bot_async():
    """Start the Discord bot in a separate thread."""
    if not discord_service:
        bot_logger.error("Discord service not available")
        return False
    
    # Check if Discord token is available
    discord_token = Settings.DISCORD_TOKEN
    if not discord_token or discord_token == 'your_discord_bot_token_here':
        bot_logger.warning("Discord bot not started - DISCORD_TOKEN not configured")
        return False
    
    # Ensure we have the required instances before starting
    if not app_instance or not db_instance:
        bot_logger.critical("ERROR: Flask app or database not initialized before starting bot")
        return False
    
    # Check if this is the dummy service
    if isinstance(discord_service, type(discord_service)) and hasattr(discord_service, '__class__') and 'Dummy' in discord_service.__class__.__name__:
        bot_logger.warning("Cannot start Discord bot - running in web-only mode due to Python 3.13 compatibility")
        return False
    
    # Start the bot
    success = discord_service.start_bot(discord_token)
    if success:
        bot_logger.info("Discord bot started successfully")
    else:
        bot_logger.error("Failed to start Discord bot")
    
    return success


def stop_bot():
    """Stop the Discord bot."""
    global discord_service
    
    if discord_service:
        discord_service.stop_bot()
        bot_logger.info("Discord bot stopped")


def get_bot_status():
    """Get the current status of the Discord bot."""
    if discord_service:
        return discord_service.get_status()
    return {
        'running': False,
        'ready': False,
        'guild_count': 0,
        'bot_user': 'Service unavailable',
        'error': 'Discord service failed to initialize'
    }


def is_bot_ready():
    """Check if the Discord bot is ready."""
    return discord_service and hasattr(discord_service, 'is_ready') and discord_service.is_ready


def run_bot():
    """Run the Discord bot (blocking mode for standalone execution)."""
    try:
        # Check if Discord is available
        if discord_import_error:
            bot_logger.error("Cannot run Discord bot in standalone mode:")
            bot_logger.error(f"Import error: {discord_import_error}")
            bot_logger.error("This is likely due to Python 3.13 compatibility issues with Discord libraries.")
            bot_logger.error("Please use Python 3.12 or wait for library updates.")
            return
        
        # Check if Discord token is available
        discord_token = Settings.DISCORD_TOKEN
        if not discord_token or discord_token == 'your_discord_bot_token_here':
            bot_logger.warning("Discord bot not started - DISCORD_TOKEN not configured")
            return
        
        bot_logger.info("Starting Discord bot in standalone mode...")
        
        # Create a minimal Flask app for testing
        from flask import Flask
        from models.base import init_db
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = Settings.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        init_db(app)
        
        # Initialize bot with app
        init_bot_with_app(app, None)
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            bot_logger.info("Received shutdown signal, stopping bot...")
            stop_bot()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start bot (blocking)
        with app.app_context():
            if hasattr(discord_service, 'discord_bot'):
                discord_service.discord_bot.run(discord_token)
            else:
                bot_logger.error("Discord bot not available in dummy service")
            
    except Exception as e:
        bot_logger.error(f"Error running bot: {e}")
        import traceback
        bot_logger.error(traceback.format_exc())


# Backward compatibility functions for existing code
def safe_send_message(destination, *args, **kwargs):
    """
    Legacy function for backward compatibility.
    In the new architecture, message sending should be handled through the Discord service.
    """
    bot_logger.warning("safe_send_message called - consider using Discord service methods instead")
    # This would need to be implemented if still needed
    pass


def safe_dm_user(user, *args, **kwargs):
    """
    Legacy function for backward compatibility.
    In the new architecture, DM sending should be handled through the Discord service.
    """
    bot_logger.warning("safe_dm_user called - consider using Discord service methods instead")
    # This would need to be implemented if still needed
    pass


if __name__ == "__main__":
    run_bot() 