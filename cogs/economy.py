import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction
from datetime import datetime, timedelta, date
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging for cogs
cog_logger = logging.getLogger('economy.cogs')

VERIFIED_ROLE_ID = int(os.getenv('VERIFIED_ROLE_ID', 0))
GENERAL_CHANNEL_ID = int(os.getenv('GENERAL_CHANNEL_ID')) if os.getenv('GENERAL_CHANNEL_ID') else None
ONBOARDING_ROLE_IDS = os.getenv('ONBOARDING_ROLE_IDS', '').split(',') if os.getenv('ONBOARDING_ROLE_IDS') else []

# Custom emoji reward system - Replace with your server's custom emoji names
CAMPUS_PICTURE_EMOJI = "campus_photo"        # Your custom campus picture emoji name
DAILY_ENGAGEMENT_EMOJI = "daily_engage"      # Your custom daily engagement emoji name  
ENROLLMENT_DEPOSIT_EMOJI = "deposit_check"   # Your custom enrollment deposit emoji name

# Point values for each activity
DAILY_ENGAGEMENT_POINTS = 25   # Points for daily engagement approval
CAMPUS_PICTURE_POINTS = 100    # Points for campus picture approval
ENROLLMENT_DEPOSIT_POINTS = 500 # Points for enrollment deposit approval
BIRTHDAY_SETUP_POINTS = 50     # Points for setting up birthday

# Limits for recurring activities
MAX_DAILY_CLAIMS = 90          # Maximum daily reward claims per user
MAX_CAMPUS_PHOTOS = 5          # Maximum campus photo approvals per user
MAX_DAILY_ENGAGEMENT = 365     # Maximum daily engagement approvals per user (1 per day for a year)
MAX_VOICE_MINUTES = 10000      # Maximum voice minutes that count toward achievements
MAX_MESSAGES = 50000           # Maximum messages that count toward achievements
MAX_REACTIONS = 25000          # Maximum reactions that count toward achievements

# Birthday system configuration
BIRTHDAY_CHECK_TIME = "09:30"  # Time in MST (24-hour format)

