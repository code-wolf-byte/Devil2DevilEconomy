import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

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
                print(f"Unknown destination type: {type(destination)}")
                return None
                
        except nextcord.errors.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = float(e.response.headers.get('Retry-After', base_delay))
                print(f"Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(retry_after)
                continue
            elif e.status in [403, 404]:  # Forbidden or Not Found
                print(f"Cannot send message: {e}")
                return None
            else:
                print(f"HTTP error sending message: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
        except Exception as e:
            print(f"Unexpected error sending message: {e}")
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
                print(f"Failed to send fallback message to general channel: {e}")
        return None
    except Exception as e:
        print(f"Error sending DM to {user}: {e}")
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
    print(f"Bot is ready! Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} guilds")
    await bot.change_presence(activity=nextcord.Game(name="Managing Economy"))
    
    # Sync slash commands
    try:
        synced = await bot.sync_all_application_commands()
        print(f"Synced {len(synced)} application commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

def run_bot():
    """Run the Discord bot"""
    try:
        # Load the economy cog
        from cogs.economy import setup as setup_economy_cog
        setup_economy_cog(bot, app_instance, db_instance, User, EconomySettings, Achievement, UserAchievement)
        
        # Start the bot
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        print(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_bot() 