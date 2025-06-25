from flask import Flask
from discord_files.bot import EconomyBot
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)

# Configure Flask app before initializing extensions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bot = EconomyBot()

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'



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