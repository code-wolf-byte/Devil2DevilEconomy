import sys
import subprocess

# Auto-setup functionality
def ensure_dependencies():
    """Ensure all required packages are installed"""
    required_packages = [
        'flask==3.0.2',
        'nextcord==2.6.0', 
        'sqlalchemy==2.0.27',
        'python-dotenv==1.0.1',
        'flask-sqlalchemy==3.1.1',
        'flask-login==0.6.3',
        'PyNaCl==1.5.0',
        'qrcode==7.4.2',
        'pillow==10.2.0',
        'requests==2.31.0',
        'pytz==2024.1',
        'flask-migrate==4.0.5'
    ]
    
    missing_packages = []
    for package in required_packages:
        package_name = package.split('==')[0]
        try:
            __import__(package_name.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("🔧 Installing missing dependencies...")
        for package in missing_packages:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✅ Dependencies installed successfully!")

def create_env_file():
    """Create .env file with default values if it doesn't exist"""
    import os
    if not os.path.exists('.env'):
        print("🔧 Creating .env file with default values...")
        env_content = """# Discord Bot Configuration
# Get these from Discord Developer Portal: https://discord.com/developers/applications
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here  
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:6000/callback

# Flask Configuration
SECRET_KEY=your_super_secret_key_change_this_in_production

# Database Configuration  
DATABASE_URL=sqlite:///store.db

# Guild Configuration (Optional - for Discord server integration)
GUILD_ID=your_guild_id_here
GENERAL_CHANNEL_ID=your_general_channel_id_here

# Role Configuration for Economy System (Optional)
VERIFIED_ROLE_ID=your_verified_role_id_here
# ONBOARDING_ROLE_IDS=role1_id,role2_id,role3_id  # Now configured via webapp admin panel
"""
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            print("✅ .env file created! Please edit it with your Discord bot credentials.")
            return True
        except (OSError, PermissionError) as e:
            print(f"⚠️  Could not create .env file: {e}")
            print("   This is normal in Docker environments. Using environment variables instead.")
            return False
    return False

def setup_directories():
    """Create required directories"""
    import os
    directories = ['logs', 'static/uploads', 'instance']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")

def check_configuration():
    """Check if required configuration is present"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['DISCORD_TOKEN', 'DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower()}_here':
            missing_vars.append(var)
    
    return missing_vars

# Run auto-setup
print("🚀 Economy Bot Auto-Setup")
print("=" * 40)

ensure_dependencies()
setup_directories()
env_created = create_env_file()

# Now import everything else
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import datetime as dt
from werkzeug.utils import secure_filename
import requests
import threading
import os
import uuid
import json
import asyncio
import logging
import logging.handlers
from contextlib import contextmanager
from flask_migrate import Migrate

from dotenv import load_dotenv

# Load environment variables with explicit path
load_dotenv()

missing_config = check_configuration()
if missing_config:
    print("\n⚠️  Configuration Required:")
    print("Please set the following environment variables:")
    for var in missing_config:
        print(f"   - {var}")
    print("\n📖 To get Discord bot credentials:")
    print("   1. Go to https://discord.com/developers/applications")
    print("   2. Create a new application")
    print("   3. Go to the 'Bot' section and create a bot")
    print("   4. Copy the token to DISCORD_TOKEN")
    print("   5. Go to 'OAuth2' section for CLIENT_ID and CLIENT_SECRET")
    
    # In Docker, we should continue with default values rather than exit
    if env_created and not os.getenv('DOCKER_ENV'):
        print(f"\n🔧 Then restart the application: python {sys.argv[0]}")
        sys.exit(1)
    else:
        print("\n⚠️  Running with default configuration. Some features may not work properly.")

print("✅ Setup complete! Starting application...\n")

# Configure logging
def setup_logging():
    """Set up centralized logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add console handler first
    root_logger.addHandler(console_handler)
    
    # Try to add file handlers, but continue if they fail (Docker environments)
    try:
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'economy_app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'economy_errors.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
    except (OSError, PermissionError) as e:
        print(f"⚠️  Could not set up file logging: {e}")
        print("   Continuing with console logging only (normal in Docker environments)")
    
    # Create specific loggers for different components
    app_logger = logging.getLogger('economy.app')
    bot_logger = logging.getLogger('economy.bot')
    cog_logger = logging.getLogger('economy.cogs')
    
    return app_logger, bot_logger, cog_logger

# Initialize logging
app_logger, bot_logger, cog_logger = setup_logging()

# Initialize Flask app and extensions
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.urandom(24)
# Use absolute path for database to avoid path resolution issues
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'store.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'pool_size': 10,
    'max_overflow': 20
}

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@contextmanager
def db_transaction():
    """Database transaction context manager with proper error handling."""
    try:
        db.session.begin()
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Database transaction rolled back: {e}")
        raise
    finally:
        db.session.close()

# Helper function to construct Discord avatar URL
def get_discord_avatar_url(user_id, avatar_hash):
    """Construct Discord avatar URL from user ID and avatar hash."""
    if not avatar_hash:
        # Use default Discord avatar based on discriminator
        # For new Discord usernames (without discriminator), use user ID
        return f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png"
    
    # Check if avatar is animated (starts with 'a_')
    if avatar_hash.startswith('a_'):
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.gif"
    else:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {
        # Images
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz', 'tar.gz',
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'md', 'rtf',
        # Audio
        'mp3', 'wav', 'ogg', 'flac', 'm4a',
        # Video
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'ogv',
        # Minecraft specific
        'mcpack', 'mcworld', 'mctemplate', 'mcaddon',
        # Other
        'json', 'xml', 'csv', 'exe', 'msi'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, file_type='image'):
    """Save uploaded file securely and return filename"""
    try:
        # Generate secure filename (prevent any directory traversal)
        original_filename = secure_filename(file.filename)
        # Remove any remaining path separators and dots
        safe_filename = original_filename.replace('..', '').replace('/', '').replace('\\', '')
        if not safe_filename:
            safe_filename = 'upload'
        
        # Generate completely new filename with safe extension
        file_ext = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else 'jpg'
        
        # Validate extension based on file type
        if file_type == 'image':
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                file_ext = 'jpg'
        elif file_type == 'preview':
            # Allow both images and videos for preview
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'ogv', 'mov'}:
                file_ext = 'jpg'
        
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Ensure upload directory exists and is secure
        upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create full file path and verify it's within upload directory
        file_path = os.path.abspath(os.path.join(upload_dir, unique_filename))
        if not file_path.startswith(upload_dir):
            app_logger.error('Invalid file path detected during upload')
            return None
        
        # Validate file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            app_logger.error(f'File too large: {file_size} bytes')
            return None
        
        # Save file
        file.save(file_path)
        app_logger.info(f"{file_type.capitalize()} uploaded successfully: {unique_filename}")
        return unique_filename
        
    except Exception as e:
        app_logger.error(f"Error saving uploaded file: {e}")
        return None


# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Discord configuration with fallbacks and debugging
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:6000/callback')
DISCORD_OAUTH_SCOPE = 'identify guilds guilds.members.read'
DISCORD_API_BASE_URL = 'https://discord.com/api'

# Check for required environment variables with graceful handling
def validate_environment():
    """Validate environment variables with helpful error messages"""
    errors = []
    
    if not DISCORD_CLIENT_ID or DISCORD_CLIENT_ID == 'your_discord_client_id_here':
        errors.append("DISCORD_CLIENT_ID")
    if not DISCORD_CLIENT_SECRET or DISCORD_CLIENT_SECRET == 'your_discord_client_secret_here':
        errors.append("DISCORD_CLIENT_SECRET")
    
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token or discord_token == 'your_discord_bot_token_here':
        errors.append("DISCORD_TOKEN")
    
    if errors:
        app_logger.critical("Missing required Discord configuration!")
        app_logger.critical("Please set the following environment variables in your .env file:")
        for var in errors:
            app_logger.critical(f"  - {var}")
        app_logger.critical("\nTo get these values:")
        app_logger.critical("1. Go to https://discord.com/developers/applications")
        app_logger.critical("2. Create or select your application")
        app_logger.critical("3. Copy the Application ID to DISCORD_CLIENT_ID")
        app_logger.critical("4. Go to OAuth2 -> General for CLIENT_SECRET")
        app_logger.critical("5. Go to Bot section for DISCORD_TOKEN")
        app_logger.critical("\nThe bot will start in web-only mode until configured.")
        return False
    
    return True

