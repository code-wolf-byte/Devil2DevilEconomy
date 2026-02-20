from shared import app, bot, db, User, EconomySettings, Achievement, UserAchievement, login_manager, Product
from discord_files.cogs.economy import EconomyCog
from routes.auth import auth, handle_callback
from routes.main import main
from routes.api import api as api_bp
import dotenv
import os
import time
import asyncio
import threading
from flask import redirect, url_for, jsonify

# Load environment variables
dotenv.load_dotenv()

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(main)
app.register_blueprint(api_bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Discord OAuth callback route (at root level to match Discord's redirect)
@app.route('/callback')
def callback():
    """Handle Discord OAuth callback"""
    return handle_callback()

@app.route('/login')
def login_redirect():
    """Shortcut for auth login to support frontend routing."""
    return redirect(url_for('auth.login'))

@app.route('/logout')
def logout_redirect():
    """Shortcut for auth logout to support frontend routing."""
    return redirect(url_for('auth.logout'))


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

def run_startup_tasks():
    """Run startup tasks needed before serving requests."""
    # Create database tables and seed required data
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

        # Seed achievements that must exist for the economy to function correctly.
        # Safe to run on every deploy — skips any that already exist.
        achievements_to_seed = [
            # Reaction milestones
            {'name': 'Reactor I',   'description': 'Add 10 reactions to messages.',    'points': 200, 'type': 'reactions', 'requirement': 10},
            {'name': 'Reactor II',  'description': 'Add 500 reactions to messages.',   'points': 500, 'type': 'reactions', 'requirement': 500},
            # Voice milestones
            {'name': 'Voice Regular', 'description': 'Spend 60 minutes in voice channels.',    'points': 200, 'type': 'voice', 'requirement': 60},
            {'name': 'Voice Veteran', 'description': 'Spend 720 minutes in voice channels.',   'points': 500, 'type': 'voice', 'requirement': 720},
            {'name': 'Voice Legend',  'description': 'Spend 1,440 minutes in voice channels.', 'points': 700, 'type': 'voice', 'requirement': 1440},
        ]

        seeded = 0
        for ach_data in achievements_to_seed:
            exists = Achievement.query.filter_by(
                type=ach_data['type'], requirement=ach_data['requirement']
            ).first()
            if not exists:
                db.session.add(Achievement(**ach_data))
                seeded += 1

        if seeded:
            db.session.commit()
            print(f"✅ Seeded {seeded} new achievement(s).")
        else:
            print("✅ All achievements already present — nothing to seed.")
    # Fix image paths before starting the application
    print("🔧 Running image path fix...")
    try:
        # Find all products with image URLs that start with '/static/uploads/'
        products_to_fix = Product.query.filter(
            Product.image_url.like('/static/uploads/%')
        ).all()
        
        if products_to_fix:
            print(f"🔧 Found {len(products_to_fix)} products with incorrect image paths:")
            for product in products_to_fix:
                old_path = product.image_url
                # Remove the '/static/uploads/' prefix, keeping just 'filename'
                new_path = product.image_url.replace('/static/uploads/', '', 1)
                product.image_url = new_path
                print(f"   - Product '{product.name}': {old_path} → {new_path}")
            
            # Save changes
            db.session.commit()
            print(f"✅ Fixed {len(products_to_fix)} image paths successfully!")
        else:
            print("✅ No products found with incorrect image paths.")
            
    except Exception as e:
        print(f"⚠️ Warning: Image path fix failed: {e}")
        print("   Continuing with application startup...")
    
    # Ensure uploads directory has proper permissions
    print("🔧 Checking uploads directory permissions...")
    try:
        uploads_dir = os.path.join('static', 'uploads')
        
        # Create directory if it doesn't exist
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, mode=0o775)
            print(f"📁 Created uploads directory: {uploads_dir}")
        
        # Set proper permissions (775 = rwxrwxr-x)
        # This allows the owner and group to read, write, and execute
        # and others to read and execute
        os.chmod(uploads_dir, 0o775)
        print(f"✅ Set uploads directory permissions to 775: {uploads_dir}")
        
        # Verify permissions
        stat_info = os.stat(uploads_dir)
        perms = oct(stat_info.st_mode)[-3:]
        print(f"📋 Current uploads directory permissions: {perms}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not set uploads directory permissions: {e}")
        print("   This may cause file upload issues. Check directory permissions manually.")
        print("   Continuing with application startup...")
    
    # Ensure database files have proper permissions
    print("🔧 Checking database file permissions...")
    try:
        db_files = ['store.db', 'instance/store.db']
        
        for db_file in db_files:
            if os.path.exists(db_file):
                # Set proper permissions (664 = rw-rw-r--)
                # This allows the owner and group to read and write
                os.chmod(db_file, 0o664)
                print(f"✅ Set database file permissions to 664: {db_file}")
                
                # Verify permissions
                stat_info = os.stat(db_file)
                perms = oct(stat_info.st_mode)[-3:]
                print(f"📋 Current database file permissions: {perms} for {db_file}")
            else:
                print(f"📝 Database file does not exist yet: {db_file}")
        
        # Check instance directory permissions
        instance_dir = 'instance'
        if os.path.exists(instance_dir):
            os.chmod(instance_dir, 0o775)
            print(f"✅ Set instance directory permissions to 775: {instance_dir}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not set database file permissions: {e}")
        print("   This may cause database write issues. Check file permissions manually.")
        print("   Continuing with application startup...")

def start_bot_thread():
    """Start the Discord bot in a background thread."""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Bot thread started")
    return bot_thread

def run_dev_server():
    run_startup_tasks()
    start_bot_thread()
    # Give the bot more time to start and connect
    time.sleep(5)
    # Start the Flask app (this will block)
    print("Starting Flask app...")
    app.run(host='0.0.0.0', debug=True, use_reloader=False, port=5000)

if __name__ == "__main__":
    run_dev_server()
