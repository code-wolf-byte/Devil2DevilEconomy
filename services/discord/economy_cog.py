"""
Economy cog for Discord bot using py-cord.
Migrated from nextcord with improved structure and organization.
"""

import discord
from discord.ext import commands, tasks
from discord import Interaction
from datetime import datetime, timedelta, date
import datetime as dt
import os
import asyncio
import logging
from typing import Optional

from config import EconomyPoints, ActivityLimits, TimeConfig, CustomEmojis
from models.base import db_transaction

# Set up logging for cogs
cog_logger = logging.getLogger('economy.discord.cog')


class EconomyCog(commands.Cog):
    """Economy system cog for Discord bot."""
    
    def __init__(self, bot, app, db, User, EconomySettings, Achievement, UserAchievement):
        self.bot = bot
        self.app = app
        self.db = db
        self.User = User
        self.EconomySettings = EconomySettings
        self.Achievement = Achievement
        self.UserAchievement = UserAchievement
        
        # Get configuration from environment
        self.verified_role_id = int(os.getenv('VERIFIED_ROLE_ID', 0)) if os.getenv('VERIFIED_ROLE_ID') else None
        self.general_channel_id = int(os.getenv('GENERAL_CHANNEL_ID')) if os.getenv('GENERAL_CHANNEL_ID') else None
        
        # Don't start tasks in __init__ - wait for bot to be ready
        self._tasks_started = False
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        if hasattr(self, 'daily_birthday_check') and self.daily_birthday_check.is_running():
            self.daily_birthday_check.cancel()
        if hasattr(self, 'process_role_assignments') and self.process_role_assignments.is_running():
            self.process_role_assignments.cancel()
        cog_logger.info("Economy cog unloaded and tasks cancelled")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready - start background tasks."""
        if not self._tasks_started:
            cog_logger.info("Economy cog ready - starting background tasks")
            
            # Start background tasks
            if not self.daily_birthday_check.is_running():
                self.daily_birthday_check.start()
            if not self.process_role_assignments.is_running():
                self.process_role_assignments.start()
            
            self._tasks_started = True
    
    def _is_economy_enabled(self) -> bool:
        """Check if economy system is enabled."""
        try:
            with self.app.app_context():
                settings = self.EconomySettings.query.first()
                return settings and settings.economy_enabled
        except Exception as e:
            cog_logger.error(f"Error checking economy status: {e}")
            return False
    
    def _get_or_create_user(self, discord_user) -> Optional['User']:
        """Get or create a user in the database."""
        try:
            user = self.User.query.filter_by(id=str(discord_user.id)).first()
            if not user:
                user = self.User(
                    id=str(discord_user.id), 
                    username=discord_user.name, 
                    discord_id=str(discord_user.id)
                )
                self.db.session.add(user)
                self.db.session.flush()  # Ensure user is created with default values
            return user
        except Exception as e:
            cog_logger.error(f"Error getting/creating user {discord_user.id}: {e}")
            return None
    
    # Event Listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        """Called when a message is sent."""
        if message.author.bot or not self._is_economy_enabled():
            return
        
        with self.app.app_context():
            try:
                user = self._get_or_create_user(message.author)
                if not user:
                    return
                
                # Ensure message_count is not None and enforce limit
                if user.message_count is None:
                    user.message_count = 0
                
                # Only increment if under the limit
                if user.message_count < ActivityLimits.MAX_MESSAGES:
                    user.message_count += 1
                    self.db.session.commit()
                    
                    # Check message achievements
                    await self.check_achievements(user, 'message', user.message_count)
                else:
                    # User has reached message limit, still commit to update last activity
                    self.db.session.commit()
                    
            except Exception as e:
                cog_logger.error(f"Error processing message from {message.author.id}: {e}")
                self.db.session.rollback()
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Called when a reaction is added to a message."""
        if user.bot or not self._is_economy_enabled():
            return
        
        with self.app.app_context():
            try:
                # Check if this is an admin giving points through custom emoji reactions
                await self.check_admin_reactions(reaction, user)
                
                # Track user reaction count for achievements
                user_obj = self._get_or_create_user(user)
                if not user_obj:
                    return
                
                # Ensure reaction_count is not None and enforce limit
                if user_obj.reaction_count is None:
                    user_obj.reaction_count = 0
                
                # Only increment if under the limit
                if user_obj.reaction_count < ActivityLimits.MAX_REACTIONS:
                    user_obj.reaction_count += 1
                    self.db.session.commit()
                    
                    # Check reaction achievements
                    await self.check_achievements(user_obj, 'reaction', user_obj.reaction_count)
                else:
                    # User has reached reaction limit, still commit to update last activity
                    self.db.session.commit()
                    
            except Exception as e:
                cog_logger.error(f"Error processing reaction from {user.id}: {e}")
                self.db.session.rollback()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice time and check achievements."""
        if member.bot or not self._is_economy_enabled():
            return
        
        with self.app.app_context():
            try:
                user = self._get_or_create_user(member)
                if not user:
                    return
                
                # If user joined a voice channel
                if not before.channel and after.channel:
                    # Ensure voice_minutes is not None and enforce limit
                    if user.voice_minutes is None:
                        user.voice_minutes = 0
                    
                    # Only increment if under the limit
                    if user.voice_minutes < ActivityLimits.MAX_VOICE_MINUTES:
                        user.voice_minutes += 1  # Increment by 1 minute
                        self.db.session.commit()
                        
                        # Check voice achievements
                        await self.check_achievements(user, 'voice')
                    else:
                        # User has reached voice limit, still commit to update last activity
                        self.db.session.commit()
                        
            except Exception as e:
                cog_logger.error(f"Error processing voice state update for {member.id}: {e}")
                self.db.session.rollback()
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Called when a member is updated (role changes, nickname changes, etc.)."""
        if not self._is_economy_enabled():
            return
        
        if before.roles != after.roles:
            with self.app.app_context():
                try:
                    added_roles = set(after.roles) - set(before.roles)
                    
                    # Check for verification role
                    if self.verified_role_id and any(role.id == self.verified_role_id for role in added_roles):
                        await self.handle_verification_bonus(after)
                    
                    # Check for onboarding roles using database config
                    settings = self.EconomySettings.query.first()
                    if settings and settings.onboarding_roles_list:
                        onboarding_role_ids = [int(role_id) for role_id in settings.onboarding_roles_list if role_id.strip()]
                        if any(role.id in onboarding_role_ids for role in added_roles):
                            await self.handle_onboarding_bonus(after)
                            
                except Exception as e:
                    cog_logger.error(f"Error processing member update for {after.id}: {e}")
    
    # Bonus Handlers
    async def handle_verification_bonus(self, member):
        """Handle verification bonus for new verified members with atomic transaction."""
        with self.app.app_context():
            try:
                with db_transaction() as session:
                    # Lock user row to prevent race conditions
                    user = session.query(self.User).with_for_update().filter_by(id=str(member.id)).first()
                    if not user:
                        user = self.User(
                            id=str(member.id), 
                            username=member.name, 
                            discord_id=str(member.id)
                        )
                        session.add(user)
                        session.flush()
                    
                    # Check if user already received verification bonus
                    if user.verification_bonus_received:
                        cog_logger.debug(f"User {member.name} already received verification bonus")
                        return
                    
                    # Get bonus amount from settings
                    settings = session.query(self.EconomySettings).first()
                    bonus_points = settings.verified_bonus_points if settings else EconomyPoints.VERIFICATION_BONUS
                    
                    # Award points and mark as received
                    user.add_points(bonus_points, "Verification bonus")
                    user.verification_bonus_received = True
                    
                    cog_logger.info(f"Awarded verification bonus of {bonus_points} points to {member.name}")
                    
                    # Send notification if general channel is configured
                    if self.general_channel_id:
                        channel = self.bot.get_channel(self.general_channel_id)
                        if channel:
                            embed = discord.Embed(
                                title="🎉 Verification Bonus!",
                                description=f"{member.mention} received {bonus_points} pitchforks for getting verified!",
                                color=discord.Color.green()
                            )
                            await channel.send(embed=embed)
                            
            except Exception as e:
                cog_logger.error(f"Error awarding verification bonus to {member.name}: {e}")
    
    async def handle_onboarding_bonus(self, member):
        """Handle onboarding bonus for new members with atomic transaction."""
        with self.app.app_context():
            try:
                with db_transaction() as session:
                    # Lock user row to prevent race conditions
                    user = session.query(self.User).with_for_update().filter_by(id=str(member.id)).first()
                    if not user:
                        user = self.User(
                            id=str(member.id), 
                            username=member.name, 
                            discord_id=str(member.id)
                        )
                        session.add(user)
                        session.flush()
                    
                    # Check if user already received onboarding bonus
                    if user.onboarding_bonus_received:
                        cog_logger.debug(f"User {member.name} already received onboarding bonus")
                        return
                    
                    # Get bonus amount from settings
                    settings = session.query(self.EconomySettings).first()
                    bonus_points = settings.onboarding_bonus_points if settings else EconomyPoints.ONBOARDING_BONUS
                    
                    # Award points and mark as received
                    user.add_points(bonus_points, "Onboarding bonus")
                    user.onboarding_bonus_received = True
                    
                    cog_logger.info(f"Awarded onboarding bonus of {bonus_points} points to {member.name}")
                    
                    # Send notification if general channel is configured
                    if self.general_channel_id:
                        channel = self.bot.get_channel(self.general_channel_id)
                        if channel:
                            embed = discord.Embed(
                                title="🎉 Welcome Bonus!",
                                description=f"{member.mention} received {bonus_points} pitchforks for completing onboarding!",
                                color=discord.Color.blue()
                            )
                            await channel.send(embed=embed)
                            
            except Exception as e:
                cog_logger.error(f"Error awarding onboarding bonus to {member.name}: {e}")
    
    # Background Tasks
    @tasks.loop(time=datetime.strptime(TimeConfig.BIRTHDAY_CHECK_TIME, "%H:%M").time())
    async def daily_birthday_check(self):
        """Check for birthdays daily and award points."""
        if not self._is_economy_enabled():
            return
        
        with self.app.app_context():
            try:
                await self.check_birthdays()
            except Exception as e:
                cog_logger.error(f"Error in daily birthday check: {e}")
    
    @daily_birthday_check.before_loop
    async def before_birthday_check(self):
        """Wait for bot to be ready before starting birthday check."""
        await self.bot.wait_until_ready()
        cog_logger.info("Birthday check task started")
    
    @tasks.loop(seconds=30)
    async def process_role_assignments(self):
        """Process pending Discord role assignments."""
        if not self._is_economy_enabled():
            return
        
        with self.app.app_context():
            try:
                from models import RoleAssignment
                
                # Get pending role assignments
                pending_assignments = RoleAssignment.query.filter_by(status='pending').limit(10).all()
                
                for assignment in pending_assignments:
                    try:
                        # Get guild and member
                        guild = self.bot.get_guild(int(os.getenv('GUILD_ID', '1082823852322725888')))
                        if not guild:
                            cog_logger.error("Guild not found for role assignment")
                            continue
                        
                        member = guild.get_member(int(assignment.user_id))
                        if not member:
                            cog_logger.warning(f"Member {assignment.user_id} not found in guild")
                            assignment.status = 'failed'
                            assignment.error_message = 'Member not found in guild'
                            assignment.completed_at = datetime.utcnow()
                            continue
                        
                        # Get role
                        role = guild.get_role(int(assignment.role_id))
                        if not role:
                            cog_logger.warning(f"Role {assignment.role_id} not found in guild")
                            assignment.status = 'failed'
                            assignment.error_message = 'Role not found in guild'
                            assignment.completed_at = datetime.utcnow()
                            continue
                        
                        # Assign role
                        await member.add_roles(role, reason=f"Economy purchase (Purchase ID: {assignment.purchase_id})")
                        
                        # Mark as completed
                        assignment.status = 'completed'
                        assignment.completed_at = datetime.utcnow()
                        
                        cog_logger.info(f"Successfully assigned role {role.name} to {member.name}")
                        
                        # Send notification to user
                        try:
                            embed = discord.Embed(
                                title="🎭 Role Assigned!",
                                description=f"You have been given the **{role.name}** role!",
                                color=discord.Color.green()
                            )
                            await member.send(embed=embed)
                        except discord.Forbidden:
                            cog_logger.debug(f"Could not DM {member.name} about role assignment")
                        
                    except discord.Forbidden:
                        assignment.status = 'failed'
                        assignment.error_message = 'Bot lacks permission to assign role'
                        assignment.completed_at = datetime.utcnow()
                        cog_logger.error(f"Permission denied assigning role {assignment.role_id} to {assignment.user_id}")
                    
                    except Exception as e:
                        assignment.status = 'failed'
                        assignment.error_message = str(e)
                        assignment.completed_at = datetime.utcnow()
                        cog_logger.error(f"Error assigning role {assignment.role_id} to {assignment.user_id}: {e}")
                
                # Commit all changes
                self.db.session.commit()
                
            except Exception as e:
                cog_logger.error(f"Error processing role assignments: {e}")
                self.db.session.rollback()
    
    @process_role_assignments.before_loop
    async def before_role_assignments(self):
        """Wait for bot to be ready before processing role assignments."""
        await self.bot.wait_until_ready()
        cog_logger.info("Role assignment processing task started")
    
    # Slash Commands (to be continued in next part due to length)
    @discord.slash_command(name="balance", description="Check your current pitchfork balance")
    async def balance(self, ctx):
        """Check user's current balance."""
        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return
        
        with self.app.app_context():
            try:
                user = self._get_or_create_user(ctx.user)
                if not user:
                    await ctx.respond("❌ Error accessing your account.", ephemeral=True)
                    return
                
                self.db.session.commit()
                
                embed = discord.Embed(
                    title="💰 Your Balance",
                    description=f"You have **{user.balance:,}** pitchforks!",
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=ctx.user.display_avatar.url)
                
                await ctx.respond(embed=embed)
                
            except Exception as e:
                cog_logger.error(f"Error checking balance for {ctx.user.id}: {e}")
                await ctx.respond("❌ Error checking your balance.", ephemeral=True)
    
    # Helper Methods
    async def check_achievements(self, user, achievement_type, count=None):
        """Check and award achievements for a user."""
        try:
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
                user_count = count if count is not None else getattr(user, f"{achievement_type}_count", 0)
                
                if user_count >= achievement.requirement:
                    await self.award_achievement(user, achievement)
                    
        except Exception as e:
            cog_logger.error(f"Error checking achievements for user {user.id}: {e}")
    
    async def award_achievement(self, user, achievement):
        """Award an achievement to a user."""
        try:
            # Create achievement record
            user_achievement = self.UserAchievement(
                user_id=user.id,
                achievement_id=achievement.id
            )
            self.db.session.add(user_achievement)
            
            # Award points
            user.add_points(achievement.points, f"Achievement: {achievement.name}")
            
            self.db.session.commit()
            
            # Send announcement
            await self.send_achievement_announcement(user, achievement)
            
            cog_logger.info(f"Awarded achievement '{achievement.name}' to {user.username}")
            
        except Exception as e:
            cog_logger.error(f"Error awarding achievement {achievement.name} to user {user.id}: {e}")
            self.db.session.rollback()
    
    async def send_achievement_announcement(self, user, achievement):
        """Send achievement announcement to general channel."""
        if not self.general_channel_id:
            return
        
        try:
            channel = self.bot.get_channel(self.general_channel_id)
            if not channel:
                return
            
            # Get Discord user
            discord_user = self.bot.get_user(int(user.id))
            if not discord_user:
                return
            
            embed = discord.Embed(
                title="🏆 Achievement Unlocked!",
                description=f"**{discord_user.mention}** earned the **{achievement.name}** achievement!",
                color=discord.Color.purple()
            )
            embed.add_field(name="Description", value=achievement.description, inline=False)
            embed.add_field(name="Reward", value=f"{achievement.points} pitchforks", inline=True)
            embed.set_thumbnail(url=discord_user.display_avatar.url)
            
            await channel.send(embed=embed)
            
        except Exception as e:
            cog_logger.error(f"Error sending achievement announcement: {e}")
    
    async def check_birthdays(self):
        """Check for users with birthdays today and award points."""
        try:
            today = date.today()
            
            # Get users with today's birthday who haven't received points yet
            users_with_birthday = self.User.query.filter(
                self.User.birthday != None,
                self.db.extract('month', self.User.birthday) == today.month,
                self.db.extract('day', self.User.birthday) == today.day,
                self.User.birthday_points_received == False
            ).all()
            
            for user in users_with_birthday:
                # Award birthday points
                user.add_points(EconomyPoints.BIRTHDAY_SETUP, "Birthday bonus")
                user.birthday_points_received = True
                
                cog_logger.info(f"Awarded birthday points to {user.username}")
                
                # Send birthday message if general channel is configured
                if self.general_channel_id:
                    channel = self.bot.get_channel(self.general_channel_id)
                    if channel:
                        discord_user = self.bot.get_user(int(user.id))
                        if discord_user:
                            embed = discord.Embed(
                                title="🎂 Happy Birthday!",
                                description=f"Happy birthday {discord_user.mention}! 🎉\nYou've received {EconomyPoints.BIRTHDAY_SETUP} pitchforks!",
                                color=discord.Color.magenta()
                            )
                            await channel.send(embed=embed)
            
            self.db.session.commit()
            
        except Exception as e:
            cog_logger.error(f"Error checking birthdays: {e}")
            self.db.session.rollback()
    
    async def check_admin_reactions(self, reaction, admin_user):
        """Check for admin reactions that award points."""
        # This will be implemented with the custom emoji system
        # For now, just a placeholder
        pass

    # Additional Slash Commands
    @discord.slash_command(name="achievements", description="View your achievements")
    async def achievements(self, ctx):
        """View your achievements."""
        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return
        
        with self.app.app_context():
            try:
                user = self._get_or_create_user(ctx.user)
                if not user:
                    await ctx.respond("❌ Error accessing your account.", ephemeral=True)
                    return
                
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
                        achievement = self.Achievement.query.filter_by(id=ua.achievement_id).first()
                        embed.add_field(
                            name=f"🎖️ {achievement.name}",
                            value=f"{achievement.description}\n**Points:** {achievement.points}",
                            inline=False
                        )
                
                embed.set_footer(text=f"Total Points Earned: {user.points}")
                await ctx.respond(embed=embed, ephemeral=True)
                
            except Exception as e:
                cog_logger.error(f"Error showing achievements for {ctx.user.id}: {e}")
                await ctx.respond("❌ Error retrieving your achievements.", ephemeral=True)

    @discord.slash_command(name="daily", description="Claim your daily pitchfork reward")
    async def daily(self, ctx):
        """Claim your daily pitchfork reward."""
        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return

        with self.app.app_context():
            try:
                user = self._get_or_create_user(ctx.user)
                if not user:
                    await ctx.respond("❌ Error accessing your account.", ephemeral=True)
                    return
                
                # Check if user has reached maximum daily claims
                daily_claims = getattr(user, 'daily_claims_count', 0) or 0
                if daily_claims >= ActivityLimits.MAX_DAILY_CLAIMS:
                    embed = discord.Embed(
                        title="🚫 Daily Limit Reached",
                        description=f"You have reached the maximum of {ActivityLimits.MAX_DAILY_CLAIMS} daily claims. No more daily rewards available!",
                        color=discord.Color.red()
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
                
                current_time = datetime.utcnow()
                if user.last_daily and (current_time - user.last_daily) < timedelta(days=1):
                    time_left = user.last_daily + timedelta(days=1) - current_time
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    embed = discord.Embed(
                        title="⏰ Daily Reward Not Ready",
                        description=f"You can claim your daily pitchforks again in {hours} hours and {minutes} minutes.",
                        color=discord.Color.red()
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
                
                # Award daily reward and increment counter
                user.balance += 85
                user.last_daily = current_time
                if not hasattr(user, 'daily_claims_count') or user.daily_claims_count is None:
                    user.daily_claims_count = 0
                user.daily_claims_count += 1
                
                self.db.session.commit()
                
                remaining_claims = ActivityLimits.MAX_DAILY_CLAIMS - user.daily_claims_count
                embed = discord.Embed(
                    title="🎉 Daily Reward Claimed!",
                    description=f"You have received 85 pitchforks. Your new balance is {user.balance:,} pitchforks.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Daily Claims Remaining",
                    value=f"{remaining_claims} out of {ActivityLimits.MAX_DAILY_CLAIMS}",
                    inline=True
                )
                await ctx.respond(embed=embed)
                
            except Exception as e:
                cog_logger.error(f"Error processing daily reward for {ctx.user.id}: {e}")
                self.db.session.rollback()
                await ctx.respond("❌ Error processing your daily reward.", ephemeral=True)

    @discord.slash_command(name="leaderboard", description="Show the top 10 users by pitchfork balance")
    async def leaderboard(self, ctx):
        """Show the pitchfork leaderboard."""
        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return

        with self.app.app_context():
            try:
                # Exclude admin users from leaderboard
                users = self.User.query.filter(self.User.is_admin == False).order_by(self.User.balance.desc()).limit(10).all()
                desc = "\n".join([
                    f"**{idx+1}. {user.username}** — {user.balance:,} pitchforks" 
                    for idx, user in enumerate(users)
                ])
                embed = discord.Embed(
                    title="🏆 Pitchfork Leaderboard",
                    description=desc or "No users found.",
                    color=discord.Color.gold()
                )
                await ctx.respond(embed=embed)
                
            except Exception as e:
                cog_logger.error(f"Error showing leaderboard: {e}")
                await ctx.respond("❌ Error retrieving leaderboard.", ephemeral=True)

    @discord.slash_command(name="give_all", description="Give pitchforks to all users (Admin only)")
    async def give_all(self, ctx, amount: int):
        """Give pitchforks to all users (Admin only)."""
        if not ctx.user.guild_permissions.administrator:
            await ctx.respond("❌ You do not have permission to use this command.", ephemeral=True)
            return

        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return

        if amount <= 0:
            await ctx.respond("❌ Amount must be greater than 0.", ephemeral=True)
            return

        with self.app.app_context():
            try:
                users = self.User.query.all()
                for user in users:
                    user.balance += amount
                self.db.session.commit()
                
                embed = discord.Embed(
                    title="💰 Mass Pitchfork Distribution",
                    description=f"Successfully gave **{amount:,} pitchforks** to all {len(users)} users!",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Distributed by",
                    value=ctx.user.mention,
                    inline=True
                )
                await ctx.respond(embed=embed)
                
            except Exception as e:
                cog_logger.error(f"Error giving pitchforks to all users: {e}")
                self.db.session.rollback()
                await ctx.respond("❌ Error distributing pitchforks.", ephemeral=True)

    @discord.slash_command(name="give", description="Give pitchforks to a specific user (Admin only)")
    async def give(self, ctx, user: discord.Member, amount: int):
        """Give pitchforks to a specific user (Admin only)."""
        if not ctx.user.guild_permissions.administrator:
            await ctx.respond("❌ You do not have permission to use this command.", ephemeral=True)
            return

        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return

        if amount <= 0:
            await ctx.respond("❌ Amount must be greater than 0.", ephemeral=True)
            return

        with self.app.app_context():
            try:
                # Get or create the target user
                target_user = self.User.query.filter_by(id=str(user.id)).first()
                if not target_user:
                    target_user = self.User(
                        id=str(user.id), 
                        username=user.display_name, 
                        discord_id=str(user.id)
                    )
                    self.db.session.add(target_user)
                    self.db.session.flush()
                
                # Add points to the user's balance
                target_user.balance += amount
                self.db.session.commit()
                
                # Send confirmation message
                embed = discord.Embed(
                    title="💰 Pitchforks Awarded",
                    description=f"Successfully gave **{amount:,} pitchforks** to {user.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="New Balance",
                    value=f"{target_user.balance:,} pitchforks",
                    inline=True
                )
                embed.add_field(
                    name="Awarded by",
                    value=ctx.user.mention,
                    inline=True
                )
                
                await ctx.respond(embed=embed)
                
                # Try to notify the user via DM
                try:
                    dm_embed = discord.Embed(
                        title="🎉 Pitchforks Received!",
                        description=f"You've received **{amount:,} pitchforks** from an admin!",
                        color=discord.Color.gold()
                    )
                    dm_embed.add_field(
                        name="New Balance",
                        value=f"{target_user.balance:,} pitchforks",
                        inline=True
                    )
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    # User has DMs disabled
                    pass
                
            except Exception as e:
                cog_logger.error(f"Error giving pitchforks to {user.id}: {e}")
                self.db.session.rollback()
                await ctx.respond("❌ Error awarding pitchforks.", ephemeral=True)

    @discord.slash_command(name="limits", description="View your earning limits and theoretical maximum pitchforks")
    async def limits(self, ctx):
        """View earning limits and theoretical maximum pitchforks."""
        if not self._is_economy_enabled():
            await ctx.respond("❌ Economy system is currently disabled.", ephemeral=True)
            return

        with self.app.app_context():
            try:
                user = self._get_or_create_user(ctx.user)
                if not user:
                    await ctx.respond("❌ Error accessing your account.", ephemeral=True)
                    return
                
                # Get current usage
                daily_claims_used = getattr(user, 'daily_claims_count', 0) or 0
                campus_photos_used = getattr(user, 'campus_photos_count', 0) or 0
                daily_engagement_used = getattr(user, 'daily_engagement_count', 0) or 0
                
                # Calculate remaining
                daily_claims_remaining = max(0, ActivityLimits.MAX_DAILY_CLAIMS - daily_claims_used)
                campus_photos_remaining = max(0, ActivityLimits.MAX_CAMPUS_PHOTOS - campus_photos_used)
                daily_engagement_remaining = max(0, ActivityLimits.MAX_DAILY_ENGAGEMENT - daily_engagement_used)
                
                # Calculate theoretical maximum pitchforks
                max_from_daily = ActivityLimits.MAX_DAILY_CLAIMS * 85
                max_from_campus = ActivityLimits.MAX_CAMPUS_PHOTOS * EconomyPoints.CAMPUS_PICTURE
                max_from_engagement = ActivityLimits.MAX_DAILY_ENGAGEMENT * EconomyPoints.DAILY_ENGAGEMENT
                max_from_deposit = EconomyPoints.ENROLLMENT_DEPOSIT
                max_from_birthday = EconomyPoints.BIRTHDAY_SETUP
                
                # Achievement points (approximate)
                total_achievement_points = sum(achievement.points for achievement in self.Achievement.query.all())
                
                theoretical_max = (max_from_daily + max_from_campus + max_from_engagement + 
                                 max_from_deposit + max_from_birthday + total_achievement_points)
                
                embed = discord.Embed(
                    title="📊 Your Earning Limits",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🎯 Daily Claims",
                    value=f"Used: {daily_claims_used}/{ActivityLimits.MAX_DAILY_CLAIMS}\nRemaining: {daily_claims_remaining}",
                    inline=True
                )
                
                embed.add_field(
                    name="📸 Campus Photos",
                    value=f"Used: {campus_photos_used}/{ActivityLimits.MAX_CAMPUS_PHOTOS}\nRemaining: {campus_photos_remaining}",
                    inline=True
                )
                
                embed.add_field(
                    name="💬 Daily Engagement",
                    value=f"Used: {daily_engagement_used}/{ActivityLimits.MAX_DAILY_ENGAGEMENT}\nRemaining: {daily_engagement_remaining}",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Theoretical Maximum",
                    value=f"{theoretical_max:,} pitchforks",
                    inline=False
                )
                
                embed.add_field(
                    name="💰 Current Balance",
                    value=f"{user.balance:,} pitchforks",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Progress",
                    value=f"{(user.balance / theoretical_max * 100):.1f}% of maximum",
                    inline=True
                )
                
                embed.set_footer(text="Limits reset when the economy is enabled for the first time")
                
                await ctx.respond(embed=embed, ephemeral=True)
                
            except Exception as e:
                cog_logger.error(f"Error showing limits for {ctx.user.id}: {e}")
                await ctx.respond("❌ Error retrieving your limits.", ephemeral=True)

    @discord.slash_command(name="help", description="Learn how to earn pitchforks in the Devil2Devil economy")
    async def help_command(self, ctx):
        """Show help information about earning pitchforks."""
        embed = discord.Embed(
            title="🔱 Devil2Devil Economy Help",
            description="Learn how to earn pitchforks in our economy system!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="💰 Daily Rewards",
            value="Use `/daily` to claim 85 pitchforks once per day",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Activity Bonuses",
            value="• Send messages in channels\n• React to messages\n• Join voice channels\n• Get verified and complete onboarding",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Achievements",
            value="Unlock achievements by being active! Use `/achievements` to see your progress.",
            inline=False
        )
        
        embed.add_field(
            name="📊 Other Commands",
            value="• `/balance` - Check your pitchfork balance\n• `/leaderboard` - See top users\n• `/limits` - View your earning limits",
            inline=False
        )
        
        embed.add_field(
            name="🛒 Spending Pitchforks",
            value="Visit the web store to spend your pitchforks on roles, skins, and other items!",
            inline=False
        )
        
        embed.set_footer(text="Economy system managed by Devil2Devil staff")
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot, app, db, User, EconomySettings, Achievement, UserAchievement):
    """Setup function for the cog."""
    return EconomyCog(bot, app, db, User, EconomySettings, Achievement, UserAchievement) 