discord_configured = validate_environment()

# Get Discord Token for bot functionality (with fallback)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') if discord_configured else None

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    discord_id = db.Column(db.String(20), unique=True)
    avatar_url = db.Column(db.String(500))  # Store Discord avatar URL
    user_uuid = db.Column(db.String(36), unique=True)  # Store unique UUID for each user
    is_admin = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer, default=0)
    balance = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    messages_reacted_to = db.Column(db.Integer, default=0)
    last_daily = db.Column(db.DateTime)
    last_daily_engagement = db.Column(db.DateTime)
    enrollment_deposit_received = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_count = db.Column(db.Integer, default=0)
    reaction_count = db.Column(db.Integer, default=0)
    voice_minutes = db.Column(db.Integer, default=0)
    has_boosted = db.Column(db.Boolean, default=False)
    birthday = db.Column(db.Date)  # Store user's birthday (month/day)
    birthday_points_received = db.Column(db.Boolean, default=False)  # Track if user got points for setting birthday
    verification_bonus_received = db.Column(db.Boolean, default=False)  # Track if user got verification bonus
    onboarding_bonus_received = db.Column(db.Boolean, default=False)  # Track if user got onboarding bonus
    
    # Earning limit tracking columns
    daily_claims_count = db.Column(db.Integer, default=0)  # Track number of daily claims used
    campus_photos_count = db.Column(db.Integer, default=0)  # Track number of campus photo approvals
    daily_engagement_count = db.Column(db.Integer, default=0)  # Track number of daily engagement approvals
    
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=True, default=None)  # None = unlimited, 0 = out of stock, >0 = limited stock
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # True = visible in store, False = archived/hidden
    archived_at = db.Column(db.DateTime)  # When the product was archived
    
    # Digital product fields
    product_type = db.Column(db.String(50), default='physical')  # physical, role, minecraft_skin, game_code, custom
    delivery_method = db.Column(db.String(50))  # auto_role, manual, download, code_generation
    delivery_data = db.Column(db.Text)  # JSON data for delivery (role_id, file_path, etc.)
    auto_delivery = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='general')
    
    # Minecraft skin specific fields
    preview_image_url = db.Column(db.String(200))  # Preview image for minecraft skins
    download_file_url = db.Column(db.String(200))  # Actual downloadable file for minecraft skins
    
    def __repr__(self):
        return f'<Product {self.name} ({self.product_type})>'
    
    @property
    def is_digital(self):
        return self.product_type != 'physical'
    
    @property
    def delivery_config(self):
        """Parse delivery_data as JSON"""
        import json
        try:
            return json.loads(self.delivery_data) if self.delivery_data else {}
        except:
            return {}
    
    @property
    def display_image(self):
        """Get the appropriate image for display (preview for minecraft skins, regular image for others)"""
        if self.product_type == 'minecraft_skin' and self.preview_image_url:
            return self.preview_image_url
        return self.image_url
    
    @property
    def has_dual_files(self):
        """Check if this product uses dual-file system (minecraft skins)"""
        return self.product_type == 'minecraft_skin' and self.preview_image_url and self.download_file_url

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_info = db.Column(db.Text)  # Store delivery details (codes, download links, etc.)
    status = db.Column(db.String(20), default='completed')  # completed, pending_delivery, failed

    user = db.relationship('User', backref=db.backref('purchases', lazy=True))
    product = db.relationship('Product', backref=db.backref('purchases', lazy=True))

    def __repr__(self):
        return f'<Purchase {self.id}>'

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    requirement = db.Column(db.Integer, nullable=False)
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f'<Achievement {self.name}>'

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>'

class EconomySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    economy_enabled = db.Column(db.Boolean, default=False)
    first_time_enabled = db.Column(db.Boolean, default=True)  # Track if it's the first time being enabled
    enabled_at = db.Column(db.DateTime)
    
    # Role configurations for first-time economy setup
    verified_role_id = db.Column(db.String(20))  # Discord role ID for verified users
    onboarding_role_ids = db.Column(db.Text)  # JSON array of Discord role IDs for onboarding
    verified_bonus_points = db.Column(db.Integer, default=200)  # Points to award for verified role
    onboarding_bonus_points = db.Column(db.Integer, default=500)  # Points to award for onboarding roles
    
    # Configuration completion flag
    roles_configured = db.Column(db.Boolean, default=False)  # Whether roles have been configured
    
    def __repr__(self):
        return f'<EconomySettings enabled={self.economy_enabled}>'
    
    @property
    def onboarding_roles_list(self):
        """Get onboarding role IDs as a list"""
        import json
        try:
            return json.loads(self.onboarding_role_ids) if self.onboarding_role_ids else []
        except:
            return []
    
    def set_onboarding_roles(self, role_ids):
        """Set onboarding role IDs from a list"""
        import json
        self.onboarding_role_ids = json.dumps(role_ids) if role_ids else None

