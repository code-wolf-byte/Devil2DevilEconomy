import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        
        # Start background tasks
        self.daily_birthday_check.start()
        self.process_role_assignments.start()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.daily_birthday_check.cancel()
        self.process_role_assignments.cancel()

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
            
            # Ensure message_count is not None
            if user.message_count is None:
                user.message_count = 0
            user.message_count += 1
            self.db.session.commit()
            
            # Check message achievements
            await self.check_achievements(user, 'message', user.message_count)

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
            
            # Ensure reaction_count is not None
            if user_obj.reaction_count is None:
                user_obj.reaction_count = 0
            user_obj.reaction_count += 1
            self.db.session.commit()
            
            # Check reaction achievements
            await self.check_achievements(user_obj, 'reaction', user_obj.reaction_count)

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
                # Ensure voice_minutes is not None
                if user.voice_minutes is None:
                    user.voice_minutes = 0
                user.voice_minutes += 1  # Increment by 1 minute
                self.db.session.commit()
                
                # Check voice achievements
                await self.check_achievements(user, 'voice')

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
                    print(f"Verification bonus already received by {member.display_name}")
                    return
                
                # Award verification bonus atomically
                user.balance += 200
                user.verification_bonus_received = True
                self.db.session.commit()
                print(f"Verification bonus awarded to {member.display_name}: 200 points")
                
            except Exception as e:
                self.db.session.rollback()
                print(f"Error awarding verification bonus to {member.display_name}: {e}")
                import traceback
                traceback.print_exc()
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
                        print(f"Sent verification welcome message for {member.display_name}")
                except Exception as e:
                    print(f"Error sending verification welcome message: {e}")

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
                    print(f"Onboarding bonus already received by {member.display_name}")
                    return
                
                # Award onboarding bonus atomically
                user.balance += 500
                user.onboarding_bonus_received = True
                self.db.session.commit()
                print(f"Onboarding bonus awarded to {member.display_name}: 500 points")
                
            except Exception as e:
                self.db.session.rollback()
                print(f"Error awarding onboarding bonus to {member.display_name}: {e}")
                import traceback
                traceback.print_exc()
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
                    print(f"Sent onboarding bonus DM to {member.display_name}")
                except:
                    if GENERAL_CHANNEL_ID:
                        general_channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
                        if general_channel:
                            await general_channel.send(f"{member.mention}", embed=embed)
                            print(f"Sent onboarding bonus message in general for {member.display_name}")
            except Exception as e:
                print(f"Error sending onboarding bonus message: {e}")

    async def award_daily_engagement_points(self, user, message):
        """Award points for daily engagement (admin approved)."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
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
            print(f"Error in check_admin_reactions: {e}")

    async def award_campus_picture_points(self, user, message):
        """Award points for campus picture posts (admin approved)."""
        try:
            # Check if economy is enabled
            settings = self.EconomySettings.query.first()
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
                
            print(f"Enrollment deposit points awarded to {user.username}: {ENROLLMENT_DEPOSIT_POINTS} points")
            return True
            
        except Exception as e:
            print(f"Error awarding enrollment deposit points: {e}")
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
                            print(f"Birthday announcement sent for {user.username}")
                    else:
                        print(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
                else:
                    print(f"No birthdays today ({today.strftime('%B %d')})")
                    
        except Exception as e:
            print(f"Error checking birthdays: {e}")

    # Set up daily birthday check task
    @tasks.loop(time=datetime.strptime(BIRTHDAY_CHECK_TIME, "%H:%M").time())
    async def daily_birthday_check(self):
        """Daily task to check for birthdays at 9:30 MST"""
        import pytz
        
        # Convert to MST timezone
        mst = pytz.timezone('US/Mountain')
        now_mst = datetime.now(mst)
        
        print(f"Running daily birthday check at {now_mst.strftime('%Y-%m-%d %H:%M:%S MST')}")
        await self.check_birthdays()

    @daily_birthday_check.before_loop
    async def before_birthday_check(self):
        """Wait until bot is ready before starting birthday checks"""
        await self.bot.wait_until_ready()
        print("Birthday checking task started - will run daily at 9:30 MST")

    # Role assignment processor for digital products
    @tasks.loop(seconds=30)
    async def process_role_assignments(self):
        """Process pending Discord role assignments"""
        try:
            with self.app.app_context():
                from app import RoleAssignment
                
                # Get pending role assignments
                pending_assignments = RoleAssignment.query.filter_by(status='pending').limit(10).all()
                
                for assignment in pending_assignments:
                    try:
                        # Get the Discord user
                        user = self.bot.get_user(int(assignment.user_id))
                        if not user:
                            try:
                                user = await self.bot.fetch_user(int(assignment.user_id))
                            except Exception:
                                assignment.status = 'failed'
                                assignment.error_message = 'User not found on Discord'
                                assignment.completed_at = datetime.utcnow()
                                continue
                        
                        # Get the guild (server)
                        guild = self.bot.get_guild(int(os.getenv('DISCORD_GUILD_ID'))) if os.getenv('DISCORD_GUILD_ID') else None
                        if not guild:
                            # Try to find the guild from the bot's guilds
                            if self.bot.guilds:
                                guild = self.bot.guilds[0]  # Use first guild
                        
                        if not guild:
                            assignment.status = 'failed'
                            assignment.error_message = 'Bot not in any Discord server'
                            assignment.completed_at = datetime.utcnow()
                            continue
                        
                        # Get the member from the guild
                        member = guild.get_member(int(assignment.user_id))
                        if not member:
                            try:
                                member = await guild.fetch_member(int(assignment.user_id))
                            except Exception:
                                assignment.status = 'failed'
                                assignment.error_message = 'Member not found in server'
                                assignment.completed_at = datetime.utcnow()
                                continue
                        
                        # Get the role
                        role = guild.get_role(int(assignment.role_id))
                        if not role:
                            assignment.status = 'failed'
                            assignment.error_message = f'Role {assignment.role_id} not found'
                            assignment.completed_at = datetime.utcnow()
                            continue
                        
                        # Assign the role
                        await member.add_roles(role, reason=f"Purchased from store (Purchase ID: {assignment.purchase_id})")
                        
                        # Mark as completed
                        assignment.status = 'completed'
                        assignment.completed_at = datetime.utcnow()
                        
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
                            
                        print(f"Successfully assigned role {role.name} to {member.display_name}")
                        
                    except Exception as e:
                        assignment.status = 'failed'
                        assignment.error_message = str(e)
                        assignment.completed_at = datetime.utcnow()
                        print(f"Failed to assign role to user {assignment.user_id}: {e}")
                
                # Commit all changes
                self.db.session.commit()
                
        except Exception as e:
            print(f"Error in role assignment processor: {e}")
            try:
                self.db.session.rollback()
            except:
                pass

    @process_role_assignments.before_loop
    async def before_role_assignments(self):
        """Wait until bot is ready before starting role assignment processing"""
        await self.bot.wait_until_ready()
        print("Role assignment processor started - will check every 30 seconds")

    async def check_achievements(self, user, achievement_type, count=None):
        """Check and award achievements for a user."""
        with self.app.app_context():
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
                print(f"Achievement announcement sent for {user.username}: {achievement.name}")
                
            else:
                print(f"Could not find general channel with ID: {GENERAL_CHANNEL_ID}")
                
        except Exception as e:
            print(f"Error sending achievement announcement: {e}")

    async def award_achievement(self, user, achievement):
        """Award an achievement to a user with atomic transaction."""
        with self.app.app_context():
            try:
                # Check if user already has this achievement (race condition protection)
                existing_achievement = self.UserAchievement.query.filter_by(
                    user_id=user.id,
                    achievement_id=achievement.id
                ).first()
                
                if existing_achievement:
                    print(f"Achievement '{achievement.name}' already awarded to {user.username}")
                    return
                
                # Lock user row to prevent concurrent balance modifications
                user_fresh = self.User.query.with_for_update().get(user.id)
                if not user_fresh:
                    print(f"User {user.id} not found for achievement award")
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
                
                print(f"Achievement '{achievement.name}' awarded to {user_fresh.username} for {achievement.points} points!")
                
                # Send achievement announcement to general channel
                await self.send_achievement_announcement(user_fresh, achievement)
                
            except Exception as e:
                self.db.session.rollback()
                print(f"Error awarding achievement to {user.username}: {e}")
                import traceback
                traceback.print_exc()

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

    @nextcord.slash_command(name="balance", description="Check your current balance")
    async def balance(self, interaction: Interaction):
        """Check your current balance"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            embed = nextcord.Embed(
                title="Balance",
                description=f"Your current balance: {user.balance} points",
                color=nextcord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="daily", description="Claim your daily points reward")
    async def daily(self, interaction: Interaction):
        """Claim your daily points with atomic transaction"""
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
                current_time = datetime.now()
                if user.last_daily and (current_time - user.last_daily) < timedelta(days=1):
                    time_left = user.last_daily + timedelta(days=1) - current_time
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    embed = nextcord.Embed(
                        title="⏰ Daily Reward Not Ready",
                        description=f"You can claim your daily points again in {hours} hours and {minutes} minutes.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                user.balance += 85
                user.last_daily = current_time
                self.db.session.commit()
                embed = nextcord.Embed(
                    title="🎉 Daily Reward Claimed!",
                    description=f"You have received 85 points. Your new balance is {user.balance} points.",
                    color=nextcord.Color.green()
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

    @nextcord.slash_command(name="leaderboard", description="Show the top 10 users by balance")
    async def leaderboard(self, interaction: Interaction):
        with self.app.app_context():
            users = self.User.query.order_by(self.User.balance.desc()).limit(10).all()
            desc = "\n".join([
                f"**{idx+1}. {user.username}** — {user.balance} points" for idx, user in enumerate(users)
            ])
            embed = nextcord.Embed(
                title="🏆 Leaderboard",
                description=desc or "No users found.",
                color=nextcord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="give_all", description="Give points to all users (Admin only)")
    async def give_all(self, interaction: Interaction, amount: int):
        with self.app.app_context():
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
            users = self.User.query.all()
            for user in users:
                user.balance += amount
            self.db.session.commit()
            await interaction.response.send_message(f"Gave {amount} points to all users.")

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
                            print(f"Awarded 'Verified' achievement to {member.display_name}")

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

def setup(bot, app, db, User, EconomySettings, Achievement, UserAchievement):
    bot.add_cog(EconomyCog(bot, app, db, User, EconomySettings, Achievement, UserAchievement)) 