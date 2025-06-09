import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

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

# Role configuration from environment variables
VERIFIED_ROLE_ID = os.getenv('VERIFIED_ROLE_ID')
ONBOARDING_ROLE_IDS = os.getenv('ONBOARDING_ROLE_IDS', '').split(',') if os.getenv('ONBOARDING_ROLE_IDS') else []
GENERAL_CHANNEL_ID = int(os.getenv('GENERAL_CHANNEL_ID')) if os.getenv('GENERAL_CHANNEL_ID') else None

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
    
    # Start the daily birthday check task
    if not daily_birthday_check.is_running():
        daily_birthday_check.start()
        print("Daily birthday check task started")

@bot.slash_command(name="balance", description="Check your current balance")
async def balance(interaction: Interaction):
    """Check your current balance"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(interaction.user.id)).first()
        if not user:
            user = User(id=str(interaction.user.id), username=interaction.user.name)
            db_instance.session.add(user)
            db_instance.session.commit()
        
        embed = nextcord.Embed(
            title="Balance",
            description=f"Your current balance: {user.balance} points",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

@bot.slash_command(name="daily", description="Claim your daily points reward")
async def daily(interaction: Interaction):
    """Claim your daily points"""
    with app_instance.app_context():
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            embed = nextcord.Embed(
                title="🔒 Economy Disabled",
                description="The economy system is currently disabled. Contact an admin for more information.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user = User.query.filter_by(id=str(interaction.user.id)).first()
        if not user:
            user = User(id=str(interaction.user.id), username=interaction.user.name)
            db_instance.session.add(user)
            db_instance.session.commit()

        # Check if user can claim daily points
        if user.last_daily and (datetime.now() - user.last_daily) < timedelta(days=1):
            time_left = user.last_daily + timedelta(days=1) - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            embed = nextcord.Embed(
                title="⏰ Daily Reward Not Ready",
                description=f"You can claim your daily points again in {hours} hours and {minutes} minutes.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Update user's balance and last_daily
        user.balance += 85
        user.last_daily = datetime.now()
        db_instance.session.commit()

        embed = nextcord.Embed(
            title="🎉 Daily Reward Claimed!",
            description=f"You received **85 points**!\nYour new balance is **{user.balance} points**",
            color=nextcord.Color.green()
        )
        embed.set_footer(text=f"Next daily reward available in 24 hours")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="leaderboard", description="Show the top 10 users by balance")
async def leaderboard(interaction: Interaction):
    """Show the top 10 users by balance"""
    with app_instance.app_context():
        top_users = User.query.order_by(User.balance.desc()).limit(10).all()
        
        embed = nextcord.Embed(
            title="🏆 Leaderboard",
            color=nextcord.Color.gold()
        )
        
        for i, user in enumerate(top_users, 1):
            embed.add_field(
                name=f"{i}. {user.username}",
                value=f"Balance: {user.balance} points",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

@bot.slash_command(name="give_all", description="Give points to all users (Admin only)")
async def give_all(interaction: Interaction, amount: int):
    """Give points to all users"""
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    with app_instance.app_context():
        users = User.query.all()
        for user in users:
            user.balance += amount
        db_instance.session.commit()
        await interaction.response.send_message(f"Added {amount} points to all users!")

@bot.slash_command(name="emoji_system", description="Show information about the custom emoji reward system (Admin only)")
async def emoji_system_info(interaction: Interaction):
    """Show information about the custom emoji reward system"""
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="🎯 Custom Emoji Reward System",
        description="React to messages with these custom emojis to award points:",
        color=nextcord.Color.blue()
    )
    
    embed.add_field(
        name=f"📝 Daily Engagement: :{DAILY_ENGAGEMENT_EMOJI}:",
        value=f"**{DAILY_ENGAGEMENT_POINTS} points** - React to any message\n*Cooldown: 20 hours*",
        inline=False
    )
    
    embed.add_field(
        name=f"📸 Campus Picture: :{CAMPUS_PICTURE_EMOJI}:",
        value=f"**{CAMPUS_PICTURE_POINTS} points** - React to messages with images\n*Must contain image attachments*",
        inline=False
    )
    
    embed.add_field(
        name=f"💰 Enrollment Deposit: :{ENROLLMENT_DEPOSIT_EMOJI}:",
        value=f"**{ENROLLMENT_DEPOSIT_POINTS} points** - React to enrollment posts\n*One-time bonus per user*",
        inline=False
    )
    
    embed.add_field(
        name=f"🎂 Birthday Setup: `/birthday` command",
        value=f"**{BIRTHDAY_SETUP_POINTS} points** - Set your birthday once\n*Get daily birthday announcements*",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ How to Setup Custom Emojis",
        value="1. Upload emojis to your server\n2. Update the emoji names in bot code\n3. Only admins can award points",
        inline=False
    )
    
    embed.set_footer(text="Only administrators can use these emoji reactions to award points")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="birthday", description="Set your birthday to earn points and get birthday announcements")
async def set_birthday(interaction: Interaction, month: int, day: int):
    """Set your birthday"""
    # Validate month and day
    if month < 1 or month > 12:
        await interaction.response.send_message("❌ Invalid month! Please enter a number between 1-12.", ephemeral=True)
        return
    
    if day < 1 or day > 31:
        await interaction.response.send_message("❌ Invalid day! Please enter a number between 1-31.", ephemeral=True)
        return
    
    # Validate day for specific months
    if month in [4, 6, 9, 11] and day > 30:
        await interaction.response.send_message("❌ That month only has 30 days!", ephemeral=True)
        return
    
    if month == 2 and day > 29:
        await interaction.response.send_message("❌ February only has 28-29 days!", ephemeral=True)
        return
    
    with app_instance.app_context():
        user = User.query.filter_by(id=str(interaction.user.id)).first()
        if not user:
            user = User(id=str(interaction.user.id), username=interaction.user.name)
            db_instance.session.add(user)
            db_instance.session.flush()  # Get the user ID
        
        # Check if user already set their birthday
        if user.birthday and user.birthday_points_received:
            await interaction.response.send_message("🎂 You've already set your birthday and received your points!", ephemeral=True)
            return
        
        # Set birthday
        from datetime import date
        user.birthday = date(2000, month, day)  # Using 2000 as placeholder year
        
        # Award points if first time setting birthday
        if not user.birthday_points_received:
            user.balance += BIRTHDAY_SETUP_POINTS
            user.birthday_points_received = True
            points_message = f"\n💰 You earned **{BIRTHDAY_SETUP_POINTS} points** for setting up your birthday!"
        else:
            points_message = ""
        
        db_instance.session.commit()
        
        month_names = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        
        embed = nextcord.Embed(
            title="🎂 Birthday Set Successfully!",
            description=f"Your birthday is set to **{month_names[month]} {day}**{points_message}",
            color=nextcord.Color.purple()
        )
        
        embed.add_field(
            name="🎉 What happens on your birthday?",
            value="• You'll get a special announcement in the general channel\n• The whole server will celebrate with you!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="economy", description="Enable or disable the economy system (Admin only)")
async def economy_toggle(interaction: Interaction, action: str):
    """Enable or disable the economy system"""
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    if action.lower() not in ['enable', 'disable']:
        await interaction.response.send_message("❌ Invalid action! Use `enable` or `disable`.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    with app_instance.app_context():
        # Get or create economy settings
        settings = EconomySettings.query.first()
        if not settings:
            settings = EconomySettings()
            db_instance.session.add(settings)
        
        if action.lower() == 'enable':
            if settings.economy_enabled:
                embed = nextcord.Embed(
                    title="⚠️ Economy Already Enabled",
                    description="The economy system is already running!",
                    color=nextcord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Enable economy
            settings.economy_enabled = True
            is_first_time = settings.first_time_enabled
            
            if is_first_time:
                settings.first_time_enabled = False
                settings.enabled_at = datetime.now()
                
                # Award verification bonus to existing verified members
                verified_count = 0
                if VERIFIED_ROLE_ID:
                    try:
                        guild = bot.get_guild(int(os.getenv('GUILD_ID')))
                        if guild:
                            verified_role = guild.get_role(int(VERIFIED_ROLE_ID))
                            if verified_role:
                                for member in verified_role.members:
                                    user = User.query.filter_by(id=str(member.id)).first()
                                    if not user:
                                        user = User(
                                            id=str(member.id), 
                                            username=member.display_name,
                                            discord_id=str(member.id)
                                        )
                                        db_instance.session.add(user)
                                        db_instance.session.flush()
                                    
                                    if not user.verification_bonus_received:
                                        user.balance += 200
                                        user.verification_bonus_received = True
                                        verified_count += 1
                                        print(f"Awarded verification bonus to existing member: {member.display_name}")
                    except Exception as e:
                        print(f"Error awarding verification bonuses: {e}")
                
                db_instance.session.commit()
                
                embed = nextcord.Embed(
                    title="🎉 Economy System Enabled!",
                    description="The economy system has been successfully enabled for the first time!",
                    color=nextcord.Color.green()
                )
                
                if verified_count > 0:
                    embed.add_field(
                        name="💰 Verification Bonuses Awarded",
                        value=f"**{verified_count}** existing verified members received **200 points** each!",
                        inline=False
                    )
                
                embed.add_field(
                    name="✨ What's Next?",
                    value="• New verified members will automatically get 200 points\n• Users with onboarding roles get 500 points\n• All economy features are now active!",
                    inline=False
                )
            else:
                settings.enabled_at = datetime.now()
                db_instance.session.commit()
                
                embed = nextcord.Embed(
                    title="✅ Economy System Re-enabled",
                    description="The economy system has been re-enabled!",
                    color=nextcord.Color.green()
                )
        
        else:  # disable
            if not settings.economy_enabled:
                embed = nextcord.Embed(
                    title="⚠️ Economy Already Disabled",
                    description="The economy system is already disabled!",
                    color=nextcord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            settings.economy_enabled = False
            db_instance.session.commit()
            
            embed = nextcord.Embed(
                title="🔒 Economy System Disabled",
                description="The economy system has been disabled. Users can no longer earn or spend points.",
                color=nextcord.Color.red()
            )
    
    await interaction.followup.send(embed=embed)

@bot.event
async def on_message(message):
    """Called when a message is sent"""
    if message.author.bot:
        return
    
    with app_instance.app_context():
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return  # Economy is disabled, don't award points
        
        user = User.query.filter_by(id=str(message.author.id)).first()
        if not user:
            user = User(id=str(message.author.id), username=message.author.name)
            db_instance.session.add(user)
        
        user.message_count += 1
        db_instance.session.commit()
        
        # Check message achievements
        await check_achievements(user, 'message', user.message_count)

@bot.event
async def on_reaction_add(reaction, user):
    """Called when a reaction is added to a message"""
    if user.bot:
        return
    
    with app_instance.app_context():
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return  # Economy is disabled, don't award points
        
        # Check if this is an admin giving points through custom emoji reactions
        await check_admin_reactions(reaction, user)
        
        # Track user reaction count for achievements
        user_obj = User.query.filter_by(id=str(user.id)).first()
        if not user_obj:
            user_obj = User(id=str(user.id), username=user.name)
            db_instance.session.add(user_obj)
        
        user_obj.reaction_count += 1
        db_instance.session.commit()
        
        # Check reaction achievements
        await check_achievements(user_obj, 'reaction', user_obj.reaction_count)

@bot.event
async def on_voice_state_update(member, before, after):
    """Track voice time and check achievements."""
    if member.bot:
        return

    with app_instance.app_context():
        user = User.query.filter_by(id=str(member.id)).first()
        if not user:
            user = User(id=str(member.id), username=member.name)
            db_instance.session.add(user)
        
        # If user joined a voice channel
        if not before.channel and after.channel:
            user.voice_minutes += 1  # Increment by 1 minute
            db_instance.session.commit()
            
            # Check voice achievements
            await check_achievements(user, 'voice')

@bot.event
async def on_member_update(before, after):
    """Called when a member is updated (role changes, nickname changes, etc.)"""
    if before.roles != after.roles:
        # Check if economy is enabled
        with app_instance.app_context():
            settings = EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return  # Economy is disabled, don't award points
            
            added_roles = set(after.roles) - set(before.roles)
            
            # Check for verification role
            if VERIFIED_ROLE_ID and any(role.id == int(VERIFIED_ROLE_ID) for role in added_roles):
                await handle_verification_bonus(after)
            
            # Check for onboarding roles
            if ONBOARDING_ROLE_IDS:
                onboarding_role_ids = [int(role_id.strip()) for role_id in ONBOARDING_ROLE_IDS if role_id.strip()]
                if any(role.id in onboarding_role_ids for role in added_roles):
                    await handle_onboarding_bonus(after)

async def handle_verification_bonus(member):
    """Handle verification bonus for new verified members"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(member.id)).first()
        if not user:
            user = User(
                id=str(member.id), 
                username=member.display_name,
                discord_id=str(member.id)
            )
            db_instance.session.add(user)
            db_instance.session.flush()
        
        # Check if user already received verification bonus
        if user.verification_bonus_received:
            return
        
        # Award verification bonus
        user.balance += 200
        user.verification_bonus_received = True
        db_instance.session.commit()
        
        # Send welcome message in general channel
        if GENERAL_CHANNEL_ID:
            try:
                general_channel = bot.get_channel(GENERAL_CHANNEL_ID)
                if general_channel:
                    embed = nextcord.Embed(
                        title="🎉 Welcome to the Community!",
                        description=f"Welcome {member.mention}! 🎊",
                        color=nextcord.Color.green()
                    )
                    
                    embed.add_field(
                        name="✅ Verification Complete",
                        value="You've been verified and are now part of our community!",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💰 Verification Bonus",
                        value="You've received **200 points** for getting verified!",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🚀 Get Started",
                        value="• Use `/balance` to check your points\n• Use `/daily` to claim daily rewards\n• Check out our store with `/qrcode`",
                        inline=False
                    )
                    
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"Your current balance: {user.balance} points")
                    
                    await general_channel.send(embed=embed)
                    print(f"Sent verification welcome message for {member.display_name}")
            except Exception as e:
                print(f"Error sending verification welcome message: {e}")