# Digital Product Support Models
class RoleAssignment(db.Model):
    """Queue for Discord role assignments"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.String(20), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    user = db.relationship('User', backref='role_assignments')
    purchase = db.relationship('Purchase', backref='role_assignment')

class DownloadToken(db.Model):
    """Secure download tokens for digital products"""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship('User', backref='download_tokens')
    purchase = db.relationship('Purchase', backref='download_tokens')

# Initialize database and migrations
def setup_database():
    """Initialize database and run migrations if needed"""
    with app.app_context():
        try:
            # Try to create migration repository if it doesn't exist
            if not os.path.exists('migrations'):
                app_logger.info("Initializing database migrations...")
                from flask_migrate import init
                init()
                app_logger.info("Migration repository created")
            
            # Create all tables
            db.create_all()
            app_logger.info("Database tables created successfully")
            
            # Check if we need to run migrations
            try:
                from flask_migrate import upgrade
                upgrade()
                app_logger.info("Database migrations applied successfully")
            except Exception as migration_error:
                app_logger.warning(f"Migration warning (this is usually normal on first run): {migration_error}")
                
        except Exception as e:
            app_logger.error(f"Database setup error: {e}")
            # Fallback to simple table creation
            db.create_all()
            app_logger.info("Database tables created with fallback method")

setup_database()

# Initialize achievements
def setup_achievements():
    """Initialize default achievements"""
    with app.app_context():
        achievements = [
            {
                'name': 'Daily Reward',
                'description': 'Claim your daily reward',
                'points': 85,
                'type': 'daily',
                'requirement': 1
            },
            {
                'name': 'Join Server',
                'description': 'Join the server for the first time',
                'points': 213,
                'type': 'join',
                'requirement': 1
            },
            {
                'name': 'First Message',
                'description': 'Send your first message',
                'points': 425,
                'type': 'message',
                'requirement': 1
            },
            {
                'name': 'Verified',
                'description': 'Get verified in the server',
                'points': 200,
                'type': 'verification',
                'requirement': 1
            },
            # Message milestones
            {
                'name': 'Chatty',
                'description': 'Send 100 messages in the server',
                'points': 50,
                'type': 'message',
                'requirement': 100
            },
            {
                'name': 'Conversationalist',
                'description': 'Send 1000 messages in the server',
                'points': 100,
                'type': 'message',
                'requirement': 1000
            },
            # Reaction milestones
            {
                'name': 'Reactor',
                'description': 'React to 50 messages',
                'points': 50,
                'type': 'reaction',
                'requirement': 50
            },
            {
                'name': 'Super Reactor',
                'description': 'React to 500 messages',
                'points': 100,
                'type': 'reaction',
                'requirement': 500
            }
            # Add more achievements as needed
        ]

        for achievement_data in achievements:
            achievement = Achievement.query.filter_by(name=achievement_data['name']).first()
            if not achievement:
                achievement = Achievement(**achievement_data)
                db.session.add(achievement)
        
        db.session.commit()
        app_logger.info("Achievements initialized successfully")

setup_achievements()

def setup_economy_settings():
    """Initialize default economy settings"""
    with app.app_context():
        settings = EconomySettings.query.first()
        if not settings:
            settings = EconomySettings(
                economy_enabled=False,
                first_time_enabled=False,  # False means it hasn't been enabled for the first time yet
                enabled_at=None
            )
            db.session.add(settings)
            db.session.commit()
            app_logger.info("Economy settings initialized successfully")

setup_economy_settings()

def update_minecraft_skin_delivery_methods():
    """Update existing Minecraft skin products to have proper delivery method for auto-download"""
    try:
        with app.app_context():
            minecraft_skins = Product.query.filter_by(product_type='minecraft_skin').all()
            updated_count = 0
            
            for product in minecraft_skins:
                if product.delivery_method != 'download' or not product.auto_delivery:
                    product.delivery_method = 'download'
                    product.auto_delivery = True
                    updated_count += 1
                    app_logger.info(f"Updated delivery method for Minecraft skin: {product.name}")
            
            if updated_count > 0:
                db.session.commit()
                app_logger.info(f"Updated {updated_count} Minecraft skin products for auto-download")
            else:
                app_logger.info("All Minecraft skin products already have correct delivery method")
                
    except Exception as e:
        app_logger.error(f"Error updating Minecraft skin delivery methods: {e}")
        db.session.rollback()

# Run the update function
update_minecraft_skin_delivery_methods()

def migrate_product_active_status():
    """Ensure all existing products are marked as active"""
    try:
        with app.app_context():
            # Find products with NULL is_active status (from before the column was added)
            products_to_update = Product.query.filter(Product.is_active.is_(None)).all()
            
            if products_to_update:
                for product in products_to_update:
                    product.is_active = True
                
                db.session.commit()
                app_logger.info(f"Migrated {len(products_to_update)} products to active status")
            else:
                app_logger.info("All products already have active status set")
                
    except Exception as e:
        app_logger.error(f"Error migrating product active status: {e}")
        try:
            db.session.rollback()
        except RuntimeError:
            pass

# Run the migration
migrate_product_active_status()

# Initialize login manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, str(user_id))

# Digital Product Delivery System
class DigitalDeliveryService:
    """Service for handling digital product delivery"""
    
    @staticmethod
    def deliver_product(user, product, purchase):
        """Deliver digital product to user based on product type"""
        try:
            if product.delivery_method == 'auto_role':
                return DigitalDeliveryService._deliver_discord_role(user, product, purchase)
            elif product.delivery_method == 'code_generation':
                return DigitalDeliveryService._generate_code(user, product, purchase)
            elif product.delivery_method == 'download':
                return DigitalDeliveryService._prepare_download(user, product, purchase)
            elif product.delivery_method == 'manual':
                return DigitalDeliveryService._queue_manual_delivery(user, product, purchase)
            else:
                return False, "Unknown delivery method"
        except Exception as e:
            app_logger.error(f"Digital delivery error: {e}")
            return False, f"Delivery failed: {str(e)}"
    
    @staticmethod
    def _deliver_discord_role(user, product, purchase):
        """Deliver Discord role to user"""
        delivery_config = product.delivery_config
        role_id = delivery_config.get('role_id')
        
        if not role_id:
            return False, "Role ID not configured"
        
        # Queue role assignment for bot to process
        role_assignment = RoleAssignment(
            user_id=user.id,
            role_id=role_id,
            purchase_id=purchase.id,
            status='pending'
        )
        db.session.add(role_assignment)
        db.session.commit()
        
        return True, f"Discord role will be assigned within 1 minute"
    
    @staticmethod
    def _generate_code(user, product, purchase):
        """Generate unique code for user"""
        delivery_config = product.delivery_config
        code_pattern = delivery_config.get('code_pattern', 'GAME-{uuid}')
        
        # Generate unique code
        unique_code = code_pattern.format(
            uuid=str(uuid.uuid4())[:8].upper(),
            user_id=user.id,
            product_id=product.id
        )
        
        # Store code in purchase notes (we'll need to add this field)
        purchase.delivery_info = f"Generated code: {unique_code}"
        db.session.commit()
        
        return True, f"Your code: **{unique_code}**"
    
    @staticmethod
    def _prepare_download(user, product, purchase):
        """Prepare download link for user"""
        # Handle dual-file system for Minecraft skins
        if product.product_type == 'minecraft_skin' and product.download_file_url:
            file_path = product.download_file_url
        else:
            # Use legacy delivery_config for other products
            delivery_config = product.delivery_config
            file_path = delivery_config.get('file_path')
        
        if not file_path:
            return False, "Download file not configured"
        
        # Generate secure download token
        download_token = str(uuid.uuid4())
        
        # Store download info
        from datetime import timedelta
        download_info = DownloadToken(
            token=download_token,
            user_id=user.id,
            purchase_id=purchase.id,
            file_path=file_path,
            expires_at=datetime.now(dt.timezone.utc) + timedelta(hours=24)
        )
        db.session.add(download_info)
        db.session.commit()
        
        download_url = f"/download/{download_token}"
        return True, f"Download link: {download_url} (expires in 24 hours)"
    
    @staticmethod
    def _queue_manual_delivery(user, product, purchase):
        """Queue product for manual delivery by admin"""
        purchase.delivery_info = f"Manual delivery required for {product.name}"
        db.session.commit()
        
        return True, "Your purchase is queued for manual delivery. You'll be contacted within 24 hours."

@app.route('/')
def index():
    # Only show active products in the storefront
    products = Product.query.filter_by(is_active=True).all()
    
    # Fix any None values in products before sending to template
    for product in products:
        if product.stock is None:
            product.stock = -1  # Use -1 to represent unlimited stock
    
    # Get current user's purchases if they're logged in
    user_purchases = []
    if current_user.is_authenticated:
        # Ensure current user has proper balance/points values
        if current_user.balance is None:
            current_user.balance = 0
        if current_user.points is None:
            current_user.points = 0
            
        user_purchases = Purchase.query.filter_by(user_id=current_user.id).all()
    
    return render_template('index.html', products=products, purchases=user_purchases)

@app.route('/login')
def login():
    return redirect(f"{DISCORD_API_BASE_URL}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope={DISCORD_OAUTH_SCOPE}")

@app.route('/callback')
def callback():
    try:
        code = request.args.get('code')
        if not code:
            flash('No code provided')
            return redirect(url_for('index'))
        
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        app_logger.debug(f"Requesting token with data: {data}")
        response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=data, headers=headers)
        app_logger.debug(f"Token response status: {response.status_code}")
        app_logger.debug(f"Token response: {response.text}")
        
        if response.status_code != 200:
            flash('Failed to get access token')
            return redirect(url_for('index'))
        
        access_token = response.json()['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers)
        app_logger.debug(f"User response status: {user_response.status_code}")
        app_logger.debug(f"User response: {user_response.text}")
        
        if user_response.status_code != 200:
            flash('Failed to get user info')
            return redirect(url_for('index'))
        
        user_data = user_response.json()
        app_logger.debug(f"User data: {user_data}")
        
        # Verify the Discord user ID matches the OAuth token
        if not user_data.get('id'):
            flash('Invalid Discord user data received')
            return redirect(url_for('index'))
        
        # Additional validation: Check token validity by re-requesting user info
        verify_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers)
        if verify_response.status_code != 200 or verify_response.json().get('id') != user_data['id']:
            flash('Authentication verification failed')
            return redirect(url_for('index'))
        
        # Check if user is admin in the Discord server
        is_admin = False
        guild_id = "1082823852322725888"  # Your test guild ID
        app_logger.info(f"Checking admin status for user: {user_data['username']} (ID: {user_data['id']})")
        
        try:
            # First, try to get guild member info using user token
            guild_member_response = requests.get(
                f"{DISCORD_API_BASE_URL}/users/@me/guilds/{guild_id}/member",
                headers=headers
            )
            app_logger.debug(f"Guild member API response status: {guild_member_response.status_code}")
            app_logger.debug(f"Guild member API response: {guild_member_response.text}")
            
            if guild_member_response.status_code == 200:
                member_data = guild_member_response.json()
                roles = member_data.get('roles', [])
                app_logger.debug(f"User roles: {roles}")
                
                # Get guild roles to check for admin permissions
                bot_token = os.getenv('DISCORD_TOKEN')
                if bot_token:
                    bot_headers = {'Authorization': f'Bot {bot_token}'}
                    roles_response = requests.get(
                        f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/roles",
                        headers=bot_headers
                    )
                    app_logger.debug(f"Guild roles API response status: {roles_response.status_code}")
                    
                    if roles_response.status_code == 200:
                        guild_roles = roles_response.json()
                        app_logger.debug(f"Found {len(guild_roles)} guild roles")
                        
                        for role_id in roles:
                            for guild_role in guild_roles:
                                if guild_role['id'] == role_id:
                                    permissions = int(guild_role.get('permissions', 0))
                                    app_logger.debug(f"Role '{guild_role['name']}' (ID: {role_id}) has permissions: {permissions}")
                                    
                                    # Check for Administrator permission (0x8) or Manage Server (0x20)
                                    if permissions & 0x8:
                                        is_admin = True
                                        app_logger.info(f"User has Administrator permission via role: {guild_role['name']}")
                                        break
                                    elif permissions & 0x20:
                                        is_admin = True
                                        app_logger.info(f"User has Manage Server permission via role: {guild_role['name']}")
                                        break
                            if is_admin:
                                break
                    else:
                        app_logger.warning(f"Failed to get guild roles: {roles_response.text}")
                else:
                    app_logger.warning("Bot token not available for role checking")
            else:
                app_logger.warning(f"Failed to get guild member info: {guild_member_response.text}")
                # Alternative method: Try using bot token to get member info
                bot_token = os.getenv('DISCORD_TOKEN')
                if bot_token:
                    bot_headers = {'Authorization': f'Bot {bot_token}'}
                    bot_member_response = requests.get(
                        f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/members/{user_data['id']}",
                        headers=bot_headers
                    )
                    app_logger.debug(f"Bot member API response status: {bot_member_response.status_code}")
                    
                    if bot_member_response.status_code == 200:
                        member_data = bot_member_response.json()
                        roles = member_data.get('roles', [])
                        app_logger.debug(f"User roles (via bot): {roles}")
                        
                        # Get guild roles
                        roles_response = requests.get(
                            f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/roles",
                            headers=bot_headers
                        )
                        
                        if roles_response.status_code == 200:
                            guild_roles = roles_response.json()
                            
                            for role_id in roles:
                                for guild_role in guild_roles:
                                    if guild_role['id'] == role_id:
                                        permissions = int(guild_role.get('permissions', 0))
                                        app_logger.debug(f"Role '{guild_role['name']}' (ID: {role_id}) has permissions: {permissions}")
                                        
                                        # Check for Administrator permission (0x8) or Manage Server (0x20)
                                        if permissions & 0x8:
                                            is_admin = True
                                            app_logger.info(f"User has Administrator permission via role: {guild_role['name']}")
                                            break
                                        elif permissions & 0x20:
                                            is_admin = True
                                            app_logger.info(f"User has Manage Server permission via role: {guild_role['name']}")
                                            break
                                if is_admin:
                                    break
                    else:
                        app_logger.warning(f"Failed to get member info via bot: {bot_member_response.text}")
                        
        except Exception as e:
                    app_logger.error(f"Error checking admin status: {e}")
        import traceback
        app_logger.error(traceback.format_exc())
        
        app_logger.info(f"Final admin status for {user_data['username']}: {is_admin}")
        
        # Construct avatar URL
        avatar_url = get_discord_avatar_url(user_data['id'], user_data.get('avatar'))
        
        # Try to get user by primary key (id) first, then by discord_id
        user = User.query.filter_by(id=user_data['id']).first()
        if not user:
            user = User.query.filter_by(discord_id=user_data['id']).first()
        
        if not user:
            try:
                user = User(
                    id=user_data['id'],  # Use Discord ID as primary key
                    username=user_data['username'],
                    discord_id=user_data['id'],
                    avatar_url=avatar_url,
                    is_admin=is_admin,
                    points=0,
                    balance=0
                )
                db.session.add(user)
                db.session.commit()
                app_logger.info(f"Created new user: {user.username} (Admin: {is_admin})")
            except Exception as e:
                # Rollback and try to get user again in case of race condition
                db.session.rollback()
                user = User.query.filter_by(id=user_data['id']).first()
                if not user:
                    user = User.query.filter_by(discord_id=user_data['id']).first()
                if not user:
                    raise e  # Re-raise if we still can't find the user
                app_logger.info(f"Race condition resolved, found existing user: {user.username}")
        
        # Update user information and fix any null balance issues
        user.is_admin = is_admin
        user.username = user_data['username']  # Update username in case it changed
        user.avatar_url = avatar_url
        
        # Fix any None balance or points (for existing users)
        if user.balance is None:
            user.balance = 0
        if user.points is None:
            user.points = 0
        try:
            db.session.commit()
            app_logger.info(f"Updated existing user: {user.username} (Admin: {is_admin})")
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"Error updating user: {e}")
        
        login_user(user)
        if is_admin:
            flash(f"Welcome, Admin {user.username}!")
        else:
            flash(f"Welcome, {user.username}!")
        return redirect(url_for('index'))
        
    except Exception as e:
        app_logger.error(f"Error in callback: {str(e)}")
        import traceback
        app_logger.error(traceback.format_exc())
        flash(f'Authentication error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase(product_id):
    try:
        # Re-fetch current user to get latest balance
        current_user_fresh = User.query.with_for_update().get(current_user.id)
        if not current_user_fresh:
            flash('User not found')
            return redirect(url_for('index'))
        
        # Lock the product row to prevent race conditions
        product = Product.query.with_for_update().get_or_404(product_id)
        
        # Validate balance
        if current_user_fresh.balance < product.price:
            flash('Insufficient balance')
            return redirect(url_for('index'))
        
        # Check stock availability (with race condition protection)
        # None = unlimited, 0 = out of stock, >0 = limited stock
        if product.stock == 0:
            flash('Product is out of stock')
            return redirect(url_for('index'))
        
        # Generate UUID if user doesn't have one
        if not current_user_fresh.user_uuid:
            current_user_fresh.user_uuid = str(uuid.uuid4())
            app_logger.info(f"Generated new UUID for user {current_user_fresh.username}: {current_user_fresh.user_uuid}")
        
        # Atomic balance deduction
        current_user_fresh.balance -= product.price
        
        # Atomic stock reduction (if limited stock)
        if product.stock is not None and product.stock > 0:
            product.stock -= 1
        
        # Create purchase record
        purchase = Purchase(
            user_id=current_user_fresh.id, 
            product_id=product.id, 
            points_spent=product.price
        )
        db.session.add(purchase)
        db.session.flush()  # Get purchase ID for digital delivery
        
        # Handle digital product delivery
        delivery_success = True
        delivery_message = ""
        
        if product.is_digital and product.auto_delivery:
            delivery_success, delivery_message = DigitalDeliveryService.deliver_product(
                current_user_fresh, product, purchase
            )
            
            if delivery_success:
                purchase.status = 'completed'
                purchase.delivery_info = delivery_message
            else:
                purchase.status = 'pending_delivery'
                purchase.delivery_info = f"Delivery failed: {delivery_message}"
        
        # Commit all changes atomically
        db.session.commit()
        
        # Update current_user object for session
        current_user.balance = current_user_fresh.balance
        current_user.user_uuid = current_user_fresh.user_uuid
        
        # Success message based on delivery
        if delivery_success and product.is_digital:
            # For Minecraft skins, auto-redirect to download
            if product.product_type == 'minecraft_skin' and product.delivery_method == 'download':
                # Extract download token from delivery message
                import re
                token_match = re.search(r'/download/([a-f0-9-]+)', delivery_message)
                if token_match:
                    download_token = token_match.group(1)
                    flash(f'Purchase successful! Your download will start automatically.')
                    app_logger.info(f"Auto-downloading Minecraft skin: User {current_user_fresh.username} bought {product.name}")
                    return redirect(url_for('download_file', token=download_token))
            
            flash(f'Purchase successful! {delivery_message}')
        elif product.is_digital and not delivery_success:
            flash(f'Purchase completed but delivery pending: {delivery_message}')
        else:
            flash(f'Purchase successful! Your UUID: {current_user_fresh.user_uuid}')
        
        app_logger.info(f"Purchase completed: User {current_user_fresh.username} bought {product.name} for {product.price} points")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        app_logger.error(f"Purchase failed: {str(e)}")
        flash('Purchase failed. Please try again.')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Show all products in admin panel (active and archived), ordered by status and creation date
    products = Product.query.order_by(Product.is_active.desc(), Product.created_at.desc()).all()
    
    # Fix any None values in products before sending to template
    for product in products:
        if product.stock is None:
            product.stock = -1  # Use -1 to represent unlimited stock
    
    return render_template('admin.html', products=products)

@app.route('/admin/purchases')
@login_required
def admin_purchases():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    # Get all purchases with related user and product data
    purchases = Purchase.query.options(
        db.joinedload(Purchase.user),
        db.joinedload(Purchase.product)
    ).order_by(Purchase.timestamp.desc()).all()
    
    return render_template('admin_purchases.html', purchases=purchases)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get product type first to determine file handling
            product_type = request.form.get('product_type', 'physical')
            
            # Initialize file variables
            image_filename = None
            preview_image_filename = None
            download_file_filename = None
            
            # Handle file uploads based on product type
            if product_type == 'minecraft_skin':
                # Handle dual-file system for Minecraft skins
                
                # Preview image upload
                if 'preview_image' in request.files:
                    file = request.files['preview_image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        preview_image_filename = save_uploaded_file(file, 'preview')
                        if not preview_image_filename:
                            flash('Error uploading preview image.')
                            return render_template('product_form.html', title='Add New Product')
                    elif file and file.filename != '':
                        flash('Invalid preview image type. Please upload PNG, JPG, JPEG, GIF, or WebP images.')
                        return render_template('product_form.html', title='Add New Product')
                
                # Download file upload
                if 'download_file' in request.files:
                    file = request.files['download_file']
                    if file and file.filename != '' and allowed_file(file.filename):
                        download_file_filename = save_uploaded_file(file, 'download')
                        if not download_file_filename:
                            flash('Error uploading download file.')
                            return render_template('product_form.html', title='Add New Product')
                    elif file and file.filename != '':
                        flash('Invalid download file type.')
                        return render_template('product_form.html', title='Add New Product')
                
                # For Minecraft skins, require both files
                if not preview_image_filename or not download_file_filename:
                    flash('Both preview image and download file are required for Minecraft skins.')
                    return render_template('product_form.html', title='Add New Product')
                    
            else:
                # Handle regular image upload for other product types
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        image_filename = save_uploaded_file(file, 'image')
                        if not image_filename:
                            flash('Error uploading image.')
                            return render_template('product_form.html', title='Add New Product')
                    elif file and file.filename != '':
                        flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images.')
                        return render_template('product_form.html', title='Add New Product')
            
            # Validate and sanitize input
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if not name:
                flash('Product name is required')
                return render_template('product_form.html', title='Add New Product')
            
            if len(name) > 100:
                flash('Product name must be 100 characters or less')
                return render_template('product_form.html', title='Add New Product')
            
            try:
                price = int(request.form['price'])
                if price < 0:
                    flash('Price must be a positive number')
                    return render_template('product_form.html', title='Add New Product')
                if price > 999999:
                    flash('Price must be less than 1,000,000')
                    return render_template('product_form.html', title='Add New Product')
            except (ValueError, KeyError):
                flash('Invalid price. Please enter a valid number.')
                return render_template('product_form.html', title='Add New Product')
            
            # Handle stock - empty means unlimited (None), otherwise convert to int
            stock_input = request.form.get('stock', '').strip()
            if stock_input == '':
                stock = None  # Unlimited stock
            else:
                try:
                    stock = int(stock_input)
                    if stock < 0:
                        flash('Stock must be a positive number')
                        return render_template('product_form.html', title='Add New Product')
                    if stock > 999999:
                        flash('Stock must be less than 1,000,000')
                        return render_template('product_form.html', title='Add New Product')
                except ValueError:
                    flash('Invalid stock. Please enter a valid number.')
                    return render_template('product_form.html', title='Add New Product')

            # Get digital product fields (product_type already retrieved above)
            delivery_method = request.form.get('delivery_method', '')
            auto_delivery = 'auto_delivery' in request.form
            category = request.form.get('category', 'general')
            
            # Set default delivery method for Minecraft skins
            if product_type == 'minecraft_skin':
                delivery_method = 'download'
                auto_delivery = True
            
            # Handle delivery data (JSON)
            delivery_data = ""
            if product_type == 'role' and delivery_method == 'auto_role':
                role_id = request.form.get('role_id', '').strip()
                if role_id:
                    delivery_data = json.dumps({"role_id": role_id})
            elif product_type == 'game_code' and delivery_method == 'code_generation':
                code_pattern = request.form.get('code_pattern', 'GAME-{uuid}').strip()
                delivery_data = json.dumps({"code_pattern": code_pattern})
            elif delivery_method == 'download' and product_type != 'minecraft_skin':
                # For non-minecraft products, use legacy file_path system
                file_path = request.form.get('file_path', '').strip()
                if file_path:
                    delivery_data = json.dumps({"file_path": file_path})

            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                image_url=image_filename,  # Store filename instead of URL
                product_type=product_type,
                delivery_method=delivery_method,
                delivery_data=delivery_data,
                auto_delivery=auto_delivery,
                category=category,
                preview_image_url=preview_image_filename,  # For Minecraft skins
                download_file_url=download_file_filename   # For Minecraft skins
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.name}" added successfully!')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error adding product: {str(e)}')
            app_logger.error(f"Error in new_product: {e}")
    
    return render_template('product_form.html', title='Add New Product')

@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Handle image upload
            image_filename = product.image_url  # Keep existing image by default
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Delete old image if it exists
                    if product.image_url:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_url)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                                app_logger.info(f"Deleted old image: {product.image_url}")
                            except Exception as e:
                                app_logger.error(f"Error deleting old image: {e}")
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    image_filename = unique_filename
                    app_logger.info(f"New image uploaded successfully: {image_filename}")
                elif file and file.filename != '':
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images.')
                    return render_template('product_form.html', title='Edit Product', product=product)
            
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = int(request.form['price'])
            
            # Handle stock - empty means unlimited (None), otherwise convert to int
            stock_input = request.form.get('stock', '').strip()
            if stock_input == '':
                product.stock = None  # Unlimited stock
            else:
                product.stock = int(stock_input)
            
            product.image_url = image_filename
        
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}')
            app_logger.error(f"Error in edit_product: {e}")
    
    return render_template('product_form.html', title='Edit Product', product=product)

@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    try:
        # Check if there are any purchases for this product
        purchase_count = Purchase.query.filter_by(product_id=product_id).count()
        
        if purchase_count > 0:
            # Archive the product instead of deleting it to preserve purchase history
            product.is_active = False
            product.archived_at = datetime.now(dt.timezone.utc)
            db.session.commit()
            
            flash(f'Product "{product_name}" has been removed from the store (archived). '
                  f'Purchase history for {purchase_count} purchase(s) has been preserved.')
            app_logger.info(f"Product {product_name} archived by admin {current_user.username} due to existing purchases")
            return redirect(url_for('admin_panel'))
        
        # Check for any role assignments or download tokens associated with this product
        role_assignment_count = db.session.query(RoleAssignment).join(Purchase).filter(Purchase.product_id == product_id).count()
        download_token_count = db.session.query(DownloadToken).join(Purchase).filter(Purchase.product_id == product_id).count()
        
        if role_assignment_count > 0 or download_token_count > 0:
            # Archive the product instead of deleting it to preserve digital delivery integrity
            product.is_active = False
            product.archived_at = datetime.now(dt.timezone.utc)
            db.session.commit()
            
            flash(f'Product "{product_name}" has been removed from the store (archived). '
                  f'Digital delivery records have been preserved.')
            app_logger.info(f"Product {product_name} archived by admin {current_user.username} due to delivery records")
            return redirect(url_for('admin_panel'))
        
        # No purchases or delivery records - safe to actually delete
        # Delete associated image files if they exist
        files_to_delete = []
        if product.image_url:
            files_to_delete.append(product.image_url)
        if hasattr(product, 'preview_image_url') and product.preview_image_url:
            files_to_delete.append(product.preview_image_url)
        if hasattr(product, 'download_file_url') and product.download_file_url:
            files_to_delete.append(product.download_file_url)
        
        for filename in files_to_delete:
            if filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        app_logger.info(f"Deleted file: {filename}")
                    except Exception as e:
                        app_logger.error(f"Error deleting file {filename}: {e}")
        
        # Actually delete the product (no purchase history to preserve)
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product_name}" deleted successfully!')
        app_logger.info(f"Product {product_name} permanently deleted by admin {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}')
        app_logger.error(f"Error in delete_product: {e}")
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/product/<int:product_id>/restore', methods=['POST'])
@login_required
def restore_product(product_id):
    """Restore an archived product back to the store"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    try:
        if product.is_active:
            flash(f'Product "{product_name}" is already active in the store.')
            return redirect(url_for('admin_panel'))
        
        # Restore the product to active status
        product.is_active = True
        product.archived_at = None
        db.session.commit()
        
        flash(f'Product "{product_name}" has been restored to the store!')
        app_logger.info(f"Product {product_name} restored by admin {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring product: {str(e)}')
        app_logger.error(f"Error in restore_product: {e}")
    
    return redirect(url_for('admin_panel'))

# Import bot after models are defined
from bot import run_bot, init_bot_with_app

# Initialize bot with app and models
init_bot_with_app(app, db, User, Achievement, UserAchievement, EconomySettings)

@app.route('/admin/get-discord-roles')
@login_required
def get_discord_roles():
    """Get available Discord roles from the server"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from bot import bot
        
        # Check if bot is ready
        if not bot.is_ready():
            return jsonify({'error': 'Discord bot is not ready yet. Please try again in a moment.'}), 503
        
        # Get the guild (server)
        guild = None
        if os.getenv('DISCORD_GUILD_ID'):
            guild = bot.get_guild(int(os.getenv('DISCORD_GUILD_ID')))
        elif bot.guilds:
            guild = bot.guilds[0]  # Use first guild if no specific guild ID
        
        if not guild:
            return jsonify({'error': 'Bot not connected to any Discord server'}), 400
        
        # Get all roles from the guild, excluding @everyone and bot roles
        roles = []
        bot_member = guild.get_member(bot.user.id)
        bot_highest_role = bot_member.top_role if bot_member else None
        
        for role in guild.roles:
            # Skip @everyone role and bot roles
            if role.name == "@everyone" or role.managed:
                continue
            
            # Skip roles higher than the bot's highest role (bot can't assign them)
            if bot_highest_role and role.position >= bot_highest_role.position:
                continue
            
            # Skip the bot's own role
            if bot_member and role in bot_member.roles:
                continue
                
            roles.append({
                'id': str(role.id),
                'name': role.name,
                'color': str(role.color) if role.color else '#000000',
                'position': role.position,
                'permissions': role.permissions.value,
                'assignable': True
            })
        
        # Sort by position (higher position = higher in hierarchy)
        roles.sort(key=lambda x: x['position'], reverse=True)
        
        return jsonify({'roles': roles})
    
    except Exception as e:
        app_logger.error(f"Error fetching Discord roles: {e}")
        return jsonify({'error': f'Failed to fetch roles: {str(e)}'}), 500

@app.route('/admin/get-role-products')
@login_required
def get_role_products():
    """Get existing role-based products"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all role products
        role_products = Product.query.filter_by(product_type='role').all()
        products = []
        
        for product in role_products:
            # Parse delivery data to get role ID
            role_data = product.delivery_config
            role_id = role_data.get('role_id', 'Unknown')
            
            products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'role_id': role_id,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'auto_delivery': product.auto_delivery
            })
        
        return jsonify({'products': products})
    
    except Exception as e:
        app_logger.error(f"Error fetching role products: {e}")
        return jsonify({'error': f'Failed to fetch role products: {str(e)}'}), 500