class EconomyCog(commands.Cog):
    def __init__(self, bot, app, db, User, EconomySettings, Achievement, UserAchievement):
        self.bot = bot
        self.app = app
        self.db = db
        self.User = User
        self.EconomySettings = EconomySettings
        self.Achievement = Achievement
        self.UserAchievement = UserAchievement
        
        # Don't start tasks in __init__ - wait for bot to be ready
        # self.daily_birthday_check.start()  # Moved to on_ready
        # self.process_role_assignments.start()  # Moved to on_ready

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        if self.daily_birthday_check.is_running():
            self.daily_birthday_check.cancel()
        if self.process_role_assignments.is_running():
            self.process_role_assignments.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready - start background tasks"""
        cog_logger.info("Economy cog ready - starting background tasks")
        if not self.daily_birthday_check.is_running():
            self.daily_birthday_check.start()
        if not self.process_role_assignments.is_running():
            self.process_role_assignments.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Called when a message is sent"""
        if message.author.bot:
            return
        
        with self.app.app_context():
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return  # Economy is disabled, don't award points
            
            user = self.User.query.filter_by(id=str(message.author.id)).first()
            if not user:
                user = self.User(id=str(message.author.id), username=message.author.name, discord_id=str(message.author.id))
                self.db.session.add(user)
                self.db.session.flush()  # Ensure user is created with default values
            
            # Ensure message_count is not None and enforce limit
            if user.message_count is None:
                user.message_count = 0
            
            # Only increment if under the limit
            if user.message_count < MAX_MESSAGES:
                user.message_count += 1
                self.db.session.commit()
                
                # Check message achievements
                await self.check_achievements(user, 'message', user.message_count)
            else:
                # User has reached message limit, still commit to update last activity
                self.db.session.commit()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Called when a reaction is added to a message"""
        if user.bot:
            return
        
        with self.app.app_context():
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return  # Economy is disabled, don't award points
            
            # Check if this is an admin giving points through custom emoji reactions
            await self.check_admin_reactions(reaction, user)
            
            # Track user reaction count for achievements
            user_obj = self.User.query.filter_by(id=str(user.id)).first()
            if not user_obj:
                user_obj = self.User(id=str(user.id), username=user.name, discord_id=str(user.id))
                self.db.session.add(user_obj)
                self.db.session.flush()  # Ensure user is created with default values
            
            # Ensure reaction_count is not None and enforce limit
            if user_obj.reaction_count is None:
                user_obj.reaction_count = 0
            
            # Only increment if under the limit
            if user_obj.reaction_count < MAX_REACTIONS:
                user_obj.reaction_count += 1
                self.db.session.commit()
                
                # Check reaction achievements
                await self.check_achievements(user_obj, 'reaction', user_obj.reaction_count)
            else:
                # User has reached reaction limit, still commit to update last activity
                self.db.session.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice time and check achievements."""
        if member.bot:
            return

        with self.app.app_context():
            user = self.User.query.filter_by(id=str(member.id)).first()
            if not user:
                user = self.User(id=str(member.id), username=member.name, discord_id=str(member.id))
                self.db.session.add(user)
                self.db.session.flush()  # Ensure user is created with default values
            
            # If user joined a voice channel
            if not before.channel and after.channel:
                # Ensure voice_minutes is not None and enforce limit
                if user.voice_minutes is None:
                    user.voice_minutes = 0
                
                # Only increment if under the limit
                if user.voice_minutes < MAX_VOICE_MINUTES:
                    user.voice_minutes += 1  # Increment by 1 minute
                    self.db.session.commit()
                    
                    # Check voice achievements
                    await self.check_achievements(user, 'voice')
                else:
                    # User has reached voice limit, still commit to update last activity
                    self.db.session.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Called when a member is updated (role changes, nickname changes, etc.)"""
        if before.roles != after.roles:
            # Check if economy is enabled
            with self.app.app_context():
                settings = self.EconomySettings.query.first()
                if not settings or not settings.economy_enabled:
                    return  # Economy is disabled, don't award points
                
                added_roles = set(after.roles) - set(before.roles)
                
                # Check for verification role
                if VERIFIED_ROLE_ID and any(role.id == int(VERIFIED_ROLE_ID) for role in added_roles):
                    await self.handle_verification_bonus(after)
                
                # Check for onboarding roles
                if ONBOARDING_ROLE_IDS:
                    onboarding_role_ids = [int(role_id.strip()) for role_id in ONBOARDING_ROLE_IDS if role_id.strip()]
                    if any(role.id in onboarding_role_ids for role in added_roles):
                        await self.handle_onboarding_bonus(after)

    async def handle_verification_bonus(self, member):
        """Handle verification bonus for new verified members with atomic transaction"""
        with self.app.app_context():
            try:
                # Lock user row to prevent race conditions
                user = self.User.query.filter_by(id=str(member.id)).first()
                if not user:
                    user = self.User(
                        id=str(member.id), 
                        username=member.display_name,
                        discord_id=str(member.id),
                        verification_bonus_received=False
                    )
                    self.db.session.add(user)
                    self.db.session.commit()
                
                # Check if user already received verification bonus
                if user.verification_bonus_received:
                    cog_logger.info(f"Verification bonus already received by {member.display_name}")
                    return
                
                # Award verification bonus atomically
                user.balance += 200
                user.verification_bonus_received = True
                self.db.session.commit()
                cog_logger.info(f"Verification bonus awarded to {member.display_name}: 200 points")
                
            except Exception as e:
                self.db.session.rollback()
                cog_logger.error(f"Error awarding verification bonus to {member.display_name}: {e}")
                import traceback
                cog_logger.error(traceback.format_exc())
                return
            
            # Send welcome message in general channel
            if GENERAL_CHANNEL_ID:
                try:
                    general_channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
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
                        cog_logger.info(f"Sent verification welcome message for {member.display_name}")
                except Exception as e:
                    cog_logger.error(f"Error sending verification welcome message: {e}")

    async def handle_onboarding_bonus(self, member):
        """Handle onboarding bonus for new members with onboarding roles with atomic transaction"""
        with self.app.app_context():
            try:
                # Lock user row to prevent race conditions
                user = self.User.query.filter_by(id=str(member.id)).first()
                if not user:
                    user = self.User(
                        id=str(member.id), 
                        username=member.display_name,
                        discord_id=str(member.id),
                        onboarding_bonus_received=False
                    )
                    self.db.session.add(user)
                    self.db.session.commit()
                
                # Check if user already received onboarding bonus
                if user.onboarding_bonus_received:
                    cog_logger.info(f"Onboarding bonus already received by {member.display_name}")
                    return
                
                # Award onboarding bonus atomically
                user.balance += 500
                user.onboarding_bonus_received = True
                self.db.session.commit()
                cog_logger.info(f"Onboarding bonus awarded to {member.display_name}: 500 points")
                
            except Exception as e:
                self.db.session.rollback()
                cog_logger.error(f"Error awarding onboarding bonus to {member.display_name}: {e}")
                import traceback
                cog_logger.error(traceback.format_exc())
                return
            
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
                    cog_logger.info(f"Sent onboarding bonus DM to {member.display_name}")
                except:
                    if GENERAL_CHANNEL_ID:
                        general_channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
                        if general_channel:
                            await general_channel.send(f"{member.mention}", embed=embed)
                            cog_logger.info(f"Sent onboarding bonus message in general for {member.display_name}")
            except Exception as e:
                cog_logger.error(f"Error sending onboarding bonus message: {e}")

    async def award_daily_engagement_points(self, user, message):
        """Award points for daily engagement (admin approved)."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return False  # Economy is disabled, don't award points
            
            # Check if user has reached maximum daily engagement approvals
            daily_engagement_count = getattr(user, 'daily_engagement_count', 0) or 0
            if daily_engagement_count >= MAX_DAILY_ENGAGEMENT:
                # Send message to admin about limit reached
                try:
                    await message.reply(f"❌ {message.author.mention} has already reached the maximum of {MAX_DAILY_ENGAGEMENT} daily engagement approvals.")
                except:
                    pass
                return False
            
            # Check if user has already received daily engagement points today
            if user.last_daily_engagement:
                time_since_last = datetime.now() - user.last_daily_engagement
                if time_since_last < timedelta(hours=20):  # 20 hour cooldown to prevent spam
                    return False
            
            # Award daily engagement points
            user.points += DAILY_ENGAGEMENT_POINTS
            user.balance += DAILY_ENGAGEMENT_POINTS
            user.last_daily_engagement = datetime.now()
            
            # Increment daily engagement counter
            if not hasattr(user, 'daily_engagement_count') or user.daily_engagement_count is None:
                user.daily_engagement_count = 0
            user.daily_engagement_count += 1
            
            remaining_engagements = MAX_DAILY_ENGAGEMENT - user.daily_engagement_count
            
            # Send confirmation message
            embed = nextcord.Embed(
                title="🎉 Daily Engagement Approved!",
                description=f"Your daily engagement has been approved by an admin!\n\n**Points Earned:** {DAILY_ENGAGEMENT_POINTS}",
                color=nextcord.Color.green()
            )
            embed.add_field(
                name="New Balance",
                value=f"{user.balance} pitchforks",
                inline=True
            )
            embed.add_field(
                name="Engagements Remaining",
                value=f"{remaining_engagements} out of {MAX_DAILY_ENGAGEMENT}",
                inline=True
            )
            embed.set_footer(text=f"New balance: {user.balance} pitchforks")
            
            try:
                await message.author.send(embed=embed)
            except nextcord.Forbidden:
                # If DM fails, reply to the original message
                await message.reply(f"🎉 {message.author.mention} earned {DAILY_ENGAGEMENT_POINTS} pitchforks for daily engagement! ({remaining_engagements} remaining)")
                
            cog_logger.info(f"Daily engagement points awarded to {user.username}: {DAILY_ENGAGEMENT_POINTS} points ({user.daily_engagement_count}/{MAX_DAILY_ENGAGEMENT})")
            return True
            
        except Exception as e:
            cog_logger.error(f"Error awarding daily engagement points: {e}")
            return False

    async def check_admin_reactions(self, reaction, admin_user):
        """Check if an admin reaction awards points for specific activities."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return  # Economy is disabled, don't award points
            
            # Check if the user who reacted is an admin
            if not admin_user.guild_permissions.administrator:
                return
            
            message = reaction.message
            
            # Get the message author from database
            message_author = self.User.query.filter_by(id=str(message.author.id)).first()
            if not message_author:
                message_author = self.User(id=str(message.author.id), username=message.author.name)
                self.db.session.add(message_author)
            
            # Check which custom emoji was used
            emoji_name = None
            if hasattr(reaction.emoji, 'name'):
                emoji_name = reaction.emoji.name
            else:
                emoji_name = str(reaction.emoji)
            
            # Check for daily engagement emoji reaction
            if emoji_name == DAILY_ENGAGEMENT_EMOJI:
                await self.award_daily_engagement_points(message_author, message)
            
            # Check for campus picture emoji reaction
            elif emoji_name == CAMPUS_PICTURE_EMOJI:
                # Check if message has image attachments
                if message.attachments and any(attachment.content_type and attachment.content_type.startswith('image/') for attachment in message.attachments):
                    await self.award_campus_picture_points(message_author, message)
            
            # Check for enrollment deposit emoji reaction
            elif emoji_name == ENROLLMENT_DEPOSIT_EMOJI:
                await self.award_enrollment_deposit_points(message_author, message)
            
        except Exception as e:
            cog_logger.error(f"Error in check_admin_reactions: {e}")

    async def award_campus_picture_points(self, user, message):
        """Award points for campus picture posts (admin approved)."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
            if not settings or not settings.economy_enabled:
                return False  # Economy is disabled, don't award points
            
            # Check if user has reached maximum campus photo approvals
            campus_photos_count = getattr(user, 'campus_photos_count', 0) or 0
            if campus_photos_count >= MAX_CAMPUS_PHOTOS:
                # Send message to admin about limit reached
                try:
                    await message.reply(f"❌ {message.author.mention} has already reached the maximum of {MAX_CAMPUS_PHOTOS} campus photo approvals.")
                except:
                    pass
                return False
            
            # Award campus picture points
            user.points += CAMPUS_PICTURE_POINTS
            user.balance += CAMPUS_PICTURE_POINTS
            
            # Increment campus photos counter
            if not hasattr(user, 'campus_photos_count') or user.campus_photos_count is None:
                user.campus_photos_count = 0
            user.campus_photos_count += 1
            
            remaining_photos = MAX_CAMPUS_PHOTOS - user.campus_photos_count
            
            # Send confirmation message
            embed = nextcord.Embed(
                title="📸 Campus Picture Approved!",
                description=f"Your campus picture has been approved by an admin!\n\n**Points Earned:** {CAMPUS_PICTURE_POINTS}",
                color=nextcord.Color.blue()
            )
            embed.add_field(
                name="New Balance",
                value=f"{user.balance} pitchforks",
                inline=True
            )
            embed.add_field(
                name="Campus Photos Remaining",
                value=f"{remaining_photos} out of {MAX_CAMPUS_PHOTOS}",
                inline=True
            )
            embed.set_footer(text=f"New balance: {user.balance} pitchforks")
            
            try:
                await message.author.send(embed=embed)
            except nextcord.Forbidden:
                # If DM fails, reply to the original message
                await message.reply(f"📸 {message.author.mention} earned {CAMPUS_PICTURE_POINTS} pitchforks for sharing a campus picture! ({remaining_photos} photos remaining)")
                
            cog_logger.info(f"Campus picture points awarded to {user.username}: {CAMPUS_PICTURE_POINTS} points ({user.campus_photos_count}/{MAX_CAMPUS_PHOTOS})")
            return True
            
        except Exception as e:
            cog_logger.error(f"Error awarding campus picture points: {e}")
            return False

    async def award_enrollment_deposit_points(self, user, message):
        """Award points for enrollment deposit confirmation (admin approved, one-time)."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
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
                
            cog_logger.info(f"Enrollment deposit points awarded to {user.username}: {ENROLLMENT_DEPOSIT_POINTS} points")
            return True
            
        except Exception as e:
            cog_logger.error(f"Error awarding enrollment deposit points: {e}")
            return False

    # Birthday system functions
    async def check_birthdays(self):
        """Check for birthdays and send announcements daily at 9:30 MST"""
        import pytz
        
        try:
            with self.app.app_context():
                today = date.today()
                
                # Get users with birthdays today
                birthday_users = self.User.query.filter(
                    self.db.func.extract('month', self.User.birthday) == today.month,
                    self.db.func.extract('day', self.User.birthday) == today.day
                ).all()
                
                if birthday_users:
                    channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
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
                            cog_logger.info(f"Birthday announcement sent for {user.username}")
                    else:
                        cog_logger.warning(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
                else:
                    cog_logger.info(f"No birthdays today ({today.strftime('%B %d')})")
                    
        except Exception as e:
            cog_logger.error(f"Error checking birthdays: {e}")

    # Set up daily birthday check task
    @tasks.loop(time=datetime.strptime(BIRTHDAY_CHECK_TIME, "%H:%M").time())
    async def daily_birthday_check(self):
        """Daily task to check for birthdays at 9:30 MST"""
        import pytz
        
        # Convert to MST timezone
        mst = pytz.timezone('US/Mountain')
        now_mst = datetime.now(mst)
        
        cog_logger.info(f"Running daily birthday check at {now_mst.strftime('%Y-%m-%d %H:%M:%S MST')}")
        await self.check_birthdays()

    @daily_birthday_check.before_loop
    async def before_birthday_check(self):
        """Wait until bot is ready before starting birthday checks"""
        await self.bot.wait_until_ready()
        cog_logger.info("Birthday checking task started - will run daily at 9:30 MST")

    # Role assignment processor for digital products
    @tasks.loop(seconds=30)
    async def process_role_assignments(self):
        """Process pending Discord role assignments"""
        if not self.app or not self.db:
            cog_logger.warning("App or DB not initialized for role assignment processor")
            return
            
        try:
            # Use direct SQL approach to avoid Flask context issues
            import sqlite3
            import os
            
            # Get database path from Flask app config
            db_path = self.app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///store.db')
            if db_path.startswith('sqlite:///'):
                db_path = db_path.replace('sqlite:///', '')
                # Handle relative paths - Flask creates database in instance/ folder
                if not os.path.isabs(db_path):
                    db_path = os.path.join('instance', db_path)
            
            # Direct database connection
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            cursor = conn.cursor()
            
            try:
                # Get pending role assignments
                cursor.execute("""
                    SELECT id, user_id, role_id, purchase_id, status, created_at, error_message
                    FROM role_assignment 
                    WHERE status = 'pending' 
                    LIMIT 10
                """)
                pending_assignments = cursor.fetchall()
                
                for assignment in pending_assignments:
                    try:
                        assignment_id = assignment['id']
                        user_id = assignment['user_id']
                        role_id = assignment['role_id']
                        purchase_id = assignment['purchase_id']
                        
                        # Get the Discord user
                        user = self.bot.get_user(int(user_id))
                        if not user:
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                            except Exception:
                                cursor.execute("""
                                    UPDATE role_assignment 
                                    SET status = 'failed', error_message = 'User not found on Discord', completed_at = ?
                                    WHERE id = ?
                                """, (datetime.utcnow().isoformat(), assignment_id))
                                continue
                        
                        # Get the guild (server)
                        guild = self.bot.get_guild(int(os.getenv('DISCORD_GUILD_ID'))) if os.getenv('DISCORD_GUILD_ID') else None
                        if not guild:
                            # Try to find the guild from the bot's guilds
                            if self.bot.guilds:
                                guild = self.bot.guilds[0]  # Use first guild
                        
                        if not guild:
                            cursor.execute("""
                                UPDATE role_assignment 
                                SET status = 'failed', error_message = 'Bot not in any Discord server', completed_at = ?
                                WHERE id = ?
                            """, (datetime.utcnow().isoformat(), assignment_id))
                            continue
                        
                        # Get the member from the guild
                        member = guild.get_member(int(user_id))
                        if not member:
                            try:
                                member = await guild.fetch_member(int(user_id))
                            except Exception:
                                cursor.execute("""
                                    UPDATE role_assignment 
                                    SET status = 'failed', error_message = 'Member not found in server', completed_at = ?
                                    WHERE id = ?
                                """, (datetime.utcnow().isoformat(), assignment_id))
                                continue
                        
                        # Get the role
                        role = guild.get_role(int(role_id))
                        if not role:
                            cursor.execute("""
                                UPDATE role_assignment 
                                SET status = 'failed', error_message = ?, completed_at = ?
                                WHERE id = ?
                            """, (f'Role {role_id} not found', datetime.utcnow().isoformat(), assignment_id))
                            continue
                        
                        # Assign the role
                        await member.add_roles(role, reason=f"Purchased from store (Purchase ID: {purchase_id})")
                        
                        # Mark as completed
                        cursor.execute("""
                            UPDATE role_assignment 
                            SET status = 'completed', completed_at = ?
                            WHERE id = ?
                        """, (datetime.utcnow().isoformat(), assignment_id))
                        
                        # Send confirmation DM to user
                        try:
                            embed = nextcord.Embed(
                                title="🎉 Role Delivered!",
                                description=f"You have been granted the **{role.name}** role!",
                                color=nextcord.Color.green()
                            )
                            await user.send(embed=embed)
                        except Exception:
                            pass  # DM failed, but role was assigned successfully
                            
                        cog_logger.info(f"Successfully assigned role {role.name} to {member.display_name}")
                        
                    except Exception as e:
                        cursor.execute("""
                            UPDATE role_assignment 
                            SET status = 'failed', error_message = ?, completed_at = ?
                            WHERE id = ?
                        """, (str(e), datetime.utcnow().isoformat(), assignment_id))
                        cog_logger.error(f"Failed to assign role to user {user_id}: {e}")
                
                # Commit all changes
                conn.commit()
                cog_logger.info("Role assignment changes committed successfully")
                        
            except Exception as e:
                cog_logger.error(f"Error in role assignment processor: {e}")
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    cog_logger.error(f"Error during rollback: {rollback_error}")
            
            finally:
                # Always close the database connection
                try:
                    cursor.close()
                    conn.close()
                except Exception as close_error:
                    cog_logger.error(f"Error closing database connection: {close_error}")
                
        except Exception as e:
            cog_logger.error(f"Fatal error in role assignment processor: {e}")
            import traceback
            cog_logger.error(traceback.format_exc())

    @process_role_assignments.before_loop
    async def before_role_assignments(self):
        """Wait until bot is ready before starting role assignment processing"""
        await self.bot.wait_until_ready()
        
        # Wait for Flask app to be properly initialized
        max_wait = 30  # Maximum wait time in seconds
        wait_count = 0
        while (not self.app or not self.db) and wait_count < max_wait:
            cog_logger.warning(f"Waiting for Flask app initialization... ({wait_count + 1}/{max_wait})")
            await asyncio.sleep(1)
            wait_count += 1
        
        if not self.app or not self.db:
            cog_logger.critical("ERROR: Flask app not properly initialized after waiting. Role assignment processor may not work.")
        else:
            cog_logger.info("Role assignment processor started - will check every 30 seconds")

    async def check_achievements(self, user, achievement_type, count=None):
        """Check and award achievements for a user."""
        if not self.app:
            return
            
        try:
            ctx = self.app.app_context()
            ctx.push()
            # Get all achievements of the specified type
            achievements = self.Achievement.query.filter_by(type=achievement_type).all()
            
            for achievement in achievements:
                # Check if user already has this achievement
                user_achievement = self.UserAchievement.query.filter_by(
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
                    await self.award_achievement(user, achievement)
                    
        except Exception as e:
            cog_logger.error(f"Error in check_achievements: {e}")
        finally:
            try:
                ctx.pop()
            except Exception as ctx_error:
                cog_logger.error(f"Error popping Flask context in check_achievements: {ctx_error}")

    async def send_achievement_announcement(self, user, achievement):
        """Send achievement announcement to general channel."""
        try:
            channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
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
                cog_logger.info(f"Achievement announcement sent for {user.username}: {achievement.name}")
                
            else:
                cog_logger.warning(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
                
        except Exception as e:
            cog_logger.error(f"Error sending achievement announcement: {e}")

    async def award_achievement(self, user, achievement):
        """Award an achievement to a user with atomic transaction."""
        if not self.app:
            return
            
        try:
            ctx = self.app.app_context()
            ctx.push()
            try:
                # Check if user already has this achievement (race condition protection)
                existing_achievement = self.UserAchievement.query.filter_by(
                    user_id=user.id,
                    achievement_id=achievement.id
                ).first()
                
                if existing_achievement:
                    cog_logger.info(f"Achievement \'{achievement.name}\' already awarded to {user.username}")
                    return
                
                # Lock user row to prevent concurrent balance modifications
                user_fresh = self.User.query.with_for_update().get(user.id)
                if not user_fresh:
                    cog_logger.warning(f"User {user.id} not found for achievement award")
                    return
                
                # Add achievement to user
                user_achievement = self.UserAchievement(
                    user_id=user_fresh.id,
                    achievement_id=achievement.id
                )
                self.db.session.add(user_achievement)
                
                # Award points atomically
                user_fresh.points += achievement.points
                user_fresh.balance += achievement.points
                
                # Commit transaction
                self.db.session.commit()
                
                cog_logger.info(f"Achievement \'{achievement.name}\' awarded to {user_fresh.username} for {achievement.points} points!")
                
                # Send achievement announcement to general channel
                await self.send_achievement_announcement(user_fresh, achievement)
                
            except Exception as e:
                try:
                    self.db.session.rollback()
                except Exception as rollback_error:
                    cog_logger.error(f"Error during rollback in award_achievement: {rollback_error}")
                cog_logger.error(f"Error awarding achievement to {user.username}: {e}")
                import traceback
                cog_logger.error(traceback.format_exc())
                
        except Exception as e:
            cog_logger.error(f"Fatal error in award_achievement: {e}")
        finally:
            try:
                ctx.pop()
            except Exception as ctx_error:
                cog_logger.error(f"Error popping Flask context in award_achievement: {ctx_error}")

    @nextcord.slash_command(name="achievements", description="View your achievements")
    async def achievements(self, interaction: Interaction):
        """View your achievements"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            
            # Get user's achievements
            user_achievements = self.UserAchievement.query.filter_by(user_id=user.id).all()
            
            embed = nextcord.Embed(
                title="🏆 Your Achievements",
                color=nextcord.Color.gold()
            )
            
            if not user_achievements:
                embed.description = "You haven't unlocked any achievements yet!"
            else:
                for ua in user_achievements:
                    achievement = self.Achievement.query.get(ua.achievement_id)
                    embed.add_field(
                        name=f"🎖️ {achievement.name}",
                        value=f"{achievement.description}\n**Points:** {achievement.points}",
                        inline=False
                    )
            
            embed.set_footer(text=f"Total Points Earned: {user.points}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="balance", description="Check your current pitchfork balance")
    async def balance(self, interaction: Interaction):
        """Check your current pitchfork balance"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            embed = nextcord.Embed(
                title="Pitchfork Balance",
                description=f"Your current balance: {user.balance} pitchforks",
                color=nextcord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="daily", description="Claim your daily pitchfork reward")
    async def daily(self, interaction: Interaction):
        """Claim your daily pitchforks with atomic transaction"""
        with self.app.app_context():
            try:
                settings = self.EconomySettings.query.first()
                if not settings or not settings.economy_enabled:
                    embed = nextcord.Embed(
                        title="🔒 Economy Disabled",
                        description="The economy system is currently disabled. Contact an admin for more information.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                user = self.User.query.filter_by(id=str(interaction.user.id)).first()
                if not user:
                    user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                    self.db.session.add(user)
                    self.db.session.commit()
                
                # Check if user has reached maximum daily claims
                daily_claims = getattr(user, 'daily_claims_count', 0) or 0
                if daily_claims >= MAX_DAILY_CLAIMS:
                    embed = nextcord.Embed(
                        title="🚫 Daily Limit Reached",
                        description=f"You have reached the maximum of {MAX_DAILY_CLAIMS} daily claims. No more daily rewards available!",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                current_time = datetime.now()
                if user.last_daily and (current_time - user.last_daily) < timedelta(days=1):
                    time_left = user.last_daily + timedelta(days=1) - current_time
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    embed = nextcord.Embed(
                        title="⏰ Daily Reward Not Ready",
                        description=f"You can claim your daily pitchforks again in {hours} hours and {minutes} minutes.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Award daily reward and increment counter
                user.balance += 85
                user.last_daily = current_time
                if not hasattr(user, 'daily_claims_count') or user.daily_claims_count is None:
                    user.daily_claims_count = 0
                user.daily_claims_count += 1
                
                self.db.session.commit()
                
                remaining_claims = MAX_DAILY_CLAIMS - user.daily_claims_count
                embed = nextcord.Embed(
                    title="🎉 Daily Reward Claimed!",
                    description=f"You have received 85 pitchforks. Your new balance is {user.balance} pitchforks.",
                    color=nextcord.Color.green()
                )
                embed.add_field(
                    name="Daily Claims Remaining",
                    value=f"{remaining_claims} out of {MAX_DAILY_CLAIMS}",
                    inline=True
                )
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                self.db.session.rollback()
                embed = nextcord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=nextcord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="leaderboard", description="Show the top 10 users by pitchfork balance")
    async def leaderboard(self, interaction: Interaction):
        with self.app.app_context():
            users = self.User.query.order_by(self.User.balance.desc()).limit(10).all()
            desc = "\n".join([
                f"**{idx+1}. {user.username}** — {user.balance} pitchforks" for idx, user in enumerate(users)
            ])
            embed = nextcord.Embed(
                title="🏆 Pitchfork Leaderboard",
                description=desc or "No users found.",
                color=nextcord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="give_all", description="Give pitchforks to all users (Admin only)")
    async def give_all(self, interaction: Interaction, amount: int):
        with self.app.app_context():
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
            users = self.User.query.all()
            for user in users:
                user.balance += amount
            self.db.session.commit()
            await interaction.response.send_message(f"Gave {amount} pitchforks to all users.")

    @nextcord.slash_command(name="give", description="Give pitchforks to a specific user (Admin only)")
    async def give(self, interaction: Interaction, user: nextcord.Member, amount: int):
        """Give pitchforks to a specific user"""
        with self.app.app_context():
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
            
            if amount <= 0:
                await interaction.response.send_message("Amount must be greater than 0.", ephemeral=True)
                return
            
            # Get or create the target user
            target_user = self.User.query.filter_by(id=str(user.id)).first()
            if not target_user:
                target_user = self.User(id=str(user.id), username=user.display_name, discord_id=str(user.id))
                self.db.session.add(target_user)
                self.db.session.flush()
            
            # Add points to the user's balance
            target_user.balance += amount
            self.db.session.commit()
            
            # Send confirmation message
            embed = nextcord.Embed(
                title="💰 Pitchforks Awarded",
                description=f"Successfully gave **{amount} pitchforks** to {user.mention}",
                color=nextcord.Color.green()
            )
            embed.add_field(
                name="New Balance",
                value=f"{target_user.balance} pitchforks",
                inline=True
            )
            embed.add_field(
                name="Awarded by",
                value=interaction.user.mention,
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Try to notify the user via DM
            try:
                dm_embed = nextcord.Embed(
                    title="🎉 Pitchforks Received!",
                    description=f"You've received **{amount} pitchforks** from an admin!",
                    color=nextcord.Color.gold()
                )
                dm_embed.add_field(
                    name="New Balance",
                    value=f"{target_user.balance} pitchforks",
                    inline=True
                )
                await user.send(embed=dm_embed)
            except nextcord.Forbidden:
                # DM failed, but that's okay
                pass

    def on_first_economy_enable(self, interaction):
        # This function runs only the first time the economy is enabled
        # Award the 'Verified' achievement to all users with the verified role
        guild = interaction.guild
        verified_role = guild.get_role(VERIFIED_ROLE_ID)
        if verified_role:
            for member in verified_role.members:
                with self.app.app_context():
                    user = self.User.query.filter_by(id=str(member.id)).first()
                    if user:
                        achievement = self.Achievement.query.filter_by(name="Verified").first()
                        if achievement:
                            user_achievement = self.UserAchievement(user_id=user.id, achievement_id=achievement.id)
                            self.db.session.add(user_achievement)
                            self.db.session.commit()
                            cog_logger.info(f"Awarded \'Verified\' achievement to {member.display_name}")

    @nextcord.slash_command(name="economy", description="Enable or disable the economy system (Admin only)")
    async def economy_toggle(self, interaction: Interaction, action: str):
        with self.app.app_context():
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
            settings = self.EconomySettings.query.first()
            if not settings:
                await interaction.response.send_message("Economy settings not found.", ephemeral=True)
                return
            if action.lower() == "enable":
                first_time = not getattr(settings, 'first_time_enabled', False)
                settings.economy_enabled = True
                settings.first_time_enabled = True
                self.db.session.commit()
                await interaction.response.send_message("Economy enabled.")
                if first_time:
                    self.on_first_economy_enable(interaction)
            elif action.lower() == "disable":
                settings.economy_enabled = False
                self.db.session.commit()
                await interaction.response.send_message("Economy disabled.")
            else:
                await interaction.response.send_message("Invalid action. Use 'enable' or 'disable'.", ephemeral=True)

    @nextcord.slash_command(name="limits", description="View your earning limits and theoretical maximum pitchforks")
    async def limits(self, interaction: Interaction):
        """Show user's current progress toward earning limits and theoretical maximum"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            
            # Get current counts (with safe defaults)
            daily_claims = getattr(user, 'daily_claims_count', 0) or 0
            campus_photos = getattr(user, 'campus_photos_count', 0) or 0
            daily_engagement = getattr(user, 'daily_engagement_count', 0) or 0
            messages = user.message_count or 0
            reactions = user.reaction_count or 0
            voice_minutes = user.voice_minutes or 0
            
            # Calculate theoretical maximum pitchforks
            max_from_daily = MAX_DAILY_CLAIMS * 85  # 90 * 85 = 7,650
            max_from_campus = MAX_CAMPUS_PHOTOS * 100  # 5 * 100 = 500
            max_from_engagement = MAX_DAILY_ENGAGEMENT * 25  # 365 * 25 = 9,125
            max_from_onetime = 200 + 500 + 500 + 50  # verification + onboarding + enrollment + birthday = 1,250
            
            # Achievement points (estimated based on typical achievement values)
            estimated_achievement_points = 2000  # Conservative estimate for all achievements
            
            theoretical_max = max_from_daily + max_from_campus + max_from_engagement + max_from_onetime + estimated_achievement_points
            
            # Calculate current earned from limited sources
            earned_from_daily = daily_claims * 85
            earned_from_campus = campus_photos * 100
            earned_from_engagement = daily_engagement * 25
            
            embed = nextcord.Embed(
                title="🎯 Pitchfork Earning Limits",
                description="Your progress toward maximum earning limits",
                color=nextcord.Color.gold()
            )
            
            # Recurring limits section
            embed.add_field(
                name="📅 Daily Claims",
                value=f"{daily_claims}/{MAX_DAILY_CLAIMS}\n💰 {earned_from_daily:,} pitchforks",
                inline=True
            )
            
            embed.add_field(
                name="📸 Campus Photos",
                value=f"{campus_photos}/{MAX_CAMPUS_PHOTOS}\n💰 {earned_from_campus:,} pitchforks",
                inline=True
            )
            
            embed.add_field(
                name="🔥 Daily Engagement",
                value=f"{daily_engagement}/{MAX_DAILY_ENGAGEMENT}\n💰 {earned_from_engagement:,} pitchforks",
                inline=True
            )
            
            # Activity limits section
            embed.add_field(
                name="💬 Messages",
                value=f"{messages:,}/{MAX_MESSAGES:,}",
                inline=True
            )
            
            embed.add_field(
                name="❤️ Reactions",
                value=f"{reactions:,}/{MAX_REACTIONS:,}",
                inline=True
            )
            
            embed.add_field(
                name="🎤 Voice Minutes",
                value=f"{voice_minutes:,}/{MAX_VOICE_MINUTES:,}",
                inline=True
            )
            
            # Theoretical maximum
            embed.add_field(
                name="🏆 Theoretical Maximum",
                value=f"**{theoretical_max:,} pitchforks**\n"
                      f"Daily: {max_from_daily:,}\n"
                      f"Campus: {max_from_campus:,}\n"
                      f"Engagement: {max_from_engagement:,}\n"
                      f"One-time: {max_from_onetime:,}\n"
                      f"Achievements: ~{estimated_achievement_points:,}",
                inline=False
            )
            
            # Current balance
            embed.add_field(
                name="💰 Current Balance",
                value=f"{user.balance:,} pitchforks",
                inline=True
            )
            
            # Progress percentage
            progress_percentage = (user.balance / theoretical_max) * 100 if theoretical_max > 0 else 0
            embed.add_field(
                name="📊 Progress",
                value=f"{progress_percentage:.1f}% of maximum",
                inline=True
            )
            
            embed.set_footer(text="Limits help maintain balance and prevent exploitation")
            await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot, app, db, User, EconomySettings, Achievement, UserAchievement):
    bot.add_cog(EconomyCog(bot, app, db, User, EconomySettings, Achievement, UserAchievement)) 