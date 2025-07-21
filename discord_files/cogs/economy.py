import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import logging
import os
import json
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
import traceback
from discord import app_commands

# Configure logging
cog_logger = logging.getLogger('economy_cog')
cog_logger.setLevel(logging.INFO)

# Constants
DAILY_ENGAGEMENT_POINTS = int(os.getenv('DAILY_ENGAGEMENT_POINTS', 25))
CAMPUS_PICTURE_POINTS = int(os.getenv('CAMPUS_PICTURE_POINTS', 100))
ENROLLMENT_DEPOSIT_POINTS = int(os.getenv('ENROLLMENT_DEPOSIT_POINTS', 500))
BIRTHDAY_SETUP_POINTS = int(os.getenv('BIRTHDAY_SETUP_POINTS', 50))
DAILY_POINTS = int(os.getenv('DAILY_POINTS', 85))
MAX_DAILY_CLAIMS = 90  # Lifetime limit for daily command claims

# Emoji constants
CAMPUS_PICTURE_EMOJI = os.getenv('CAMPUS_PICTURE_EMOJI', 'campus_photo')
DAILY_ENGAGEMENT_EMOJI = os.getenv('DAILY_ENGAGEMENT_EMOJI', 'daily_engage')
ENROLLMENT_DEPOSIT_EMOJI = os.getenv('ENROLLMENT_DEPOSIT_EMOJI', 'deposit_check')

# Channel and role IDs
GENERAL_CHANNEL_ID = os.getenv('GENERAL_CHANNEL_ID')
VERIFIED_ROLE_ID = os.getenv('VERIFIED_ROLE_ID')
ONBOARDING_ROLE_IDS = os.getenv('ONBOARDING_ROLE_IDS', '').split(',') if os.getenv('ONBOARDING_ROLE_IDS') else []
BIRTHDAY_CHECK_TIME = os.getenv('BIRTHDAY_CHECK_TIME', '09:30')

# Role management constants
UNVERIFIED_ROLE_NAME = os.getenv('UNVERIFIED_ROLE_NAME', 'Unverified')  # Role that triggers removal
COMMITTED_ROLE_NAME = os.getenv('COMMITTED_ROLE_NAME', 'Committed')  # Role to remove/prevent from unverified users

def get_role_by_name(guild, role_name):
    """Helper function to get a role by name"""
    if not guild or not role_name:
        return None
    
    for role in guild.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None

