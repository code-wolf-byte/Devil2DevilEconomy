"""
Discord service wrapper for managing the bot and its functionality.
"""

import asyncio
import logging
import threading
from typing import Optional

from .bot import DiscordBot
from config import Settings

# Set up logging
service_logger = logging.getLogger('economy.discord.service')


class DiscordService:
    """Service class for managing Discord bot functionality."""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        self.discord_bot: Optional[DiscordBot] = None
        self.bot_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
    
    def initialize(self, app, db):
        """Initialize the Discord service with Flask app and database."""
        self.app = app
        self.db = db
        
        # Create Discord bot instance
        self.discord_bot = DiscordBot(app=app, db=db)
        
        # Load economy cog
        self.discord_bot.load_economy_cog()
        
        service_logger.info("Discord service initialized")
    
    def start_bot(self, token: str = None):
        """Start the Discord bot in a separate thread."""
        if not token:
            token = Settings.DISCORD_TOKEN
        
        if not token:
            service_logger.error("No Discord token provided")
            return False
        
        if self._running:
            service_logger.warning("Discord bot is already running")
            return True
        
        if not self.discord_bot:
            service_logger.error("Discord bot not initialized")
            return False
        
        def run_bot():
            """Run the bot in a separate thread."""
            try:
                # Create new event loop for this thread
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                
                self._running = True
                service_logger.info("Starting Discord bot...")
                
                # Run the bot
                self.discord_bot.run(token)
                
            except Exception as e:
                service_logger.error(f"Error running Discord bot: {e}")
                self._running = False
            finally:
                if self.loop:
                    self.loop.close()
                self._running = False
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
        
        service_logger.info("Discord bot thread started")
        return True
    
    def stop_bot(self):
        """Stop the Discord bot."""
        if not self._running:
            service_logger.info("Discord bot is not running")
            return
        
        try:
            if self.discord_bot and self.loop:
                # Schedule bot closure in the bot's event loop
                asyncio.run_coroutine_threadsafe(
                    self.discord_bot.close(), 
                    self.loop
                ).result(timeout=10)
            
            # Wait for thread to finish
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=5)
            
            self._running = False
            service_logger.info("Discord bot stopped")
            
        except Exception as e:
            service_logger.error(f"Error stopping Discord bot: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if the Discord bot is running."""
        return self._running and self.discord_bot and self.discord_bot.is_ready
    
    @property
    def is_ready(self) -> bool:
        """Check if the Discord bot is ready."""
        return self.discord_bot and self.discord_bot.is_ready
    
    def get_guild_count(self) -> int:
        """Get the number of guilds the bot is in."""
        if self.discord_bot:
            return len(self.discord_bot.guilds)
        return 0
    
    def get_guild(self, guild_id: int):
        """Get a guild by ID."""
        if self.discord_bot:
            return self.discord_bot.get_guild(guild_id)
        return None
    
    def get_user(self, user_id: int):
        """Get a user by ID."""
        if self.discord_bot:
            return self.discord_bot.get_user(user_id)
        return None
    
    def get_channel(self, channel_id: int):
        """Get a channel by ID."""
        if self.discord_bot:
            return self.discord_bot.get_channel(channel_id)
        return None
    
    async def send_message(self, channel_id: int, content: str = None, embed=None):
        """Send a message to a channel."""
        if not self.discord_bot or not self.loop:
            service_logger.error("Discord bot not available")
            return None
        
        try:
            channel = self.discord_bot.get_channel(channel_id)
            if not channel:
                service_logger.error(f"Channel {channel_id} not found")
                return None
            
            # Send message in bot's event loop
            future = asyncio.run_coroutine_threadsafe(
                channel.send(content=content, embed=embed),
                self.loop
            )
            return future.result(timeout=10)
            
        except Exception as e:
            service_logger.error(f"Error sending message to channel {channel_id}: {e}")
            return None
    
    def get_status(self) -> dict:
        """Get the current status of the Discord service."""
        return {
            'running': self._running,
            'ready': self.is_ready,
            'guild_count': self.get_guild_count(),
            'bot_user': str(self.discord_bot.bot.user) if self.discord_bot and self.discord_bot.bot else None
        }


# Global Discord service instance
discord_service = DiscordService() 