@app.route('/admin/get-minecraft-skin-products')
@login_required
def get_minecraft_skin_products():
    """Get existing Minecraft skin products for the digital templates page"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all Minecraft skin products
        skin_products = Product.query.filter_by(product_type='minecraft_skin').all()
        
        products_data = []
        for product in skin_products:
            # Determine if preview is video or image
            preview_type = 'image'
            if product.preview_image_url:
                file_ext = product.preview_image_url.split('.')[-1].lower()
                if file_ext in ['mp4', 'webm', 'ogv', 'mov']:
                    preview_type = 'video'
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'preview_image_url': product.preview_image_url,
                'download_file_url': product.download_file_url,
                'preview_type': preview_type,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M'),
                'has_dual_files': product.has_dual_files
            })
        
        return jsonify({'products': products_data})
        
    except Exception as e:
        app_logger.error(f"Error getting Minecraft skin products: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/digital-templates')
@login_required
def digital_templates():
    """Show pre-made digital product templates"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Enhanced digital product templates
    templates = {
        "roles": [],  # Dynamic roles will be loaded via JavaScript
        "skins": [],  # Dynamic skins will be loaded via JavaScript
        "codes": [
            {
                "name": "🎯 Steam Game Code",
                "description": "Random Steam game worth $10-20 from our curated collection",
                "price": 1200,
                "category": "gaming",
                "product_type": "game_code",
                "delivery_method": "code_generation", 
                "auto_delivery": True,
                "code_pattern": "STEAM-{uuid}"
            },
            {
                "name": "🎁 $5 Amazon Gift Card",
                "description": "Digital Amazon gift card code delivered instantly",
                "price": 600,  
                "category": "gift_cards",
                "product_type": "gift_card",
                "delivery_method": "code_generation",
                "auto_delivery": True,
                "code_pattern": "AMZN-{uuid}"
            },
            {
                "name": "🎮 Discord Nitro Code",
                "description": "1-month Discord Nitro subscription code",
                "price": 800,
                "category": "gaming",
                "product_type": "game_code",
                "delivery_method": "code_generation",
                "auto_delivery": True,
                "code_pattern": "NITRO-{uuid}"
            },
            {
                "name": "🍕 $10 Food Delivery Credit",
                "description": "Credit for popular food delivery services",
                "price": 1000,
                "category": "gift_cards",
                "product_type": "gift_card",
                "delivery_method": "code_generation",
                "auto_delivery": True,
                "code_pattern": "FOOD-{uuid}"
            }
        ],
        "digital_content": [
            {
                "name": "📚 Study Guide Pack",
                "description": "Comprehensive study materials and guides for ASU courses",
                "price": 200,
                "category": "education",
                "product_type": "digital_content",
                "delivery_method": "download",
                "auto_delivery": True,
                "file_path_placeholder": "content/study_guides.zip"
            },
            {
                "name": "🎵 Music Pack",
                "description": "Royalty-free music collection for content creation",
                "price": 300,
                "category": "creative",
                "product_type": "digital_content",
                "delivery_method": "download",
                "auto_delivery": True,
                "file_path_placeholder": "content/music_pack.zip"
            },
            {
                "name": "🖼️ Design Assets Bundle",
                "description": "Graphics, icons, and design elements for projects",
                "price": 250,
                "category": "creative",
                "product_type": "digital_content",
                "delivery_method": "download",
                "auto_delivery": True,
                "file_path_placeholder": "content/design_assets.zip"
            }
        ]
    }
    
    return render_template('digital_templates.html', templates=templates)

