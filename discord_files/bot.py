import discord
from discord.ext import commands
import asyncio
import threading
import os

class EconomyBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents, *args, **kwargs)
        self.token = None
        self.bot_thread = None
        self.ready_event = asyncio.Event()

    def set_token(self, token):
        self.token = token

    async def setup_hook(self):
        from discord_files.cogs.economy import EconomyCog
        from shared import app, db, User, EconomySettings, Achievement, UserAchievement

        await self.add_cog(EconomyCog(self, app, db, User, EconomySettings, Achievement, UserAchievement))

        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            await self.tree.sync(guild=guild)
            print(f"Bot setup complete. Synced {len(self.tree.get_commands(guild=guild))} commands to guild {guild_id}.")
        else:
            await self.tree.sync()
            print(f"Bot setup complete. Synced {len(self.tree.get_commands())} global commands.")

        # Print intents information
        print(f"Bot intents: {self.intents}")
        print(f"Reactions intent enabled: {self.intents.reactions}")
        print(f"Message content intent enabled: {self.intents.message_content}")

    async def on_ready(self):
        print(f"Bot logged in as {self.user} (ID: {self.user.id})")
        print("Bot is ready to receive events!")
        print("Try using !test command to create a message you can react to.")
        
        # Signal that the bot is ready
        self.ready_event.set()

    def run_bot(self):
        """Run the bot in an async event loop"""
        if not self.token:
            print("Error: No token provided. Please set DISCORD_TOKEN in your .env file.")
            return
        
        try:
            super().run(self.token)
        except Exception as e:
            print(f"Error running bot: {e}")

    def start_bot_thread(self):
        """Start the bot in a separate thread"""
        if self.bot_thread is None or not self.bot_thread.is_alive():
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            print("Bot thread started")
        else:
            print("Bot is already running")

    def run(self):
        """Public method to start the bot"""
        self.start_bot_thread()
        
    async def wait_for_ready(self):
        """Wait for the bot to be ready"""
        await self.ready_event.wait()