class RoleRemovalConfirmationView(discord.ui.View):
    def __init__(self, cog, admin_user_id, affected_users):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.admin_user_id = admin_user_id
        self.affected_users = affected_users

    @discord.ui.button(label='✅ Confirm Removal', style=discord.ButtonStyle.danger)
    async def confirm_removal(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user clicking is the same admin who initiated the command
        if interaction.user.id != self.admin_user_id:
            await interaction.response.send_message("❌ Only the admin who initiated this command can confirm.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            print(f"Confirmed bulk role removal initiated by {interaction.user.name}")
            
            # Remove roles from affected users
            removed_count = 0
            for user_data in self.affected_users:
                member = user_data['member']
                try:
                    committed_role = get_role_by_name(member.guild, COMMITTED_ROLE_NAME)
                    if committed_role and committed_role in member.roles:
                        await member.remove_roles(committed_role, reason="Admin confirmed bulk removal")
                        await self.cog.log_role_removal(member, "Admin confirmed bulk removal")
                        removed_count += 1
                except Exception as e:
                    cog_logger.error(f"Failed to remove role from {member.name}: {e}")
            
            # Create success embed
            embed = discord.Embed(
                title="🚫 Role Removal Complete",
                description=f"Successfully removed restricted role from **{removed_count}** users.",
                color=0xff4444
            )
            embed.add_field(
                name="Details",
                value=f"• Committed Role: `{COMMITTED_ROLE_NAME}`\n• Unverified Role: `{UNVERIFIED_ROLE_NAME}`",
                inline=False
            )
            embed.add_field(
                name="Action Taken",
                value="✅ All affected users have been processed and logged.",
                inline=False
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
            print(f"Bulk role removal completed. {removed_count} roles removed.")
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred during role removal: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            cog_logger.error(f"Error in confirmed role removal: {e}")

    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_removal(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user clicking is the same admin who initiated the command
        if interaction.user.id != self.admin_user_id:
            await interaction.response.send_message("❌ Only the admin who initiated this command can cancel.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Operation Cancelled",
            description="Role removal operation has been cancelled. No roles were removed.",
            color=0x95a5a6
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        print(f"Role removal cancelled by {interaction.user.name}")

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True

class EconomyCog(commands.Cog):
    def __init__(self, bot, app, db, User, EconomySettings, Achievement, UserAchievement):
        self.bot = bot
        self.app = app
        self.db = db
        self.User = User
        self.EconomySettings = EconomySettings
        self.Achievement = Achievement
        self.UserAchievement = UserAchievement
        # Removed role_assignment_queue since we're using direct function calls now

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        try:
            self.daily_birthday_check.cancel()
            self.monitor_restricted_role_task.cancel()
        except:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready"""
        cog_logger.info("Economy cog is ready!")
        
        # Start background tasks only after bot is ready
        try:
            if not self.daily_birthday_check.is_running():
                self.daily_birthday_check.start()
            if not self.monitor_restricted_role_task.is_running():
                self.monitor_restricted_role_task.start()
            print("Background tasks started successfully!")
        except Exception as e:
            print(f"Warning: Could not start background tasks: {e}")
        
        # Sync slash commands
        await self.bot.tree.sync()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        with self.app.app_context():
            try:
                # Get or create user
                user = self.User.query.filter_by(id=str(message.author.id)).first()
                if not user:
                    user = self.User(
                        id=str(message.author.id),
                        username=message.author.name,
                        discord_id=str(message.author.id),
                        avatar_url=str(message.author.avatar.url) if message.author.avatar else None
                    )
                    self.db.session.add(user)
                    self.db.session.commit()
                
                # Update message count
                user.message_count += 1
                self.db.session.commit()
                
                # Check for message-based achievements
                await self.check_achievements(user, 'messages', user.message_count)
                
            except Exception as e:
                cog_logger.error(f"Error processing message: {e}")

    async def process_reaction(self, payload):
        """Process reaction data - can be called from main.py or internally"""
        if payload.user_id == self.bot.user.id:
            return
        
        with self.app.app_context():
            try:
                # Get the channel and message
                channel = self.bot.get_channel(payload.channel_id)
                if not channel:
                    return
                
                try:
                    message = await channel.fetch_message(payload.message_id)
                except Exception as e:
                    return
                
                # Create a fake reaction object for compatibility
                class FakeReaction:
                    def __init__(self, message, emoji):
                        self.message = message
                        self.emoji = emoji
                        self.count = 1
                
                reaction = FakeReaction(message, payload.emoji)
                
                # Check if this is an admin reaction
                # Get the member from the guild instead of just the user
                guild = channel.guild
                if guild:
                    member = guild.get_member(payload.user_id)
                    if member and member.guild_permissions.administrator:
                        await self.check_admin_reactions(reaction, member)
                
            except Exception as e:
                cog_logger.error(f"Error processing reaction: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        with self.app.app_context():
            try:
                # Get or create user
                user = self.User.query.filter_by(id=str(member.id)).first()
                if not user:
                    user = self.User(
                        id=str(member.id),
                        username=member.name,
                        discord_id=str(member.id)
                    )
                    self.db.session.add(user)
                    self.db.session.commit()
                
                # Update voice minutes (simplified tracking)
                if before.channel is None and after.channel is not None:
                    # User joined a voice channel
                    user.voice_minutes += 1
                    self.db.session.commit()
                    
                    # Check for voice-based achievements
                    await self.check_achievements(user, 'voice', user.voice_minutes)
                
            except Exception as e:
                cog_logger.error(f"Error processing voice state update: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot:
            return
        
        with self.app.app_context():
            try:
                # Check for verification bonus
                if VERIFIED_ROLE_ID:
                    verified_role = after.guild.get_role(int(VERIFIED_ROLE_ID))
                    if verified_role and verified_role in after.roles and verified_role not in before.roles:
                        await self.handle_verification_bonus(after)
                
                # Check for onboarding bonuses
                if ONBOARDING_ROLE_IDS:
                    for role_id in ONBOARDING_ROLE_IDS:
                        if role_id.strip():
                            onboarding_role = after.guild.get_role(int(role_id.strip()))
                            if onboarding_role and onboarding_role in after.roles and onboarding_role not in before.roles:
                                await self.handle_onboarding_bonus(after)
                                break
                
                # Monitor and prevent restricted role assignment
                await self.monitor_restricted_role(before, after)
                
            except Exception as e:
                cog_logger.error(f"Error processing member update: {e}")
    
    async def monitor_restricted_role(self, before, after):
        """Monitor and prevent assignment of committed role to unverified users"""
        try:
            committed_role = get_role_by_name(after.guild, COMMITTED_ROLE_NAME)
            unverified_role = get_role_by_name(after.guild, UNVERIFIED_ROLE_NAME)
            
            if not committed_role or not unverified_role:
                return
            
            # Check if the committed role was just added
            if committed_role in after.roles and committed_role not in before.roles:
                # Someone just got the committed role, remove it immediately if they're unverified
                if unverified_role in after.roles:
                    await after.remove_roles(committed_role, reason="Committed role automatically removed from unverified user")
                    await self.log_role_removal(after, "Committed role prevented from being assigned to unverified user")
                    cog_logger.info(f"Prevented committed role assignment to unverified user {after.name} ({after.id})")
            
            # Check if someone with the unverified role has the committed role
            if unverified_role in after.roles and committed_role in after.roles:
                await after.remove_roles(committed_role, reason="Committed role removed due to unverified status")
                await self.log_role_removal(after, "Has unverified role")
                cog_logger.info(f"Removed committed role from unverified user {after.name} ({after.id})")
                
        except Exception as e:
            cog_logger.error(f"Error monitoring restricted role: {e}")
    
    async def log_role_removal(self, member, reason):
        """Log role removal with member details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] ROLE REMOVED: {member.name}#{member.discriminator} (ID: {member.id}) - Reason: {reason}"
        
        # Print to console
        print(log_message)
        
        # Log to file if needed
        cog_logger.info(log_message)
        
        # Optionally, you can send to a specific channel for admin monitoring
        # Uncomment and set ADMIN_LOG_CHANNEL_ID in .env if you want channel logging
        # admin_log_channel_id = os.getenv('ADMIN_LOG_CHANNEL_ID')
        # if admin_log_channel_id:
        #     channel = self.bot.get_channel(int(admin_log_channel_id))
        #     if channel:
        #         await channel.send(f"🚫 **Role Removed**: {member.mention} - {reason}")
    
    async def scan_and_remove_restricted_roles(self):
        """Scan all members and remove committed role from those with unverified role"""
        removed_count = 0
        for guild in self.bot.guilds:
            try:
                committed_role = get_role_by_name(guild, COMMITTED_ROLE_NAME)
                unverified_role = get_role_by_name(guild, UNVERIFIED_ROLE_NAME)
                
                if not committed_role or not unverified_role:
                    continue
                
                for member in guild.members:
                    if member.bot:
                        continue
                    
                    # If member has both unverified role and committed role, remove committed role
                    if unverified_role in member.roles and committed_role in member.roles:
                        try:
                            await member.remove_roles(committed_role, reason="Bulk removal: has unverified role")
                            await self.log_role_removal(member, "Bulk scan - has unverified role")
                            removed_count += 1
                        except Exception as e:
                            cog_logger.error(f"Failed to remove role from {member.name}: {e}")
                            
            except Exception as e:
                cog_logger.error(f"Error scanning guild {guild.name}: {e}")
        
        return removed_count
    
    async def get_affected_users(self):
        """Get list of users who would be affected by role removal (for confirmation)"""
        affected_users = []
        for guild in self.bot.guilds:
            try:
                committed_role = get_role_by_name(guild, COMMITTED_ROLE_NAME)
                unverified_role = get_role_by_name(guild, UNVERIFIED_ROLE_NAME)
                
                if not committed_role or not unverified_role:
                    continue
                
                for member in guild.members:
                    if member.bot:
                        continue
                    
                    # If member has both unverified role and committed role
                    if unverified_role in member.roles and committed_role in member.roles:
                        affected_users.append({
                            'name': f"{member.name}#{member.discriminator}",
                            'id': member.id,
                            'member': member
                        })
                        
            except Exception as e:
                cog_logger.error(f"Error scanning guild {guild.name}: {e}")
        
        return affected_users

    async def handle_verification_bonus(self, member):
        """Handle verification role bonus"""
        with self.app.app_context():
            try:
                user = self.User.query.filter_by(id=str(member.id)).first()
                if not user:
                    user = self.User(
                        id=str(member.id),
                        username=member.name,
                        discord_id=str(member.id)
                    )
                    self.db.session.add(user)
                    self.db.session.flush()
                
                # Check if user already received verification bonus
                if not user.verification_bonus_received:
                    user.balance += 200
                    user.points += 200
                    user.verification_bonus_received = True
                    self.db.session.commit()
                    
                    # Send announcement
                    if GENERAL_CHANNEL_ID:
                        channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                        if channel:
                            embed = discord.Embed(
                                title="🎉 Verification Bonus!",
                                description=f"Congratulations {member.mention}! You've received **200 pitchforks** for getting verified!",
                                color=discord.Color.gold()
                            )
                            embed.add_field(
                                name="💰 New Balance",
                                value=f"{user.balance} pitchforks",
                                inline=True
                            )
                            await channel.send(embed=embed)
                    
                    cog_logger.info(f"Verification bonus awarded to {member.name}: 200 points")
                
            except Exception as e:
                cog_logger.error(f"Error handling verification bonus: {e}")

    async def handle_onboarding_bonus(self, member):
        """Handle onboarding role bonus"""
        with self.app.app_context():
            try:
                user = self.User.query.filter_by(id=str(member.id)).first()
                if not user:
                    user = self.User(
                        id=str(member.id),
                        username=member.name,
                        discord_id=str(member.id)
                    )
                    self.db.session.add(user)
                    self.db.session.flush()
                
                # Check if user already received onboarding bonus
                if not user.onboarding_bonus_received:
                    user.balance += 500
                    user.points += 500
                    user.onboarding_bonus_received = True
                    self.db.session.commit()
                    
                    # Send announcement
                    if GENERAL_CHANNEL_ID:
                        channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                        if channel:
                            embed = discord.Embed(
                                title="🎉 Onboarding Bonus!",
                                description=f"Welcome {member.mention}! You've received **500 pitchforks** for completing onboarding!",
                                color=discord.Color.gold()
                            )
                            embed.add_field(
                                name="💰 New Balance",
                                value=f"{user.balance} pitchforks",
                                inline=True
                            )
                            await channel.send(embed=embed)
                    
                    cog_logger.info(f"Onboarding bonus awarded to {member.name}: 500 points")
                
            except Exception as e:
                cog_logger.error(f"Error handling onboarding bonus: {e}")

    async def award_daily_engagement_points(self, user, message):
        """Award points for daily engagement approval"""
        try:
            # Check if user has reached daily engagement limit
            daily_engagement_count = getattr(user, 'daily_engagement_count', 0) or 0
            if daily_engagement_count >= 3:  # Max 3 daily engagements per day
                return False, "Daily engagement limit reached"
            
            # Check if user already got daily engagement today
            current_time = datetime.now()
            if user.last_daily_engagement and (current_time - user.last_daily_engagement) < timedelta(days=1):
                return False, "Daily engagement already claimed today"
            
            # Award points
            user.balance += DAILY_ENGAGEMENT_POINTS
            user.points += DAILY_ENGAGEMENT_POINTS
            user.last_daily_engagement = current_time
            if not hasattr(user, 'daily_engagement_count') or user.daily_engagement_count is None:
                user.daily_engagement_count = 0
            user.daily_engagement_count += 1
            
            self.db.session.commit()
            
            # Check for achievements
            await self.check_achievements(user, 'daily_engagement')
            
            # Send announcement
            await self.send_daily_engagement_announcement(user)
            
            cog_logger.info(f"Daily engagement points awarded to {user.username}: {DAILY_ENGAGEMENT_POINTS} points")
            return True, f"Awarded {DAILY_ENGAGEMENT_POINTS} points for daily engagement"
            
        except Exception as e:
            cog_logger.error(f"Error awarding daily engagement points: {e}")
            return False, "Error awarding points"

    async def check_admin_reactions(self, reaction, admin_user):
        """Check if admin reaction is for point awarding"""
        with self.app.app_context():
            try:
                # Extract emoji name from the full emoji string
                emoji_str = str(reaction.emoji)
                emoji_name = emoji_str.split(':')[1] if ':' in emoji_str else emoji_str
                
                # Check for daily engagement emoji
                if emoji_name == DAILY_ENGAGEMENT_EMOJI:
                    user = self.User.query.filter_by(id=str(reaction.message.author.id)).first()
                    if user:
                        success, message = await self.award_daily_engagement_points(user, reaction.message)
                        await self.send_admin_reaction_dm(admin_user, reaction, reaction.message, "daily_engagement", DAILY_ENGAGEMENT_POINTS if success else 0)
                        # Add checkmark reaction if successful
                        if success:
                            try:
                                await reaction.message.add_reaction("✅")
                            except Exception as e:
                                cog_logger.error(f"Error adding checkmark reaction: {e}")
                    else:
                        cog_logger.warning(f"User {reaction.message.author.name} not found in database")
                
                # Check for campus picture emoji
                elif emoji_name == CAMPUS_PICTURE_EMOJI:
                    user = self.User.query.filter_by(id=str(reaction.message.author.id)).first()
                    if user:
                        success, message = await self.award_campus_picture_points(user, reaction.message)
                        await self.send_admin_reaction_dm(admin_user, reaction, reaction.message, "campus_picture", CAMPUS_PICTURE_POINTS if success else 0)
                        # Add checkmark reaction if successful
                        if success:
                            try:
                                await reaction.message.add_reaction("✅")
                            except Exception as e:
                                cog_logger.error(f"Error adding checkmark reaction: {e}")
                    else:
                        cog_logger.warning(f"User {reaction.message.author.name} not found in database")
                
                # Check for enrollment deposit emoji
                elif emoji_name == ENROLLMENT_DEPOSIT_EMOJI:
                    user = self.User.query.filter_by(id=str(reaction.message.author.id)).first()
                    if user:
                        success, message = await self.award_enrollment_deposit_points(user, reaction.message)
                        await self.send_admin_reaction_dm(admin_user, reaction, reaction.message, "enrollment_deposit", ENROLLMENT_DEPOSIT_POINTS if success else 0)
                        # Add checkmark reaction if successful
                        if success:
                            try:
                                await reaction.message.add_reaction("✅")
                            except Exception as e:
                                cog_logger.error(f"Error adding checkmark reaction: {e}")
                    else:
                        cog_logger.warning(f"User {reaction.message.author.name} not found in database")
                else:
                    cog_logger.info(f"Emoji {emoji_name} did not match any configured emojis")
                
            except Exception as e:
                cog_logger.error(f"Error checking admin reactions: {e}")

    async def award_campus_picture_points(self, user, message):
        """Award points for campus picture approval"""
        try:
            # Check if user already received campus picture points
            if getattr(user, 'campus_photos_count', 0) >= 1:
                return False, "Campus picture points already awarded"
            
            # Award points
            user.balance += CAMPUS_PICTURE_POINTS
            user.points += CAMPUS_PICTURE_POINTS
            user.campus_photos_count = 1
            
            self.db.session.commit()
            
            # Check for achievements
            await self.check_achievements(user, 'campus_picture')
            
            # Send announcement
            await self.send_campus_photo_announcement(user)
            
            cog_logger.info(f"Campus picture points awarded to {user.username}: {CAMPUS_PICTURE_POINTS} points")
            return True, f"Awarded {CAMPUS_PICTURE_POINTS} points for campus picture"
            
        except Exception as e:
            cog_logger.error(f"Error awarding campus picture points: {e}")
            return False, "Error awarding points"

    async def award_enrollment_deposit_points(self, user, message):
        """Award points for enrollment deposit approval"""
        try:
            # Check if user already received enrollment deposit points
            if user.enrollment_deposit_received:
                return False, "Enrollment deposit points already awarded"
            
            # Award points
            old_balance = user.balance
            old_points = user.points
            user.balance += ENROLLMENT_DEPOSIT_POINTS
            user.points += ENROLLMENT_DEPOSIT_POINTS
            user.enrollment_deposit_received = True
            
            # Commit the changes
            self.db.session.commit()
            
            # Check for achievements
            await self.check_achievements(user, 'enrollment_deposit')
            
            # Send announcement
            await self.send_enrollment_deposit_announcement(user)
            
            cog_logger.info(f"Enrollment deposit points awarded to {user.username}: {ENROLLMENT_DEPOSIT_POINTS} points")
            return True, f"Awarded {ENROLLMENT_DEPOSIT_POINTS} points for enrollment deposit"
            
        except Exception as e:
            self.db.session.rollback()
            cog_logger.error(f"Error awarding enrollment deposit points: {e}")
            return False, "Error awarding points"

    async def check_birthdays(self):
        """Check for birthdays and send announcements"""
        with self.app.app_context():
            try:
                current_date = datetime.now().date()
                users_with_birthdays = self.User.query.filter(
                    and_(
                        self.User.birthday.isnot(None),
                        func.extract('month', self.User.birthday) == current_date.month,
                        func.extract('day', self.User.birthday) == current_date.day
                    )
                ).all()
                
                if users_with_birthdays and GENERAL_CHANNEL_ID:
                    channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                    if channel:
                        for user in users_with_birthdays:
                            embed = discord.Embed(
                                title="🎂 Happy Birthday!",
                                description=f"Today is **{user.username}**'s birthday! 🎉",
                                color=discord.Color.pink()
                            )
                            embed.add_field(
                                name="🎁 Birthday Gift",
                                value="You've received **100 pitchforks** as a birthday gift!",
                                inline=True
                            )
                            await channel.send(embed=embed)
                            
                            # Award birthday points
                            user.balance += 100
                            user.points += 100
                            self.db.session.commit()
                            
                            cog_logger.info(f"Birthday gift awarded to {user.username}: 100 points")
                
            except Exception as e:
                cog_logger.error(f"Error checking birthdays: {e}")

    @tasks.loop(time=datetime.strptime(BIRTHDAY_CHECK_TIME, "%H:%M").time())
    async def daily_birthday_check(self):
        """Daily task to check for birthdays"""
        await self.check_birthdays()

    @daily_birthday_check.before_loop
    async def before_birthday_check(self):
        """Wait until the specified time before starting birthday checks"""
        await self.bot.wait_until_ready()
        now = datetime.now()
        target_time = datetime.strptime(BIRTHDAY_CHECK_TIME, "%H:%M").time()
        target_datetime = datetime.combine(now.date(), target_time)
        
        if now.time() > target_time:
            target_datetime += timedelta(days=1)
        
        await asyncio.sleep((target_datetime - now).total_seconds())

    @tasks.loop(minutes=10)
    async def monitor_restricted_role_task(self):
        """Periodically check and remove restricted roles from users with trigger role"""
        try:
            removed_count = await self.scan_and_remove_restricted_roles()
            if removed_count > 0:
                print(f"Periodic role monitoring: Removed restricted role from {removed_count} users")
                cog_logger.info(f"Periodic monitoring removed restricted role from {removed_count} users")
        except Exception as e:
            cog_logger.error(f"Error in periodic role monitoring: {e}")

    @monitor_restricted_role_task.before_loop
    async def before_restricted_role_monitor(self):
        """Wait until bot is ready before starting role monitoring"""
        await self.bot.wait_until_ready()

    async def assign_role_to_user(self, user_id, role_id, purchase_id):
        """
        Directly assign a Discord role to a user
        Returns: (success: bool, message: str)
        """
        try:
            # Convert string IDs to integers
            user_id = int(user_id)
            role_id = int(role_id)
            
            # Find the guild and member
            guild = None
            member = None
            
            for g in self.bot.guilds:
                temp_member = g.get_member(user_id)
                if temp_member:
                    guild = g
                    member = temp_member
                    break
            
            if not guild:
                return False, f"Could not find user {user_id} in any Discord server"
            
            if not member:
                return False, f"Could not find member {user_id} in guild {guild.name}"
            
            # Get the role
            role = guild.get_role(role_id)
            if not role:
                return False, f"Could not find role {role_id} in guild {guild.name}"
            
            # Check if user already has the role
            if role in member.roles:
                return True, f"User already has role {role.name}"
            
            # Assign the role
            try:
                await member.add_roles(role, reason=f"Economy purchase {purchase_id}")
                cog_logger.info(f"Role {role.name} assigned to {member.name} for purchase {purchase_id}")
                return True, f"Successfully assigned role {role.name}"
                
            except discord.Forbidden:
                error_msg = f"Bot doesn't have permission to assign role {role.name}"
                cog_logger.error(error_msg)
                return False, error_msg
                
            except discord.HTTPException as e:
                error_msg = f"Discord HTTP error: {str(e)}"
                cog_logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error in role assignment: {str(e)}"
            cog_logger.error(error_msg)
            return False, error_msg

    async def check_achievements(self, user, achievement_type, count=None):
        """Check and award achievements based on user activity"""
        with self.app.app_context():
            try:
                # Get all achievements of this type
                achievements = self.Achievement.query.filter_by(type=achievement_type).all()
                
                for achievement in achievements:
                    # Check if user already has this achievement
                    existing = self.UserAchievement.query.filter_by(
                        user_id=user.id,
                        achievement_id=achievement.id
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Check if user meets the requirement
                    if achievement_type == 'messages' and user.message_count >= achievement.requirement:
                        await self.award_achievement(user, achievement)
                    elif achievement_type == 'daily' and user.daily_claims_count >= achievement.requirement:
                        await self.award_achievement(user, achievement)
                    elif achievement_type == 'daily_engagement' and user.daily_engagement_count >= achievement.requirement:
                        await self.award_achievement(user, achievement)
                    elif achievement_type == 'campus_picture' and user.campus_photos_count == 0:
                        await self.award_achievement(user, achievement)
                    elif achievement_type == 'enrollment_deposit' and user.enrollment_deposit_received:
                        await self.award_achievement(user, achievement)
                    elif achievement_type == 'birthday' and user.birthday is not None:
                        await self.award_achievement(user, achievement)
                
            except Exception as e:
                cog_logger.error(f"Error checking achievements: {e}")

    async def send_achievement_announcement(self, user, achievement):
        """Send achievement announcement"""
        if GENERAL_CHANNEL_ID:
            try:
                channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                if channel:
                    embed = discord.Embed(
                        title="🏆 Achievement Unlocked!",
                        description=f"Congratulations {user.username}! You've unlocked the **{achievement.name}** achievement!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="💰 Points Earned",
                        value=f"+{achievement.points} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 New Balance",
                        value=f"{user.balance} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="🎯 Description",
                        value=achievement.description or "Great job!",
                        inline=False
                    )
                    
                    await channel.send(embed=embed)
                    
            except Exception as e:
                cog_logger.error(f"Error sending achievement announcement: {e}")
    
    async def send_purchase_notification(self, purchaser_user, product, points_spent, purchase_id):
        """Send purchase notification to the specified admin user"""
        try:
            # The Discord user ID to notify
            ADMIN_USER_ID = 689510313971810437
            
            # Get the admin user
            admin_user = self.bot.get_user(ADMIN_USER_ID)
            if not admin_user:
                cog_logger.warning(f"Could not find admin user {ADMIN_USER_ID}")
                return
            
            # Create purchase notification embed
            embed = discord.Embed(
                title="🛒 New Purchase Alert!",
                description=f"A new purchase has been made in the Devil2Devil Store!",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👤 Customer",
                value=f"{purchaser_user.username} (ID: {purchaser_user.id})",
                inline=True
            )
            
            embed.add_field(
                name="🛍️ Product",
                value=f"{product.name}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Price",
                value=f"{points_spent} pitchforks",
                inline=True
            )
            
            embed.add_field(
                name="📋 Product Type",
                value=f"{product.product_type.replace('_', ' ').title()}",
                inline=True
            )
            
            embed.add_field(
                name="📦 Purchase ID",
                value=f"#{purchase_id}",
                inline=True
            )
            
            embed.add_field(
                name="🕐 Timestamp",
                value=f"<t:{int(datetime.utcnow().timestamp())}:F>",
                inline=True
            )
            
            if product.description:
                embed.add_field(
                    name="📝 Description",
                    value=f"{product.description[:100]}{'...' if len(product.description) > 100 else ''}",
                    inline=False
                )
            
            # Add stock information if applicable
            if product.stock is not None:
                remaining_stock = product.stock
                embed.add_field(
                    name="📊 Remaining Stock",
                    value=f"{remaining_stock} items" if remaining_stock > 0 else "Out of stock",
                    inline=True
                )
            
            embed.set_footer(
                text="Devil2Devil Economy System",
                icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # Optional: Add a footer icon
            )
            
            # Send the notification
            await admin_user.send(embed=embed)
            cog_logger.info(f"Purchase notification sent to admin {ADMIN_USER_ID} for purchase {purchase_id}")
            
        except discord.Forbidden:
            cog_logger.error(f"Could not send DM to admin user {ADMIN_USER_ID} - DMs may be disabled")
        except Exception as e:
            cog_logger.error(f"Error sending purchase notification: {e}")

    async def send_enrollment_deposit_announcement(self, user):
        """Send enrollment deposit announcement"""
        if GENERAL_CHANNEL_ID:
            try:
                channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                if channel:
                    embed = discord.Embed(
                        title="🎉 Enrollment Deposit Approved!",
                        description=f"Congratulations {user.username}! Your enrollment deposit has been approved!",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="💰 Points Earned",
                        value=f"+{ENROLLMENT_DEPOSIT_POINTS} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 New Balance",
                        value=f"{user.balance} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="🎓 Next Steps",
                        value="You're now eligible for campus activities and exclusive benefits!",
                        inline=False
                    )
                    
                    await channel.send(embed=embed)
                    
            except Exception as e:
                cog_logger.error(f"Error sending enrollment deposit announcement: {e}")

    async def send_daily_engagement_announcement(self, user):
        """Send daily engagement announcement"""
        if GENERAL_CHANNEL_ID:
            try:
                channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                if channel:
                    embed = discord.Embed(
                        title="📚 Daily Engagement Approved!",
                        description=f"Great job {user.username}! Your daily engagement has been approved!",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="💰 Points Earned",
                        value=f"+{DAILY_ENGAGEMENT_POINTS} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 New Balance",
                        value=f"{user.balance} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="📊 Daily Engagement Count",
                        value=f"{user.daily_engagement_count}/3 for today",
                        inline=True
                    )
                    
                    await channel.send(embed=embed)
                    
            except Exception as e:
                cog_logger.error(f"Error sending daily engagement announcement: {e}")

    async def send_campus_photo_announcement(self, user):
        """Send campus photo announcement"""
        if GENERAL_CHANNEL_ID:
            try:
                channel = self.bot.get_channel(int(GENERAL_CHANNEL_ID))
                if channel:
                    embed = discord.Embed(
                        title="📸 Campus Photo Approved!",
                        description=f"Awesome {user.username}! Your campus photo has been approved!",
                        color=discord.Color.purple()
                    )
                    embed.add_field(
                        name="💰 Points Earned",
                        value=f"+{CAMPUS_PICTURE_POINTS} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 New Balance",
                        value=f"{user.balance} pitchforks",
                        inline=True
                    )
                    embed.add_field(
                        name="🏫 Campus Spirit",
                        value="You're showing great campus spirit! Keep it up!",
                        inline=False
                    )
                    
                    await channel.send(embed=embed)
                    
            except Exception as e:
                cog_logger.error(f"Error sending campus photo announcement: {e}")

    async def send_admin_reaction_dm(self, admin_user, reaction, message, action_taken, points_awarded=0):
        """Send DM to admin about their reaction"""
        try:
            embed = discord.Embed(
                title="🛡️ Admin Action Taken",
                description=f"You reacted to a message with {reaction.emoji}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{message.author.name} ({message.author.id})",
                inline=True
            )
            
            embed.add_field(
                name="📝 Message",
                value=f"{message.content[:100]}{'...' if len(message.content) > 100 else ''}",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Action",
                value=action_taken.replace('_', ' ').title(),
                inline=True
            )
            
            if points_awarded > 0:
                embed.add_field(
                    name="💰 Points Awarded",
                    value=f"+{points_awarded} pitchforks",
                    inline=True
                )
                embed.color = discord.Color.green()
            else:
                embed.add_field(
                    name="❌ Action Failed",
                    value="No points were awarded",
                    inline=True
                )
                embed.color = discord.Color.red()
            
            embed.add_field(
                name="📅 Timestamp",
                value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                inline=False
            )
            
            await admin_user.send(embed=embed)
            
        except Exception as e:
            cog_logger.error(f"Error sending admin reaction DM: {e}")

    async def award_achievement(self, user, achievement):
        """Award an achievement to a user"""
        with self.app.app_context():
            try:
                # Create user achievement record
                user_achievement = self.UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
                self.db.session.add(user_achievement)
                
                # Award points
                user.balance += achievement.points
                user.points += achievement.points
                
                self.db.session.commit()
                
                # Send announcement
                await self.send_achievement_announcement(user, achievement)
                
                cog_logger.info(f"Achievement '{achievement.name}' awarded to {user.username}: {achievement.points} points")
                
            except Exception as e:
                self.db.session.rollback()
                cog_logger.error(f"Error awarding achievement: {e}")

    async def cog_load(self):
        # Discord.py automatically registers app_commands when the cog is added
        # No need to manually add commands here
        pass

    @app_commands.command(name="achievements", description="View your achievements")
    async def achievements(self, interaction: discord.Interaction):
        """View your achievements"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            
            # Get user's achievements
            user_achievements = self.UserAchievement.query.filter_by(user_id=user.id).all()
            
            embed = discord.Embed(
                title="🏆 Your Achievements",
                color=discord.Color.gold()
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
            
            embed.set_footer(text=f"Total Points Earned: {user.balance}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="birthday", description="Set your birthday to receive points and birthday announcements")
    async def set_birthday(self, interaction: discord.Interaction, month: int, day: int):
        """Set your birthday (month and day)"""
        with self.app.app_context():
            # Validate input
            if month < 1 or month > 12:
                await interaction.response.send_message("Invalid month! Please enter a number between 1 and 12.", ephemeral=True)
                return
            
            if day < 1 or day > 31:
                await interaction.response.send_message("Invalid day! Please enter a number between 1 and 31.", ephemeral=True)
                return
            
            # Validate day for specific months
            days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if day > days_in_month[month - 1]:
                await interaction.response.send_message(f"Invalid day for month {month}! Please enter a valid day.", ephemeral=True)
                return
            
            # Get or create user
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name, discord_id=str(interaction.user.id))
                self.db.session.add(user)
                self.db.session.flush()
            
            # Check if birthday is already set
            birthday_already_set = user.birthday is not None
            
            # Set the birthday
            from datetime import date
            try:
                user.birthday = date(2000, month, day)  # Use 2000 as placeholder year
                
                # Award points for setting birthday (only if not already set)
                if not birthday_already_set and not user.birthday_points_received:
                    user.balance += BIRTHDAY_SETUP_POINTS
                    user.points += BIRTHDAY_SETUP_POINTS
                    user.birthday_points_received = True
                
                self.db.session.commit()
                
                # Check for birthday achievements
                await self.check_achievements(user, 'birthday')
                
                # Create response embed
                embed = discord.Embed(
                    title="🎂 Birthday Set!",
                    description=f"Your birthday has been set to **{user.birthday.strftime('%B %d')}**!",
                    color=discord.Color.gold()
                )
                
                if not birthday_already_set:
                    embed.add_field(
                        name="🎉 Bonus Points!",
                        value=f"You received **{BIRTHDAY_SETUP_POINTS} points** for setting up your birthday!",
                        inline=False
                    )
                    embed.add_field(
                        name="💰 New Balance",
                        value=f"{user.balance} pitchforks",
                        inline=True
                    )
                
                embed.add_field(
                    name="🎈 Birthday Announcements",
                    value="You'll receive special birthday announcements on your special day!",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                cog_logger.info(f"Birthday set for {user.username}: {user.birthday.strftime('%B %d')}")
                
            except ValueError as e:
                await interaction.response.send_message("Invalid date! Please check your month and day values.", ephemeral=True)
            except Exception as e:
                self.db.session.rollback()
                await interaction.response.send_message("An error occurred while setting your birthday. Please try again.", ephemeral=True)
                cog_logger.error(f"Error setting birthday for {interaction.user.name}: {e}")

    @app_commands.command(name="balance", description="Check your current pitchfork balance")
    async def balance(self, interaction: discord.Interaction):
        """Check your current pitchfork balance"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            embed = discord.Embed(
                title="Pitchfork Balance",
                description=f"Your current balance: {user.balance} pitchforks",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily pitchfork reward")
    async def daily(self, interaction: discord.Interaction):
        """Claim your daily pitchforks with atomic transaction"""
        with self.app.app_context():
            try:
                settings = self.EconomySettings.query.first()
                if not settings or not settings.economy_enabled:
                    embed = discord.Embed(
                        title="🔒 Economy Disabled",
                        description="The economy system is currently disabled. Contact an admin for more information.",
                        color=discord.Color.red()
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
                    embed = discord.Embed(
                        title="🚫 Daily Limit Reached",
                        description=f"You have reached the maximum of {MAX_DAILY_CLAIMS} daily claims. No more daily rewards available!",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                current_time = datetime.now()
                if user.last_daily and (current_time - user.last_daily) < timedelta(days=1):
                    time_left = user.last_daily + timedelta(days=1) - current_time
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    embed = discord.Embed(
                        title="⏰ Daily Reward Not Ready",
                        description=f"You can claim your daily pitchforks again in {hours} hours and {minutes} minutes.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Award daily reward and increment counter
                user.balance += 85
                user.points += 85
                user.last_daily = current_time
                if not hasattr(user, 'daily_claims_count') or user.daily_claims_count is None:
                    user.daily_claims_count = 0
                user.daily_claims_count += 1
                
                self.db.session.commit()
                
                # Check for daily achievements
                await self.check_achievements(user, 'daily')
                
                # Format the new embed as requested
                remaining_claims = 90 - user.daily_claims_count
                embed = discord.Embed(
                    title="🎉 Daily Reward Claimed!",
                    description=f"You have received 85 pitchforks. Your new balance is {user.balance} pitchforks.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Daily Claims Remaining",
                    value=f"{remaining_claims} out of 90",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                cog_logger.info(f"Daily reward claimed by {user.username}: 85 points")
                
            except Exception as e:
                self.db.session.rollback()
                await interaction.response.send_message("An error occurred while claiming your daily reward. Please try again.", ephemeral=True)
                cog_logger.error(f"Error claiming daily reward for {interaction.user.name}: {e}")

    @app_commands.command(name="leaderboard", description="Show the top 10 users by pitchfork balance")
    async def leaderboard(self, interaction: discord.Interaction):
        """Show the top 10 users by pitchfork balance"""
        with self.app.app_context():
            top_users = self.User.query.filter(self.User.is_admin == False).order_by(self.User.balance.desc()).limit(10).all()
            
            embed = discord.Embed(
                title="🏆 Pitchfork Leaderboard",
                color=discord.Color.gold()
            )
            
            for i, user in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                embed.add_field(
                    name=f"{medal} {user.username}",
                    value=f"{user.balance} pitchforks",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give_all", description="Give pitchforks to all users (Admin only)")
    async def give_all(self, interaction: discord.Interaction, amount: int):
        """Give pitchforks to all users (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        with self.app.app_context():
            users = self.User.query.all()
            for user in users:
                user.balance += amount
                user.points += amount
            self.db.session.commit()
            
            embed = discord.Embed(
                title="💰 Mass Giveaway Complete!",
                description=f"Gave {amount} pitchforks to {len(users)} users!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Give pitchforks to a specific user (Admin only)")
    async def give(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Give pitchforks to a specific user (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        with self.app.app_context():
            db_user = self.User.query.filter_by(id=str(user.id)).first()
            if not db_user:
                db_user = self.User(id=str(user.id), username=user.name, discord_id=str(user.id))
                self.db.session.add(db_user)
            
            db_user.balance += amount
            db_user.points += amount
            self.db.session.commit()
            
            embed = discord.Embed(
                title="💰 Giveaway Complete!",
                description=f"Gave {amount} pitchforks to {user.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💎 New Balance",
                value=f"{db_user.balance} pitchforks",
                inline=True
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="economy", description="Enable or disable the economy system (Admin only)")
    async def economy_toggle(self, interaction: discord.Interaction, action: str):
        """Enable or disable the economy system (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        with self.app.app_context():
            settings = self.EconomySettings.query.first()
            if not settings:
                settings = self.EconomySettings(economy_enabled=False)
                self.db.session.add(settings)
            
            if action.lower() == "enable":
                settings.economy_enabled = True
                embed = discord.Embed(
                    title="✅ Economy Enabled",
                    description="The economy system is now active!",
                    color=discord.Color.green()
                )
            elif action.lower() == "disable":
                settings.economy_enabled = False
                embed = discord.Embed(
                    title="❌ Economy Disabled",
                    description="The economy system is now inactive.",
                    color=discord.Color.red()
                )
            else:
                await interaction.response.send_message("Invalid action! Use 'enable' or 'disable'.", ephemeral=True)
                return
            
            self.db.session.commit()
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="limits", description="View your earning limits and theoretical maximum pitchforks")
    async def limits(self, interaction: discord.Interaction):
        """View your earning limits and theoretical maximum pitchforks"""
        with self.app.app_context():
            user = self.User.query.filter_by(id=str(interaction.user.id)).first()
            if not user:
                user = self.User(id=str(interaction.user.id), username=interaction.user.name)
                self.db.session.add(user)
                self.db.session.commit()
            
            embed = discord.Embed(
                title="📊 Your Earning Limits",
                color=discord.Color.blue()
            )
            
            # Daily limits
            daily_claims = getattr(user, 'daily_claims_count', 0) or 0
            embed.add_field(
                name="📅 Daily Claims",
                value=f"{daily_claims}/{MAX_DAILY_CLAIMS} used today",
                inline=True
            )
            
            # Message count
            embed.add_field(
                name="💬 Messages",
                value=f"{user.message_count} messages sent",
                inline=True
            )
            
            # Voice minutes
            embed.add_field(
                name="🎤 Voice Time",
                value=f"{user.voice_minutes} minutes in voice",
                inline=True
            )
            
            # Achievements
            user_achievements = self.UserAchievement.query.filter_by(user_id=user.id).count()
            total_achievements = self.Achievement.query.count()
            embed.add_field(
                name="🏆 Achievements",
                value=f"{user_achievements}/{total_achievements} unlocked",
                inline=True
            )
            
            # Theoretical maximum calculation
            theoretical_max = (
                user.balance +  # Current balance
                (MAX_DAILY_CLAIMS - daily_claims) * 85 +  # Remaining daily claims
                (total_achievements - user_achievements) * 50  # Remaining achievements (assuming 50 points each)
            )
            
            embed.add_field(
                name="🎯 Theoretical Maximum",
                value=f"{theoretical_max} pitchforks possible",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Learn how to earn pitchforks in the Devil2Devil economy")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information about the economy system"""
        embed = discord.Embed(
            title="💰 Devil2Devil Economy Guide",
            description="Learn how to earn pitchforks in our community!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📅 Daily Rewards",
            value="Use `/daily` to claim your daily pitchforks (up to 3 times per day)",
            inline=False
        )
        
        embed.add_field(
            name="🎂 Birthday Setup",
            value="Use `/birthday <month> <day>` to set your birthday and earn bonus points",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Achievements",
            value="Complete various activities to unlock achievements and earn points",
            inline=False
        )
        
        embed.add_field(
            name="💬 Engagement",
            value="Send messages, join voice channels, and participate in the community",
            inline=False
        )
        
        embed.add_field(
            name="🛒 Shop",
            value="Spend your pitchforks in the web shop at https://shop.devil2devil.asu.edu",
            inline=False
        )
        
        embed.add_field(
            name="📊 Check Your Status",
            value="Use `/balance`, `/achievements`, and `/limits` to track your progress",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="test", description="Test if the bot is working (Admin only)")
    async def test_bot(self, interaction: discord.Interaction):
        """Test if the bot is working (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="✅ Bot Test",
            description="The bot is working correctly!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🤖 Bot Status",
            value="Online and responsive",
            inline=True
        )
        embed.add_field(
            name="💾 Database",
            value="Connected and operational",
            inline=True
        )
        embed.add_field(
            name="🌐 Web Server",
            value="Running on https://shop.devil2devil.asu.edu",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="remove_restricted_roles", description="Remove committed role from unverified users (Admin only)")
    async def remove_restricted_roles(self, interaction: discord.Interaction):
        """Remove committed role from unverified users (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # First, scan to see how many users would be affected
            affected_users = await self.get_affected_users()
            
            if not affected_users:
                embed = discord.Embed(
                    title="ℹ️ No Action Needed",
                    description="No unverified users found with the committed role.",
                    color=0x3498db
                )
                embed.add_field(
                    name="Details",
                    value=f"• Committed Role: `{COMMITTED_ROLE_NAME}`\n• Unverified Role: `{UNVERIFIED_ROLE_NAME}`",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Show confirmation with affected users
            user_list = "\n".join([f"• {user['name']} ({user['id']})" for user in affected_users[:10]])
            if len(affected_users) > 10:
                user_list += f"\n... and {len(affected_users) - 10} more users"
            
            embed = discord.Embed(
                title="⚠️ Confirmation Required",
                description=f"Found **{len(affected_users)}** users with both roles who will have the restricted role removed.",
                color=0xff9900
            )
            embed.add_field(
                name="Affected Users",
                value=user_list,
                inline=False
            )
            embed.add_field(
                name="Details",
                value=f"• Committed Role: `{COMMITTED_ROLE_NAME}`\n• Unverified Role: `{UNVERIFIED_ROLE_NAME}`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Warning",
                value="This action cannot be undone. Please confirm to proceed.",
                inline=False
            )
            
            # Create confirmation view
            view = RoleRemovalConfirmationView(self, interaction.user.id, affected_users)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while checking users: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            cog_logger.error(f"Error in remove_restricted_roles command: {e}")

def setup(bot, app, db, User, EconomySettings, Achievement, UserAchievement):
    bot.add_cog(EconomyCog(bot, app, db, User, EconomySettings, Achievement, UserAchievement)) 