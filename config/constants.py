"""
Constants and configuration values for the Economy application.
"""

# Point values for each activity
class EconomyPoints:
    DAILY_REWARD = 85
    DAILY_ENGAGEMENT = 25
    CAMPUS_PICTURE = 100
    ENROLLMENT_DEPOSIT = 500
    BIRTHDAY_SETUP = 50
    VERIFICATION_BONUS = 200
    ONBOARDING_BONUS = 500

# Limits for recurring activities
class ActivityLimits:
    MAX_DAILY_CLAIMS = 90
    MAX_CAMPUS_PHOTOS = 5
    MAX_DAILY_ENGAGEMENT = 365
    MAX_VOICE_MINUTES = 10000
    MAX_MESSAGES = 50000
    MAX_REACTIONS = 25000

# Time-based configurations
class TimeConfig:
    DAILY_COOLDOWN_HOURS = 24
    DAILY_ENGAGEMENT_COOLDOWN_HOURS = 20
    BIRTHDAY_CHECK_TIME = "09:30"  # Time in MST (24-hour format)
    
# Custom emoji reward system
class CustomEmojis:
    CAMPUS_PICTURE = "campus_photo"
    DAILY_ENGAGEMENT = "daily_engage"
    ENROLLMENT_DEPOSIT = "deposit_check"

# Discord Configuration
class DiscordConfig:
    GUILD_ID = "1082823852322725888"  # Default test guild ID

# Discord OAuth scopes
DISCORD_SCOPES = 'identify guilds guilds.members.read'

# File upload configurations
class FileConfig:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip', 'rar'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'

# Product types
class ProductTypes:
    PHYSICAL = 'physical'
    ROLE = 'role'
    MINECRAFT_SKIN = 'minecraft_skin'
    GAME_CODE = 'game_code'
    CUSTOM = 'custom'

# Delivery methods
class DeliveryMethods:
    AUTO_ROLE = 'auto_role'
    MANUAL = 'manual'
    DOWNLOAD = 'download'
    CODE_GENERATION = 'code_generation'

# Purchase statuses
class PurchaseStatus:
    COMPLETED = 'completed'
    PENDING_DELIVERY = 'pending_delivery'
    FAILED = 'failed'

# Role assignment statuses
class RoleAssignmentStatus:
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

# Achievement types
class AchievementTypes:
    MESSAGE = 'message'
    REACTION = 'reaction'
    VOICE = 'voice'
    SPECIAL = 'special'

# Database table names (for consistency)
class TableNames:
    USER = 'user'
    PRODUCT = 'product'
    PURCHASE = 'purchase'
    ACHIEVEMENT = 'achievement'
    USER_ACHIEVEMENT = 'user_achievement'
    ECONOMY_SETTINGS = 'economy_settings'
    ROLE_ASSIGNMENT = 'role_assignment'
    DOWNLOAD_TOKEN = 'download_token'

# Environment variable names
class EnvVars:
    DISCORD_TOKEN = 'DISCORD_TOKEN'
    DISCORD_CLIENT_ID = 'DISCORD_CLIENT_ID'
    DISCORD_CLIENT_SECRET = 'DISCORD_CLIENT_SECRET'
    DISCORD_REDIRECT_URI = 'DISCORD_REDIRECT_URI'
    SECRET_KEY = 'SECRET_KEY'
    DATABASE_URL = 'DATABASE_URL'
    GUILD_ID = 'GUILD_ID'
    GENERAL_CHANNEL_ID = 'GENERAL_CHANNEL_ID'
    VERIFIED_ROLE_ID = 'VERIFIED_ROLE_ID'

# Default achievement configurations
ACHIEVEMENT_DEFINITIONS = [
    {
        'name': 'First Steps',
        'description': 'Send your first message',
        'points': 10,
        'type': AchievementTypes.MESSAGE,
        'requirement': 1
    },
    {
        'name': 'Chatterbox',
        'description': 'Send 100 messages',
        'points': 50,
        'type': AchievementTypes.MESSAGE,
        'requirement': 100
    },
    {
        'name': 'Social Butterfly',
        'description': 'Send 500 messages',
        'points': 150,
        'type': AchievementTypes.MESSAGE,
        'requirement': 500
    },
    {
        'name': 'Community Leader',
        'description': 'Send 1000 messages',
        'points': 300,
        'type': AchievementTypes.MESSAGE,
        'requirement': 1000
    },
    {
        'name': 'Legend',
        'description': 'Send 5000 messages',
        'points': 500,
        'type': AchievementTypes.MESSAGE,
        'requirement': 5000
    },
    {
        'name': 'First Reaction',
        'description': 'React to your first message',
        'points': 5,
        'type': AchievementTypes.REACTION,
        'requirement': 1
    },
    {
        'name': 'Reactor',
        'description': 'React to 50 messages',
        'points': 25,
        'type': AchievementTypes.REACTION,
        'requirement': 50
    },
    {
        'name': 'Super Reactor',
        'description': 'React to 250 messages',
        'points': 75,
        'type': AchievementTypes.REACTION,
        'requirement': 250
    },
    {
        'name': 'Reaction Master',
        'description': 'React to 1000 messages',
        'points': 200,
        'type': AchievementTypes.REACTION,
        'requirement': 1000
    },
    {
        'name': 'Voice Newbie',
        'description': 'Spend 30 minutes in voice chat',
        'points': 25,
        'type': AchievementTypes.VOICE,
        'requirement': 30
    },
    {
        'name': 'Voice Regular',
        'description': 'Spend 2 hours in voice chat',
        'points': 50,
        'type': AchievementTypes.VOICE,
        'requirement': 120
    },
    {
        'name': 'Voice Enthusiast',
        'description': 'Spend 10 hours in voice chat',
        'points': 150,
        'type': AchievementTypes.VOICE,
        'requirement': 600
    },
    {
        'name': 'Voice Addict',
        'description': 'Spend 24 hours in voice chat',
        'points': 300,
        'type': AchievementTypes.VOICE,
        'requirement': 1440
    }
] 