import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Bot(
    intents=intents,
    test_guilds=[1082823852322725888]  # Add testing guild for faster command syncing
)

# Global variables to store app and db instances
app_instance = None
db_instance = None
User = None
Achievement = None
UserAchievement = None

def init_bot_with_app(app, db, user_model, achievement_model, user_achievement_model):
    """Initialize bot with app and database instances."""
    global app_instance, db_instance, User, Achievement, UserAchievement
    app_instance = app
    db_instance = db
    User = user_model
    Achievement = achievement_model
    UserAchievement = user_achievement_model

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    print(f"Bot is ready! Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} guilds")
    await bot.change_presence(activity=discord.Game(name="Managing Economy"))

@bot.slash_command(name="balance", description="Check your current balance")
async def balance(ctx):
    """Check your current balance"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(ctx.author.id)).first()
        if not user:
            user = User(id=str(ctx.author.id), username=ctx.author.name)
            db_instance.session.add(user)
            db_instance.session.commit()
        
        embed = discord.Embed(
            title="Balance",
            description=f"Your current balance: {user.balance} points",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

@bot.slash_command(name="daily", description="Claim your daily points reward")
async def daily(ctx):
    """Claim your daily points"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(ctx.author.id)).first()
        if not user:
            user = User(id=str(ctx.author.id), username=ctx.author.name)
            db_instance.session.add(user)
            db_instance.session.commit()

        # Check if user can claim daily points
        if user.last_daily and (datetime.now() - user.last_daily) < timedelta(days=1):
            time_left = user.last_daily + timedelta(days=1) - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            embed = discord.Embed(
                title="⏰ Daily Reward Not Ready",
                description=f"You can claim your daily points again in {hours} hours and {minutes} minutes.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Update user's balance and last_daily
        user.balance += 85
        user.last_daily = datetime.now()
        db_instance.session.commit()

        embed = discord.Embed(
            title="🎉 Daily Reward Claimed!",
            description=f"You received **85 points**!\nYour new balance is **{user.balance} points**",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Next daily reward available in 24 hours")
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="leaderboard", description="Show the top 10 users by balance")
async def leaderboard(ctx):
    """Show the top 10 users by balance"""
    with app_instance.app_context():
        top_users = User.query.order_by(User.balance.desc()).limit(10).all()
        
        embed = discord.Embed(
            title="🏆 Leaderboard",
            color=discord.Color.gold()
        )
        
        for i, user in enumerate(top_users, 1):
            embed.add_field(
                name=f"{i}. {user.username}",
                value=f"Balance: {user.balance} points",
                inline=False
            )
        
        await ctx.respond(embed=embed)

@bot.slash_command(name="give_all", description="Give points to all users (Admin only)")
@commands.has_permissions(administrator=True)
async def give_all(ctx, amount: int):
    """Give points to all users"""
    with app_instance.app_context():
        users = User.query.all()
        for user in users:
            user.balance += amount
        db_instance.session.commit()
        await ctx.respond(f"Added {amount} points to all users!")

@give_all.error
async def give_all_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("You don't have permission to use this command!", ephemeral=True)

@bot.event
async def on_message(message):
    """Track messages and check achievements."""
    if message.author.bot:
        return

    with app_instance.app_context():
        user = User.query.filter_by(id=str(message.author.id)).first()
        if not user:
            user = User(id=str(message.author.id), username=message.author.name)
            db_instance.session.add(user)
        
        user.message_count += 1
        db_instance.session.commit()
        
        # Check message achievements
        await check_achievements(user, 'message')

@bot.event
async def on_reaction_add(reaction, user):
    """Track reactions and check achievements."""
    if user.bot:
        return

    with app_instance.app_context():
        db_user = User.query.filter_by(id=str(user.id)).first()
        if not db_user:
            db_user = User(id=str(user.id), username=user.name)
            db_instance.session.add(db_user)
        
        db_user.reaction_count += 1
        db_instance.session.commit()
        
        # Check reaction achievements
        await check_achievements(db_user, 'reaction')

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
    """Track server boosts and check achievements."""
    if before.premium_since is None and after.premium_since is not None:
        with app_instance.app_context():
            user = User.query.filter_by(id=str(after.id)).first()
            if not user:
                user = User(id=str(after.id), username=after.name)
                db_instance.session.add(user)
            
            user.has_boosted = True
            db_instance.session.commit()
            
            # Check boost achievements
            await check_achievements(user, 'boost')

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

@bot.slash_command(name="achievements", description="View your achievements")
async def achievements(ctx):
    """View your achievements"""
    with app_instance.app_context():
        user = User.query.filter_by(id=str(ctx.author.id)).first()
        if not user:
            user = User(id=str(ctx.author.id), username=ctx.author.name)
            db_instance.session.add(user)
            db_instance.session.commit()
        
        # Get user's achievements
        user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
        
        embed = discord.Embed(
            title="🏆 Your Achievements",
            color=discord.Color.gold()
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
        await ctx.respond(embed=embed, ephemeral=True)

def run_bot():
    """Run the Discord bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    print("Starting Discord bot...")
    print(f"Token length: {len(token)}")
    bot.run(token)

if __name__ == "__main__":
    run_bot() 