@app.route('/admin/economy-config', methods=['GET', 'POST'])
@login_required
def economy_config():
    """Configure economy settings before enabling for the first time"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    settings = EconomySettings.query.first()
    if not settings:
        # Create default settings if they don't exist
        settings = EconomySettings(
            economy_enabled=False,
            first_time_enabled=False,
            roles_configured=False
        )
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            
            # Get form data
            verified_role_id = request.form.get('verified_role_id', '').strip()
            onboarding_role_ids = request.form.getlist('onboarding_role_ids')
            verified_bonus_points = int(request.form.get('verified_bonus_points', 200))
            onboarding_bonus_points = int(request.form.get('onboarding_bonus_points', 500))
            
            # Validate points
            if verified_bonus_points < 0 or verified_bonus_points > 10000:
                flash('Verified bonus points must be between 0 and 10,000')
                return render_template('economy_config.html', settings=settings)
            
            if onboarding_bonus_points < 0 or onboarding_bonus_points > 10000:
                flash('Onboarding bonus points must be between 0 and 10,000')
                return render_template('economy_config.html', settings=settings)
            
            # Update settings
            settings.verified_role_id = verified_role_id if verified_role_id else None
            settings.set_onboarding_roles(onboarding_role_ids)
            settings.verified_bonus_points = verified_bonus_points
            settings.onboarding_bonus_points = onboarding_bonus_points
            settings.roles_configured = True
            
            if action == 'save_config':
                db.session.commit()
                flash('Economy configuration saved successfully!')
                app_logger.info(f"Economy configuration saved by {current_user.username}")
                
            elif action == 'enable_economy':
                # Enable the economy and award first-time bonuses
                settings.economy_enabled = True
                settings.enabled_at = datetime.now(dt.timezone.utc)
                db.session.commit()
                
                # Award first-time bonuses in a separate thread to avoid blocking
                from threading import Thread
                bonus_thread = Thread(target=award_first_time_bonuses, args=(settings,))
                bonus_thread.daemon = True
                bonus_thread.start()
                
                flash('Economy system enabled successfully! First-time bonuses are being awarded to eligible users.')
                app_logger.info(f"Economy system enabled by {current_user.username}")
                return redirect(url_for('admin_panel'))
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving configuration: {str(e)}')
            app_logger.error(f"Error in economy_config: {e}")
    
    return render_template('economy_config.html', settings=settings)

def award_first_time_bonuses(settings):
    """Award first-time bonuses to users with configured roles"""
    try:
        with app.app_context():
            app_logger.info("Starting first-time bonus awards...")
            
            # Import bot to get guild information
            from bot import bot
            
            # Wait for bot to be ready
            import time
            max_wait = 30  # Maximum wait time in seconds
            wait_time = 0
            while not bot.is_ready() and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
            
            if not bot.is_ready():
                app_logger.error("Bot not ready for first-time bonus awards")
                return
            
            # Get the guild
            guild = None
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                guild = bot.get_guild(int(guild_id))
            elif bot.guilds:
                guild = bot.guilds[0]  # Use first guild if no specific guild ID
            
            if not guild:
                app_logger.error("No guild found for first-time bonus awards")
                return
            
            bonus_awarded_count = 0
            
            # Award verified role bonuses
            if settings.verified_role_id:
                verified_role = guild.get_role(int(settings.verified_role_id))
                if verified_role:
                    app_logger.info(f"Awarding verified bonuses for role: {verified_role.name}")
                    
                    for member in verified_role.members:
                        if not member.bot:  # Skip bots
                            user = User.query.filter_by(id=str(member.id)).first()
                            if not user:
                                # Create user if they don't exist
                                user = User(
                                    id=str(member.id),
                                    username=member.display_name,
                                    discord_id=str(member.id),
                                    avatar_url=get_discord_avatar_url(member.id, member.avatar.key if member.avatar else None)
                                )
                                db.session.add(user)
                            
                            if not user.verification_bonus_received:
                                # Ensure balance and points are not None
                                if user.balance is None:
                                    user.balance = 0
                                if user.points is None:
                                    user.points = 0
                                
                                user.balance += settings.verified_bonus_points
                                user.points += settings.verified_bonus_points
                                user.verification_bonus_received = True
                                bonus_awarded_count += 1
                                app_logger.info(f"Awarded {settings.verified_bonus_points} points to {user.username} for verified role")
            
            # Award onboarding role bonuses
            onboarding_role_ids = settings.onboarding_roles_list
            if onboarding_role_ids:
                for role_id in onboarding_role_ids:
                    onboarding_role = guild.get_role(int(role_id))
                    if onboarding_role:
                        app_logger.info(f"Awarding onboarding bonuses for role: {onboarding_role.name}")
                        
                        for member in onboarding_role.members:
                            if not member.bot:  # Skip bots
                                user = User.query.filter_by(id=str(member.id)).first()
                                if not user:
                                    # Create user if they don't exist
                                    user = User(
                                        id=str(member.id),
                                        username=member.display_name,
                                        discord_id=str(member.id),
                                        avatar_url=get_discord_avatar_url(member.id, member.avatar.key if member.avatar else None)
                                    )
                                    db.session.add(user)
                                
                                if not user.onboarding_bonus_received:
                                    # Ensure balance and points are not None
                                    if user.balance is None:
                                        user.balance = 0
                                    if user.points is None:
                                        user.points = 0
                                    
                                    user.balance += settings.onboarding_bonus_points
                                    user.points += settings.onboarding_bonus_points
                                    user.onboarding_bonus_received = True
                                    bonus_awarded_count += 1
                                    app_logger.info(f"Awarded {settings.onboarding_bonus_points} points to {user.username} for onboarding role")
            
            # Commit all changes
            db.session.commit()
            app_logger.info(f"First-time bonus awards completed. Total bonuses awarded: {bonus_awarded_count}")
            
    except Exception as e:
        app_logger.error(f"Error awarding first-time bonuses: {e}")
        # Only rollback if we're still in the app context
        try:
            db.session.rollback()
        except RuntimeError:
            # If we're outside app context, we can't rollback
            pass

@app.route('/admin/create-role-product', methods=['POST'])
@login_required
def create_role_product():
    """Create a role-based digital product"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    try:
        # Get form data
        role_id = request.form.get('role_id', '').strip()
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        stock = request.form.get('stock', '').strip()
        
        # Validate required fields
        if not role_id:
            flash('Please select a Discord role')
            return redirect(url_for('digital_templates'))
        
        if not product_name:
            flash('Product name is required')
            return redirect(url_for('digital_templates'))
        
        if not price:
            flash('Price is required')
            return redirect(url_for('digital_templates'))
        
        try:
            price = int(price)
            if price <= 0:
                flash('Price must be greater than 0')
                return redirect(url_for('digital_templates'))
        except ValueError:
            flash('Invalid price format')
            return redirect(url_for('digital_templates'))
        
        # Handle stock - empty means unlimited (None), otherwise convert to int
        if stock == '':
            stock = None  # Unlimited stock
        else:
            try:
                stock = int(stock)
                if stock < 0:
                    flash('Stock cannot be negative')
                    return redirect(url_for('digital_templates'))
            except ValueError:
                flash('Invalid stock format')
                return redirect(url_for('digital_templates'))
        
        # Check if a product with this role already exists
        existing_product = Product.query.filter(
            Product.product_type == 'role',
            Product.delivery_data.contains(f'"role_id": "{role_id}"')
        ).first()
        
        if existing_product:
            flash(f'A product for this role already exists: {existing_product.name}')
            return redirect(url_for('digital_templates'))
        
        # Handle role image upload
        image_url = None
        if 'role_image' in request.files:
            file = request.files['role_image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    image_url = save_uploaded_file(file, 'image')
                except Exception as e:
                    flash(f'Error uploading image: {str(e)}')
                    return redirect(url_for('digital_templates'))
        
        # Create the delivery data
        delivery_data = json.dumps({"role_id": role_id})
        
        # Create the product
        product = Product(
            name=product_name,
            description=description or f"Gain access to the {product_name} role with special perks and privileges!",
            price=price,
            stock=stock,
            image_url=image_url,
            category="roles",
            product_type="role",
            delivery_method="auto_role",
            delivery_data=delivery_data,
            auto_delivery=True
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Role product "{product_name}" created successfully!')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating role product: {str(e)}')
        app_logger.error(f"Error in create_role_product: {e}")
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create-from-template', methods=['POST'])
@login_required
def create_from_template():
    """Create product from template"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    try:
        # Get template data from form
        template_name = request.form.get('name')
        description = request.form.get('description')
        price = int(request.form.get('price'))
        category = request.form.get('category')
        product_type = request.form.get('product_type')
        delivery_method = request.form.get('delivery_method')
        auto_delivery = request.form.get('auto_delivery') == 'true'
        
        # Get delivery configuration
        delivery_data = ""
        if delivery_method == 'auto_role':
            role_id = request.form.get('role_id', '').strip()
            if not role_id:
                return jsonify({'error': 'Role ID is required for role products'}), 400
            delivery_data = json.dumps({"role_id": role_id})
        elif delivery_method == 'download':
            file_path = request.form.get('file_path', '').strip()
            if not file_path:
                return jsonify({'error': 'File path is required for download products'}), 400
            delivery_data = json.dumps({"file_path": file_path})
        elif delivery_method == 'code_generation':
            code_pattern = request.form.get('code_pattern', 'CODE-{uuid}')
            delivery_data = json.dumps({"code_pattern": code_pattern})
        
        # Create product
        product = Product(
            name=template_name,
            description=description,
            price=price,
            stock=0,  # Digital products typically have unlimited stock
            category=category,
            product_type=product_type,
            delivery_method=delivery_method,
            delivery_data=delivery_data,
            auto_delivery=auto_delivery
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Return JSON response for AJAX requests
        if request.headers.get('Content-Type') == 'application/json' or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'success': True, 'message': f'Digital product "{template_name}" created successfully!'})
        
        flash(f'Digital product "{template_name}" created successfully!')
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error in create_from_template: {e}")
        
        # Return JSON response for AJAX requests
        if request.headers.get('Content-Type') == 'application/json' or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'error': str(e)}), 500
        
        flash(f'Error creating product: {str(e)}')
    
    return redirect(url_for('admin_panel'))

@app.route('/my-purchases')
@login_required
def my_purchases():
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.timestamp.desc()).all()
    return render_template('my_purchases.html', purchases=purchases)

@app.route('/how-to-earn')
def how_to_earn():
    return render_template('how_to_earn.html')

@app.route('/admin/file-manager')
@login_required
def file_manager():
    """File manager for digital assets"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    import os
    upload_path = os.path.join(app.static_folder, 'uploads')
    
    # Ensure upload directory exists
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    # Get all files in uploads directory
    files = []
    for root, dirs, filenames in os.walk(upload_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, upload_path)
            file_size = os.path.getsize(file_path)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            files.append({
                'name': filename,
                'path': relative_path,
                'size': file_size,
                'modified': file_modified,
                'is_image': filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')),
                'is_archive': filename.lower().endswith(('.zip', '.rar', '.7z', '.tar.gz')),
                'is_document': filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.md'))
            })
    
    # Sort files by modification date (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('file_manager.html', files=files)

@app.route('/admin/upload-file', methods=['POST'])
@login_required
def upload_file():
    """Upload a file for digital products"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('file_manager'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('file_manager'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Add timestamp to prevent conflicts
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"
        
        # Create subdirectory based on file type
        file_ext = filename.lower().split('.')[-1]
        if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            subfolder = 'skins'
        elif file_ext in ['zip', 'rar', '7z', 'tar.gz']:
            subfolder = 'content'
        elif file_ext in ['pdf', 'doc', 'docx', 'txt', 'md']:
            subfolder = 'documents'
        else:
            subfolder = 'misc'
        
        upload_path = os.path.join(app.static_folder, 'uploads', subfolder)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        relative_path = os.path.join(subfolder, filename)
        flash(f'File uploaded successfully: {relative_path}')
    else:
        flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WebP, ZIP, RAR, 7Z, PDF, DOC, DOCX, TXT, MD')
    
    return redirect(url_for('file_manager'))

@app.route('/admin/delete-file', methods=['POST'])
@login_required
def delete_file():
    """Delete a file from uploads"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    file_path = request.form.get('file_path')
    if not file_path:
        flash('No file specified')
        return redirect(url_for('file_manager'))
    
    full_path = os.path.join(app.static_folder, 'uploads', file_path)
    
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            flash(f'File deleted: {file_path}')
        else:
            flash('File not found')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}')
    
    return redirect(url_for('file_manager'))

