import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Set up logging for bot
bot_logger = logging.getLogger('economy.bot')

# Bot setup
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',  # Add a command prefix even though we're using slash commands
    intents=intents
)

# Global variables to store app and db instances
app_instance = None
db_instance = None
User = None
Achievement = None
UserAchievement = None
EconomySettings = None

# Rate limiting helper functions
async def safe_send_message(destination, *args, **kwargs):
    """Safely send a message with rate limit handling and retries."""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            if hasattr(destination, 'send'):
                return await destination.send(*args, **kwargs)
            elif hasattr(destination, 'response'):
                return await destination.response.send_message(*args, **kwargs)
            else:
                bot_logger.warning(f"Unknown destination type: {type(destination)}")
                return None
                
        except nextcord.errors.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = float(e.response.headers.get('Retry-After', base_delay))
                bot_logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(retry_after)
                continue
            elif e.status in [403, 404]:  # Forbidden or Not Found
                bot_logger.warning(f"Cannot send message: {e}")
                return None
            else:
                bot_logger.error(f"HTTP error sending message: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
        except Exception as e:
            bot_logger.error(f"Unexpected error sending message: {e}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(base_delay * (2 ** attempt))
            continue
    
    return None

async def safe_dm_user(user, *args, **kwargs):
    """Safely send a DM to a user with fallback to general channel."""
    try:
        return await safe_send_message(user, *args, **kwargs)
    except nextcord.Forbidden:
        # DM failed, try general channel as fallback
        if os.getenv('GENERAL_CHANNEL_ID'):
            try:
                channel = bot.get_channel(int(os.getenv('GENERAL_CHANNEL_ID')))
                if channel and 'embed' in kwargs:
                    # Modify embed to mention user
                    embed = kwargs['embed']
                    embed.description = f"{user.mention}\n\n{embed.description}"
                    return await safe_send_message(channel, embed=embed)
            except Exception as e:
                bot_logger.error(f"Failed to send fallback message to general channel: {e}")
        return None
    except Exception as e:
        bot_logger.error(f"Error sending DM to {user}: {e}")
        return None

def init_bot_with_app(app, db, user_model, achievement_model, user_achievement_model, economy_settings_model):
    """Initialize bot with app and database instances."""
    global app_instance, db_instance, User, Achievement, UserAchievement, EconomySettings
    app_instance = app
    db_instance = db
    User = user_model
    Achievement = achievement_model
    UserAchievement = user_achievement_model
    EconomySettings = economy_settings_model

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    bot_logger.info(f"🎉 Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    bot_logger.info(f"🌐 Connected to {len(bot.guilds)} guilds:")
    
    for guild in bot.guilds:
        bot_logger.info(f"   - {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    
    await bot.change_presence(activity=nextcord.Game(name="Managing Economy"))
    bot_logger.info("🎮 Bot presence set to 'Managing Economy'")
    
    # Test intents
    bot_logger.info("🔍 Testing bot permissions and intents...")
    bot_logger.info(f"   - Can read messages: {bot.intents.message_content}")
    bot_logger.info(f"   - Can see members: {bot.intents.members}")
    bot_logger.info(f"   - Can see reactions: {bot.intents.reactions}")
    
    # Sync slash commands
    try:
        bot_logger.info("⚙️  Syncing application commands...")
        synced = await bot.sync_all_application_commands()
        if synced:
            bot_logger.info(f"✅ Synced {len(synced)} application commands successfully")
        else:
            bot_logger.info("ℹ️  No application commands to sync")
    except Exception as e:
        bot_logger.error(f"❌ Failed to sync commands: {e}")
    
    bot_logger.info("🚀 Bot startup complete! Ready to process events.")

@bot.event
async def on_connect():
    """Called when the bot connects to Discord"""
    bot_logger.info("🔗 Bot connected to Discord!")

@bot.event
async def on_disconnect():
    """Called when the bot disconnects from Discord"""
    bot_logger.warning("⚠️  Bot disconnected from Discord")

@bot.event
async def on_resumed():
    """Called when the bot resumes a session"""
    bot_logger.info("🔄 Bot session resumed")

@bot.event
async def on_error(event, *args, **kwargs):
    """Called when an error occurs"""
    bot_logger.error(f"❌ Bot error in event '{event}': {args}")
    import traceback
    bot_logger.error(traceback.format_exc())

def run_bot():
    """Run the Discord bot - simplified version for async integration"""
    try:
        # Check if Discord token is available
        discord_token = os.getenv('DISCORD_TOKEN')
        if not discord_token or discord_token == 'your_discord_bot_token_here':
            bot_logger.warning("Discord bot not started - DISCORD_TOKEN not configured")
            return
        
        # Ensure we have the required instances before starting
        if not app_instance or not db_instance:
            bot_logger.critical("ERROR: Flask app or database not initialized before starting bot")
            return
            
        # Load the economy cog
        from cogs.economy import setup as setup_economy_cog
        setup_economy_cog(bot, app_instance, db_instance, User, EconomySettings, Achievement, UserAchievement)
        
        # Simple bot run - the calling code will handle async properly
        bot_logger.info("Bot setup complete, ready to start...")
        
    except Exception as e:
        bot_logger.error(f"Error setting up bot: {e}")
        import traceback
        bot_logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_bot() 