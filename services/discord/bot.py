"""
Discord bot service using py-cord.
"""

import discord
from discord.ext import commands
import logging
import os
from typing import Optional

from config import Settings

# Set up logging
discord_logger = logging.getLogger('economy.discord')


class DiscordBot:
    """Discord bot wrapper using py-cord."""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        self.bot: Optional[commands.Bot] = None
        self._setup_bot()
    
    def _setup_bot(self):
        """Initialize the Discord bot with proper intents."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.voice_states = True
        intents.reactions = True
        
        # Create bot instance
        self.bot = commands.Bot(
            command_prefix='!',  # Can be customized
            intents=intents,
            help_command=None,  # We'll create our own help command
            case_insensitive=True
        )
        
        # Set up event handlers
        self._setup_events()
    
    def _setup_events(self):
        """Set up basic bot events."""
        
        @self.bot.event
        async def on_ready():
            discord_logger.info(f'{self.bot.user} has connected to Discord!')
            discord_logger.info(f'Bot is in {len(self.bot.guilds)} guilds')
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching, 
                name="the economy 📈"
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_application_command_error(ctx, error):
            """Handle application command errors."""
            discord_logger.error(f"Application command error: {error}")
            
            if isinstance(error, commands.MissingPermissions):
                await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.respond(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
            else:
                await ctx.respond("❌ An error occurred while processing the command.", ephemeral=True)
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            """Handle general bot errors."""
            discord_logger.error(f"Bot error in event {event}: {args}, {kwargs}")
    
    def add_cog(self, cog):
        """Add a cog to the bot."""
        if self.bot:
            self.bot.add_cog(cog)
            discord_logger.info(f"Added cog: {cog.__class__.__name__}")
    
    def load_economy_cog(self):
        """Load the economy cog with proper dependencies."""
        if not self.app or not self.db:
            discord_logger.error("Cannot load economy cog: missing app or db dependencies")
            return
        
        from .economy_cog import EconomyCog
        from models import User, EconomySettings, Achievement, UserAchievement
        
        # Create and add the economy cog
        economy_cog = EconomyCog(
            bot=self.bot,
            app=self.app,
            db=self.db,
            User=User,
            EconomySettings=EconomySettings,
            Achievement=Achievement,
            UserAchievement=UserAchievement
        )
        
        self.add_cog(economy_cog)
        return economy_cog
    
    async def start(self, token: str):
        """Start the Discord bot."""
        if not token:
            discord_logger.error("No Discord token provided")
            return
        
        try:
            await self.bot.start(token)
        except Exception as e:
            discord_logger.error(f"Failed to start Discord bot: {e}")
            raise
    
    async def close(self):
        """Close the Discord bot connection."""
        if self.bot and not self.bot.is_closed():
            await self.bot.close()
            discord_logger.info("Discord bot connection closed")
    
    def run(self, token: str):
        """Run the Discord bot (blocking)."""
        if not token:
            discord_logger.error("No Discord token provided")
            return
        
        try:
            self.bot.run(token)
        except Exception as e:
            discord_logger.error(f"Failed to run Discord bot: {e}")
            raise
    
    @property
    def is_ready(self) -> bool:
        """Check if the bot is ready."""
        return self.bot and self.bot.is_ready()
    
    @property
    def guilds(self):
        """Get the guilds the bot is in."""
        return self.bot.guilds if self.bot else []
    
    def get_guild(self, guild_id: int):
        """Get a specific guild by ID."""
        return self.bot.get_guild(guild_id) if self.bot else None
    
    def get_user(self, user_id: int):
        """Get a user by ID."""
        return self.bot.get_user(user_id) if self.bot else None
    
    def get_channel(self, channel_id: int):
        """Get a channel by ID."""
        return self.bot.get_channel(channel_id) if self.bot else None 