@app.route('/download/<token>')
@login_required
def download_file(token):
    """Secure download route for digital products"""
    try:
        # Find download token
        download_token = DownloadToken.query.filter_by(token=token).first()
        
        if not download_token:
            flash('Invalid download link')
            return redirect(url_for('my_purchases'))
        
        # Check if token has expired
        if datetime.now(dt.timezone.utc) > download_token.expires_at:
            flash('Download link has expired')
            return redirect(url_for('my_purchases'))
        
        # Check if user owns this download
        if download_token.user_id != current_user.id:
            flash('Access denied')
            return redirect(url_for('my_purchases'))
        
        # Build file path
        file_path = os.path.join(app.static_folder, 'uploads', download_token.file_path)
        
        if not os.path.exists(file_path):
            flash('File not found')
            return redirect(url_for('my_purchases'))
        
        # Update download stats
        download_token.downloaded = True
        download_token.download_count += 1
        db.session.commit()
        
        # Get filename for download
        filename = os.path.basename(download_token.file_path)
        
        app_logger.info(f"File downloaded: {filename} by user {current_user.username}")
        
        # Send file for download
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        app_logger.error(f"Download error: {e}")
        flash('Download failed. Please try again.')
        return redirect(url_for('my_purchases'))

@app.route('/admin/leaderboard')
@login_required
def admin_leaderboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    # Get all users with their statistics, ordered by balance (descending)
    users = User.query.order_by(User.balance.desc()).all()
    
    # Calculate additional statistics
    leaderboard_stats = []
    for user in users:
        # Calculate total points spent (sum of all purchases)
        total_spent = db.session.query(db.func.sum(Purchase.points_spent)).filter_by(user_id=user.id).scalar() or 0
        
        # Get number of achievements
        achievement_count = UserAchievement.query.filter_by(user_id=user.id).count()
        
        # Get number of purchases
        purchase_count = Purchase.query.filter_by(user_id=user.id).count()
        
        # Calculate activity score (composite metric)
        activity_score = (
            (user.message_count or 0) * 0.1 +
            (user.reaction_count or 0) * 0.2 +
            (user.voice_minutes or 0) * 0.3 +
            achievement_count * 5 +
            (user.daily_claims_count or 0) * 1
        )
        
        leaderboard_stats.append({
            'user': user,
            'total_spent': total_spent,
            'achievement_count': achievement_count,
            'purchase_count': purchase_count,
            'activity_score': round(activity_score, 1)
        })
    
    # Get top performers in different categories
    top_spenders = sorted(leaderboard_stats, key=lambda x: x['total_spent'], reverse=True)[:10]
    top_achievers = sorted(leaderboard_stats, key=lambda x: x['achievement_count'], reverse=True)[:10]
    most_active = sorted(leaderboard_stats, key=lambda x: x['activity_score'], reverse=True)[:10]
    
    # Calculate overall economy statistics
    total_users = len(users)
    total_balance = sum(user.balance or 0 for user in users)
    total_spent = sum(stat['total_spent'] for stat in leaderboard_stats)
    total_purchases = sum(stat['purchase_count'] for stat in leaderboard_stats)
    total_achievements = sum(stat['achievement_count'] for stat in leaderboard_stats)
    
    economy_stats = {
        'total_users': total_users,
        'total_balance': total_balance,
        'total_spent': total_spent,
        'total_purchases': total_purchases,
        'total_achievements': total_achievements,
        'average_balance': round(total_balance / total_users, 1) if total_users > 0 else 0
    }
    
    return render_template('admin_leaderboard.html', 
                         leaderboard_stats=leaderboard_stats,
                         top_spenders=top_spenders,
                         top_achievers=top_achievers,
                         most_active=most_active,
                         economy_stats=economy_stats)

