from shared import app, bot, db, User, EconomySettings, Achievement, UserAchievement, login_manager, Product
from discord_files.cogs.economy import EconomyCog
from routes.auth import auth, handle_callback
from routes.main import main
from utils import fix_balance_consistency
from fix_image_paths import fix_image_paths
import dotenv
import os
import time
import asyncio
import threading
from flask import redirect, url_for

# Load environment variables
dotenv.load_dotenv()

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(main)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Discord OAuth callback route (at root level to match Discord's redirect)
@app.route('/callback')
def callback():
    """Handle Discord OAuth callback"""
    return handle_callback()

# Discord bot setup
token = os.getenv("DISCORD_TOKEN")

# Global reference to the economy cog
economy_cog = None

@bot.event
async def on_raw_reaction_add(payload):
    """Handles reactions on ALL messages, including older ones not in cache"""
    # Skip bot reactions
    if payload.user_id == bot.user.id:
        return
    
    # Get the channel and user objects
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)
    
    if channel and user:
        try:
            # Try to fetch the message (this works even for uncached messages)
            message = await channel.fetch_message(payload.message_id)
            print(f"🚀 RAW Reaction detected: {payload.emoji} by {user.name}")
            print(f"   - Message ID: {payload.message_id}")
            print(f"   - Channel: {channel.name}")
            print(f"   - Message content: '{message.content[:50]}...'")
            print(f"   - Message author: {message.author.name}")
            print(f"   - Message created: {message.created_at}")
            
            # Pass the reaction data to the economy cog for processing
            if economy_cog:
                await economy_cog.process_reaction(payload)
            else:
                print("⚠️ Economy cog not available for reaction processing")
                
        except Exception as e:
            print(f"❌ Error fetching message: {e}")
            # Even if we can't fetch the message, we still know about the reaction
            print(f"🚀 RAW Reaction detected: {payload.emoji} by {user.name} on message {payload.message_id}")
            
            # Still try to process the reaction even if we can't fetch the message
            if economy_cog:
                await economy_cog.process_reaction(payload)

@bot.event
async def on_message(message):
    if not message.author.bot:  # Ignore bot messages
        print(f"Message from {message.author.name}: {message.content}")
    
    # Process commands
    await bot.process_commands(message)

# Add a test command to create a message we can react to
@bot.command(name='test')
async def test_command(ctx):
    """Send a test message for reactions"""
    await ctx.send("React to this message to test the reaction handler! 👍")

@bot.command(name='ping')
async def ping_command(ctx):
    """Simple ping command"""
    await ctx.send("Pong!")

@bot.command(name='oldmsg')
async def old_message_test(ctx):
    """Explains how to test reactions on old messages"""
    await ctx.send(
        "To test reactions on old messages:\n"
        "1. Find any old message in this server\n"
        "2. React to it with any emoji\n"
        "3. Check the bot console - it should detect the reaction via `on_raw_reaction_add`!\n\n"
        "The bot will detect reactions on ANY message, regardless of when it was sent."
    )

async def setup_bot():
    """Setup the bot asynchronously"""
    global economy_cog
    
    print("Starting bot setup...")
    
    # Set the bot token
    bot.set_token(token)
    
    # Clear any existing commands to avoid conflicts
    bot.tree.clear_commands(guild=None)
    print("Cleared existing commands")
    
    # Create and store reference to the economy cog
    economy_cog = EconomyCog(bot, app, db, User, EconomySettings, Achievement, UserAchievement)
    print("Created economy cog")
    
    # Start the bot first
    print("Starting bot...")
    await bot.start(token)
    
    # Wait for bot to be ready using our custom method
    print("Waiting for bot to be ready...")
    await bot.wait_for_ready()
    print("Bot is ready!")
    
    # Now add the cog after bot is ready
    try:
        print("Adding economy cog...")
        await bot.add_cog(economy_cog)
        print("Economy cog added successfully!")
        
        # Check what commands are available
        commands = bot.tree.get_commands()
        print(f"Available commands before sync: {len(commands)}")
        for cmd in commands:
            print(f"  - {cmd.name}")
        
        # Sync commands after adding cog
        print("Syncing commands...")
        await bot.tree.sync()
        print(f"Synced {len(bot.tree.get_commands())} commands successfully!")
        
    except Exception as e:
        print(f"Warning: Could not add economy cog: {e}")
        import traceback
        traceback.print_exc()

def run_bot():
    """Run the bot in a separate thread"""
    try:
        asyncio.run(setup_bot())
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    # Fix balance/points consistency before starting the application
    print("🔧 Running balance consistency check...")
    try:
        fix_balance_consistency(app, db, User)
        print("✅ Balance consistency check completed!")
    except Exception as e:
        print(f"⚠️ Warning: Balance consistency check failed: {e}")
        print("   Continuing with application startup...")
    
    # Fix image paths before starting the application
    print("🔧 Running image path fix...")
    try:
        fix_image_paths()
        print("✅ Image path fix completed!")
    except Exception as e:
        print(f"⚠️ Warning: Image path fix failed: {e}")
        print("   Continuing with application startup...")
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Bot thread started")
    
    # Give the bot more time to start and connect
    time.sleep(5)
    
    # Start the Flask app (this will block)
    print("Starting Flask app...")
    app.run(host = '0.0.0.0', debug=True, use_reloader=False, port=5000)  # use_reloader=False to avoid issues with threading