async def handle_onboarding_bonus(member):
    """Handle onboarding bonus for new members with onboarding roles"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(member.id)).first()
        if not user:
            user = User(
                id=str(member.id), 
                username=member.display_name,
                discord_id=str(member.id)
            )
            db_instance.session.add(user)
            db_instance.session.flush()
        
        # Check if user already received onboarding bonus
        if user.onboarding_bonus_received:
            return
        
        # Award onboarding bonus
        user.balance += 500
        user.onboarding_bonus_received = True
        db_instance.session.commit()
        
        # Send congratulations message (ephemeral or DM)
        try:
            embed = nextcord.Embed(
                title="🎊 Onboarding Complete!",
                description=f"Congratulations! You've received **500 points** for completing your onboarding!",
                color=nextcord.Color.gold()
            )
            
            embed.add_field(
                name="💰 New Balance",
                value=f"{user.balance} points",
                inline=True
            )
            
            embed.add_field(
                name="🎯 What's Next?",
                value="Start earning more points through daily activities and achievements!",
                inline=False
            )
            
            # Try to send DM, fall back to general channel mention if fails
            try:
                await member.send(embed=embed)
                print(f"Sent onboarding bonus DM to {member.display_name}")
            except:
                if GENERAL_CHANNEL_ID:
                    general_channel = bot.get_channel(GENERAL_CHANNEL_ID)
                    if general_channel:
                        await general_channel.send(f"{member.mention}", embed=embed)
                        print(f"Sent onboarding bonus message in general for {member.display_name}")
        except Exception as e:
            print(f"Error sending onboarding bonus message: {e}")

# Custom emoji reward system - Replace with your server's custom emoji names
CAMPUS_PICTURE_EMOJI = "campus_photo"        # Your custom campus picture emoji name
DAILY_ENGAGEMENT_EMOJI = "daily_engage"      # Your custom daily engagement emoji name  
ENROLLMENT_DEPOSIT_EMOJI = "deposit_check"   # Your custom enrollment deposit emoji name

# Point values for each activity
DAILY_ENGAGEMENT_POINTS = 25   # Points for daily engagement approval
CAMPUS_PICTURE_POINTS = 100    # Points for campus picture approval
ENROLLMENT_DEPOSIT_POINTS = 500 # Points for enrollment deposit approval
BIRTHDAY_SETUP_POINTS = 50     # Points for setting up birthday

# Birthday system configuration
BIRTHDAY_CHECK_TIME = "09:30"  # Time in MST (24-hour format)

async def award_daily_engagement_points(user, message):
    """Award points for daily engagement (admin approved)."""
    try:
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return False  # Economy is disabled, don't award points
        
        # Check if user has already received daily engagement points today
        if user.last_daily_engagement:
            time_since_last = datetime.now() - user.last_daily_engagement
            if time_since_last < timedelta(hours=20):  # 20 hour cooldown to prevent spam
                return False
        
        # Award daily engagement points
        user.points += DAILY_ENGAGEMENT_POINTS
        user.balance += DAILY_ENGAGEMENT_POINTS
        user.last_daily_engagement = datetime.now()
        
        # Send confirmation message
        embed = nextcord.Embed(
            title="🎉 Daily Engagement Approved!",
            description=f"Your daily engagement has been approved by an admin!\n\n**Points Earned:** {DAILY_ENGAGEMENT_POINTS}",
            color=nextcord.Color.green()
        )
        embed.set_footer(text=f"New balance: {user.balance} points")
        
        try:
            await message.author.send(embed=embed)
        except nextcord.Forbidden:
            # If DM fails, reply to the original message
            await message.reply(f"🎉 {message.author.mention} earned {DAILY_ENGAGEMENT_POINTS} points for daily engagement!")
            
        print(f"Daily engagement points awarded to {user.username}: {DAILY_ENGAGEMENT_POINTS} points")
        return True
        
    except Exception as e:
        print(f"Error awarding daily engagement points: {e}")
        return False

async def check_admin_reactions(reaction, admin_user):
    """Check if an admin reaction awards points for specific activities."""
    try:
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return  # Economy is disabled, don't award points
        
        # Check if the user who reacted is an admin
        if not admin_user.guild_permissions.administrator:
            return
        
        message = reaction.message
        
        # Get the message author from database
        message_author = User.query.filter_by(id=str(message.author.id)).first()
        if not message_author:
            message_author = User(id=str(message.author.id), username=message.author.name)
            db_instance.session.add(message_author)
        
        # Check which custom emoji was used
        emoji_name = None
        if hasattr(reaction.emoji, 'name'):
            emoji_name = reaction.emoji.name
        else:
            emoji_name = str(reaction.emoji)
        
        # Check for daily engagement emoji reaction
        if emoji_name == DAILY_ENGAGEMENT_EMOJI:
            await award_daily_engagement_points(message_author, message)
        
        # Check for campus picture emoji reaction
        elif emoji_name == CAMPUS_PICTURE_EMOJI:
            # Check if message has image attachments
            if message.attachments and any(attachment.content_type and attachment.content_type.startswith('image/') for attachment in message.attachments):
                await award_campus_picture_points(message_author, message)
        
        # Check for enrollment deposit emoji reaction
        elif emoji_name == ENROLLMENT_DEPOSIT_EMOJI:
            await award_enrollment_deposit_points(message_author, message)
        
    except Exception as e:
        print(f"Error in check_admin_reactions: {e}")

async def award_campus_picture_points(user, message):
    """Award points for campus picture posts (admin approved)."""
    try:
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return False  # Economy is disabled, don't award points
        
        # Award campus picture points
        user.points += CAMPUS_PICTURE_POINTS
        user.balance += CAMPUS_PICTURE_POINTS
        
        # Send confirmation message
        embed = nextcord.Embed(
            title="📸 Campus Picture Approved!",
            description=f"Your campus picture has been approved by an admin!\n\n**Points Earned:** {CAMPUS_PICTURE_POINTS}",
            color=nextcord.Color.blue()
        )
        embed.set_footer(text=f"New balance: {user.balance} points")
        
        try:
            await message.author.send(embed=embed)
        except nextcord.Forbidden:
            # If DM fails, reply to the original message
            await message.reply(f"📸 {message.author.mention} earned {CAMPUS_PICTURE_POINTS} points for sharing a campus picture!")
            
        print(f"Campus picture points awarded to {user.username}: {CAMPUS_PICTURE_POINTS} points")
        return True
        
    except Exception as e:
        print(f"Error awarding campus picture points: {e}")
        return False

async def award_enrollment_deposit_points(user, message):
    """Award points for enrollment deposit confirmation (admin approved, one-time)."""
    try:
        # Check if economy is enabled
        settings = EconomySettings.query.first()
        if not settings or not settings.economy_enabled:
            return False  # Economy is disabled, don't award points
        
        # Check if user has already received enrollment deposit points
        if user.enrollment_deposit_received:
            return False
        
        # Award enrollment deposit points
        user.points += ENROLLMENT_DEPOSIT_POINTS
        user.balance += ENROLLMENT_DEPOSIT_POINTS
        user.enrollment_deposit_received = True
        
        # Send confirmation message
        embed = nextcord.Embed(
            title="💰 Enrollment Deposit Confirmed!",
            description=f"Your enrollment deposit has been confirmed by an admin!\n\n**Bonus Points:** {ENROLLMENT_DEPOSIT_POINTS}",
            color=nextcord.Color.gold()
        )
        embed.set_footer(text=f"New balance: {user.balance} points")
        
        try:
            await message.author.send(embed=embed)
        except nextcord.Forbidden:
            # If DM fails, reply to the original message
            await message.reply(f"💰 {message.author.mention} earned {ENROLLMENT_DEPOSIT_POINTS} points for enrollment deposit confirmation!")
            
        print(f"Enrollment deposit points awarded to {user.username}: {ENROLLMENT_DEPOSIT_POINTS} points")
        return True
        
    except Exception as e:
        print(f"Error awarding enrollment deposit points: {e}")
        return False

# Birthday system functions
async def check_birthdays():
    """Check for birthdays and send announcements daily at 9:30 MST"""
    from datetime import date
    import pytz
    
    try:
        with app_instance.app_context():
            today = date.today()
            
            # Get users with birthdays today
            birthday_users = User.query.filter(
                db_instance.func.extract('month', User.birthday) == today.month,
                db_instance.func.extract('day', User.birthday) == today.day
            ).all()
            
            if birthday_users:
                channel = bot.get_channel(int(GENERAL_CHANNEL_ID))
                if channel:
                    for user in birthday_users:
                        # Create birthday announcement embed
                        embed = nextcord.Embed(
                            title="🎉 Happy Birthday! 🎂",
                            description=f"Today is **{user.username}'s** birthday!\n\nEveryone wish them a happy birthday! 🥳",
                            color=nextcord.Color.gold()
                        )
                        embed.set_thumbnail(url=user.avatar_url if user.avatar_url else "https://cdn.discordapp.com/embed/avatars/0.png")
                        embed.set_footer(text="Have an amazing day! 🎈")
                        
                        await channel.send(embed=embed)
                        print(f"Birthday announcement sent for {user.username}")
                else:
                    print(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
            else:
                print(f"No birthdays today ({today.strftime('%B %d')})")
                
    except Exception as e:
        print(f"Error checking birthdays: {e}")

# Set up daily birthday check task
@tasks.loop(time=datetime.strptime(BIRTHDAY_CHECK_TIME, "%H:%M").time())
async def daily_birthday_check():
    """Daily task to check for birthdays at 9:30 MST"""
    import pytz
    
    # Convert to MST timezone
    mst = pytz.timezone('US/Mountain')
    now_mst = datetime.now(mst)
    
    print(f"Running daily birthday check at {now_mst.strftime('%Y-%m-%d %H:%M:%S MST')}")
    await check_birthdays()

@daily_birthday_check.before_loop
async def before_birthday_check():
    """Wait until bot is ready before starting birthday checks"""
    await bot.wait_until_ready()
    print("Birthday checking task started - will run daily at 9:30 MST")

async def check_achievements(user, achievement_type, count=None):
    """Check and award achievements for a user."""
    with app_instance.app_context():
        # Get all achievements of the specified type
        achievements = Achievement.query.filter_by(type=achievement_type).all()
        
        for achievement in achievements:
            # Check if user already has this achievement
            user_achievement = UserAchievement.query.filter_by(
                user_id=user.id, 
                achievement_id=achievement.id
            ).first()
            
            if user_achievement:
                continue  # User already has this achievement
                
            # Check if user meets the requirement
            requirement_met = False
            if achievement_type == 'message':
                requirement_met = user.message_count >= achievement.requirement
            elif achievement_type == 'reaction':
                requirement_met = user.reaction_count >= achievement.requirement
            elif achievement_type == 'voice':
                requirement_met = user.voice_minutes >= achievement.requirement
            elif achievement_type == 'boost':
                requirement_met = user.has_boosted and achievement.requirement == 1
            elif achievement_type == 'join':
                requirement_met = True  # Join achievement is awarded immediately
            elif achievement_type == 'daily':
                requirement_met = True  # Daily achievement is awarded when claiming
                
            if requirement_met:
                await award_achievement(user, achievement)

async def send_achievement_announcement(user, achievement):
    """Send achievement announcement to general channel."""
    try:
        channel = bot.get_channel(int(GENERAL_CHANNEL_ID))
        if channel:
            # Create achievement announcement embed
            embed = nextcord.Embed(
                title="🏆 Achievement Unlocked!",
                description=f"**{achievement.name}**\n{achievement.description}",
                color=nextcord.Color.gold()
            )
            
            # Add achievement details
            embed.add_field(
                name="🎖️ Achievement",
                value=f"**{achievement.name}**",
                inline=True
            )
            
            embed.add_field(
                name="💰 Points Earned",
                value=f"**{achievement.points} points**",
                inline=True
            )
            
            embed.add_field(
                name="🎯 New Balance",
                value=f"**{user.balance} points**",
                inline=True
            )
            
            # Set user avatar as thumbnail
            embed.set_thumbnail(url=user.avatar_url if user.avatar_url else "https://cdn.discordapp.com/embed/avatars/0.png")
            
            # Add footer with congratulations
            embed.set_footer(text="Congratulations on your achievement! 🎉")
            
            # Send message with user ping and embed
            await channel.send(f"🎉 Congratulations <@{user.id}>! You've unlocked a new achievement!", embed=embed)
            print(f"Achievement announcement sent for {user.username}: {achievement.name}")
            
        else:
            print(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
            
    except Exception as e:
        print(f"Error sending achievement announcement: {e}")

async def award_achievement(user, achievement):
    """Award an achievement to a user."""
    with app_instance.app_context():
        # Add achievement to user
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id
        )
        db_instance.session.add(user_achievement)
        
        # Award points
        user.points += achievement.points
        user.balance += achievement.points
        
        db_instance.session.commit()
        
        print(f"Achievement '{achievement.name}' awarded to {user.username} for {achievement.points} points!")
        
        # Send achievement announcement to general channel
        await send_achievement_announcement(user, achievement)

@bot.slash_command(name="achievements", description="View your achievements")
async def achievements(interaction: Interaction):
    """View your achievements"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(interaction.user.id)).first()
        if not user:
            user = User(id=str(interaction.user.id), username=interaction.user.name)
            db_instance.session.add(user)
            db_instance.session.commit()
        
        # Get user's achievements
        user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
        
        embed = nextcord.Embed(
            title="🏆 Your Achievements",
            color=nextcord.Color.gold()
        )
        
        if not user_achievements:
            embed.description = "You haven't unlocked any achievements yet!"
        else:
            for ua in user_achievements:
                achievement = Achievement.query.get(ua.achievement_id)
                embed.add_field(
                    name=f"🎖️ {achievement.name}",
                    value=f"{achievement.description}\n**Points:** {achievement.points}",
                    inline=False
                )
        
        embed.set_footer(text=f"Total Points Earned: {user.points}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="qrcode", description="Get your QR code (requires a purchase)")
async def qrcode_command(interaction: Interaction):
    """Get your QR code if you have a UUID"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(interaction.user.id)).first()
        if not user:
            embed = nextcord.Embed(
                title="❌ No Account Found",
                description="You need to log in to the web app first!",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not user.user_uuid:
            embed = nextcord.Embed(
                title="❌ No UUID Found",
                description="You need to make a purchase first to get your UUID and QR code!",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            import qrcode
            import io
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(user.user_uuid)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to buffer for Discord
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Create embed message
            embed = nextcord.Embed(
                title="🔗 Your QR Code",
                description="Here's your unique QR code:",
                color=nextcord.Color.green()
            )
            embed.add_field(
                name="Your UUID",
                value=f"`{user.user_uuid}`",
                inline=False
            )
            embed.set_footer(text="Keep this QR code safe - it's your unique identifier!")
            
            # Create file from QR code buffer
            file = nextcord.File(img_buffer, filename="qr_code.png")
            embed.set_image(url="attachment://qr_code.png")
            
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
            
        except Exception as e:
            embed = nextcord.Embed(
                title="❌ Error",
                description="Failed to generate QR code. Please try again later.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"Error generating QR code: {str(e)}")

def run_bot():
    """Run the Discord bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    print("Starting Discord bot...")
    print(f"Token length: {len(token)}")
    
    # Use asyncio's new_event_loop to avoid signal handler issues in threads
    import asyncio
    import signal
    
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot without signal handlers in thread
        loop.run_until_complete(bot.start(token))
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    run_bot() 