if __name__ == '__main__':
    import signal
    import sys
    
    # Global variable to track bot thread
    bot_thread = None
    
    def signal_handler(sig, frame):
        """Handle graceful shutdown"""
        app_logger.info("Shutting down gracefully...")
        if bot_thread and bot_thread.is_alive():
            app_logger.info("Waiting for bot thread to finish...")
            bot_thread.join(timeout=5)
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Discord bot in a separate thread (if configured)
        if discord_configured and DISCORD_TOKEN:
            app_logger.info("Starting Discord bot...")
            bot_thread = threading.Thread(target=run_bot, name="DiscordBot")
            bot_thread.daemon = False  # Not daemon to allow graceful shutdown
            bot_thread.start()
        else:
            app_logger.warning("Discord bot not started - missing configuration")
            app_logger.warning("Web interface will be available, but Discord integration disabled")
            bot_thread = None
        
        # Start Flask application
        app_logger.info("Starting Flask web application...")
        app_logger.info("🌐 Web interface available at: http://localhost:6000")
        if discord_configured:
            app_logger.info("🤖 Discord bot is running")
        else:
            app_logger.info("⚠️  Discord bot disabled - configure .env file to enable")
        
        app.run(host='0.0.0.0', port=6000, threaded=True)
        
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        app_logger.error(f"Application error: {e}")
        signal_handler(None, None)  