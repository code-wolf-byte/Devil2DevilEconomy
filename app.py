from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import requests
import threading
import os
import uuid
import json
import asyncio
from contextlib import contextmanager
from flask_migrate import Migrate

from dotenv import load_dotenv

# Load environment variables with explicit path
load_dotenv()

# Initialize Flask app and extensions
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@contextmanager
def db_transaction():
    """Database transaction context manager with proper error handling."""
    try:
        db.session.begin()
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database transaction rolled back: {e}")
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
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Discord configuration with fallbacks and debugging
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = 'http://localhost:5000/callback'
DISCORD_OAUTH_SCOPE = 'identify guilds guilds.members.read'
DISCORD_API_BASE_URL = 'https://discord.com/api'

# Check for required environment variables
if not DISCORD_CLIENT_ID:
    print("ERROR: DISCORD_CLIENT_ID not found in environment variables")
    exit(1)
if not DISCORD_CLIENT_SECRET:
    print("ERROR: DISCORD_CLIENT_SECRET not found in environment variables")
    exit(1)

# Get Discord Token for bot functionality
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    print("ERROR: DISCORD_TOKEN not found in environment variables")
    exit(1)

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
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Digital product fields
    product_type = db.Column(db.String(50), default='physical')  # physical, role, minecraft_skin, game_code, custom
    delivery_method = db.Column(db.String(50))  # auto_role, manual, download, code_generation
    delivery_data = db.Column(db.Text)  # JSON data for delivery (role_id, file_path, etc.)
    auto_delivery = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='general')
    
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
    
    def __repr__(self):
        return f'<EconomySettings enabled={self.economy_enabled}>'

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

# Initialize database
with app.app_context():
    db.create_all()
    print("Database tables created successfully")
    
    # Initialize achievements
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
        }
        # Add more achievements as needed
    ]

    for achievement_data in achievements:
        achievement = Achievement.query.filter_by(name=achievement_data['name']).first()
        if not achievement:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    
    db.session.commit()
    print("Achievements initialized successfully")

# Initialize login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(str(user_id))

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
            print(f"Digital delivery error: {e}")
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
            expires_at=datetime.utcnow() + timedelta(hours=24)
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
    products = Product.query.all()
    
    # Get current user's purchases if they're logged in
    user_purchases = []
    if current_user.is_authenticated:
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
        
        print(f"Requesting token with data: {data}")
        response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=data, headers=headers)
        print(f"Token response status: {response.status_code}")
        print(f"Token response: {response.text}")
        
        if response.status_code != 200:
            flash('Failed to get access token')
            return redirect(url_for('index'))
        
        access_token = response.json()['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers)
        print(f"User response status: {user_response.status_code}")
        print(f"User response: {user_response.text}")
        
        if user_response.status_code != 200:
            flash('Failed to get user info')
            return redirect(url_for('index'))
        
        user_data = user_response.json()
        print(f"User data: {user_data}")
        
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
        print(f"Checking admin status for user: {user_data['username']} (ID: {user_data['id']})")
        
        try:
            # First, try to get guild member info using user token
            guild_member_response = requests.get(
                f"{DISCORD_API_BASE_URL}/users/@me/guilds/{guild_id}/member",
                headers=headers
            )
            print(f"Guild member API response status: {guild_member_response.status_code}")
            print(f"Guild member API response: {guild_member_response.text}")
            
            if guild_member_response.status_code == 200:
                member_data = guild_member_response.json()
                roles = member_data.get('roles', [])
                print(f"User roles: {roles}")
                
                # Get guild roles to check for admin permissions
                bot_token = os.getenv('DISCORD_TOKEN')
                if bot_token:
                    bot_headers = {'Authorization': f'Bot {bot_token}'}
                    roles_response = requests.get(
                        f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/roles",
                        headers=bot_headers
                    )
                    print(f"Guild roles API response status: {roles_response.status_code}")
                    
                    if roles_response.status_code == 200:
                        guild_roles = roles_response.json()
                        print(f"Found {len(guild_roles)} guild roles")
                        
                        for role_id in roles:
                            for guild_role in guild_roles:
                                if guild_role['id'] == role_id:
                                    permissions = int(guild_role.get('permissions', 0))
                                    print(f"Role '{guild_role['name']}' (ID: {role_id}) has permissions: {permissions}")
                                    
                                    # Check for Administrator permission (0x8) or Manage Server (0x20)
                                    if permissions & 0x8:
                                        is_admin = True
                                        print(f"User has Administrator permission via role: {guild_role['name']}")
                                        break
                                    elif permissions & 0x20:
                                        is_admin = True
                                        print(f"User has Manage Server permission via role: {guild_role['name']}")
                                        break
                            if is_admin:
                                break
                    else:
                        print(f"Failed to get guild roles: {roles_response.text}")
                else:
                    print("Bot token not available for role checking")
            else:
                print(f"Failed to get guild member info: {guild_member_response.text}")
                # Alternative method: Try using bot token to get member info
                bot_token = os.getenv('DISCORD_TOKEN')
                if bot_token:
                    bot_headers = {'Authorization': f'Bot {bot_token}'}
                    bot_member_response = requests.get(
                        f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/members/{user_data['id']}",
                        headers=bot_headers
                    )
                    print(f"Bot member API response status: {bot_member_response.status_code}")
                    
                    if bot_member_response.status_code == 200:
                        member_data = bot_member_response.json()
                        roles = member_data.get('roles', [])
                        print(f"User roles (via bot): {roles}")
                        
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
                                        print(f"Role '{guild_role['name']}' (ID: {role_id}) has permissions: {permissions}")
                                        
                                        # Check for Administrator permission (0x8) or Manage Server (0x20)
                                        if permissions & 0x8:
                                            is_admin = True
                                            print(f"User has Administrator permission via role: {guild_role['name']}")
                                            break
                                        elif permissions & 0x20:
                                            is_admin = True
                                            print(f"User has Manage Server permission via role: {guild_role['name']}")
                                            break
                                if is_admin:
                                    break
                    else:
                        print(f"Failed to get member info via bot: {bot_member_response.text}")
                        
        except Exception as e:
            print(f"Error checking admin status: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Final admin status for {user_data['username']}: {is_admin}")
        
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
                print(f"Created new user: {user.username} (Admin: {is_admin})")
            except Exception as e:
                # Rollback and try to get user again in case of race condition
                db.session.rollback()
                user = User.query.filter_by(id=user_data['id']).first()
                if not user:
                    user = User.query.filter_by(discord_id=user_data['id']).first()
                if not user:
                    raise e  # Re-raise if we still can't find the user
                print(f"Race condition resolved, found existing user: {user.username}")
        
        # Update user information
        user.is_admin = is_admin
        user.username = user_data['username']  # Update username in case it changed
        user.avatar_url = avatar_url
        try:
            db.session.commit()
            print(f"Updated existing user: {user.username} (Admin: {is_admin})")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating user: {e}")
        
        login_user(user)
        if is_admin:
            flash(f"Welcome, Admin {user.username}!")
        else:
            flash(f"Welcome, {user.username}!")
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        import traceback
        traceback.print_exc()
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
        if product.stock != 0 and product.stock < 1:
            flash('Product is out of stock')
            return redirect(url_for('index'))
        
        # Generate UUID if user doesn't have one
        if not current_user_fresh.user_uuid:
            current_user_fresh.user_uuid = str(uuid.uuid4())
            print(f"Generated new UUID for user {current_user_fresh.username}: {current_user_fresh.user_uuid}")
        
        # Atomic balance deduction
        current_user_fresh.balance -= product.price
        
        # Atomic stock reduction (if limited stock)
        if product.stock > 0:
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
            flash(f'Purchase successful! {delivery_message}')
        elif product.is_digital and not delivery_success:
            flash(f'Purchase completed but delivery pending: {delivery_message}')
        else:
            flash(f'Purchase successful! Your UUID: {current_user_fresh.user_uuid}')
        
        print(f"Purchase completed: User {current_user_fresh.username} bought {product.name} for {product.price} points")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        # Rollback transaction on any error
        db.session.rollback()
        print(f"Purchase failed: {str(e)}")
        flash('Purchase failed. Please try again.')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/admin/purchases')
@login_required
def admin_purchases():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of purchases per page
    
    # Get purchases with user and product information, ordered by most recent first
    purchases_pagination = db.session.query(Purchase)\
        .join(User, Purchase.user_id == User.id)\
        .join(Product, Purchase.product_id == Product.id)\
        .order_by(Purchase.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    purchases = purchases_pagination.items
    
    return render_template('admin_purchases.html', 
                         purchases=purchases,
                         pagination=purchases_pagination)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Generate secure filename (prevent any directory traversal)
                    original_filename = secure_filename(file.filename)
                    # Remove any remaining path separators and dots
                    safe_filename = original_filename.replace('..', '').replace('/', '').replace('\\', '')
                    if not safe_filename:
                        safe_filename = 'upload'
                    
                    # Generate completely new filename with safe extension
                    file_ext = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else 'jpg'
                    if file_ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                        file_ext = 'jpg'
                    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
                    
                    # Ensure upload directory exists and is secure
                    upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Create full file path and verify it's within upload directory
                    file_path = os.path.abspath(os.path.join(upload_dir, unique_filename))
                    if not file_path.startswith(upload_dir):
                        flash('Invalid file path detected')
                        return render_template('product_form.html', title='Add New Product')
                    
                    # Validate file size and type
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    file.seek(0)  # Reset to beginning
                    
                    if file_size > app.config['MAX_CONTENT_LENGTH']:
                        flash('File too large. Maximum size is 16MB.')
                        return render_template('product_form.html', title='Add New Product')
                    
                    # Save file
                    file.save(file_path)
                    image_filename = unique_filename
                    print(f"Image uploaded successfully: {image_filename}")
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
            
            try:
                stock = int(request.form.get('stock', 0))
                if stock < 0:
                    flash('Stock must be a positive number or 0 for unlimited')
                    return render_template('product_form.html', title='Add New Product')
                if stock > 999999:
                    flash('Stock must be less than 1,000,000')
                    return render_template('product_form.html', title='Add New Product')
            except ValueError:
                flash('Invalid stock. Please enter a valid number.')
                return render_template('product_form.html', title='Add New Product')

            # Get digital product fields
            product_type = request.form.get('product_type', 'physical')
            delivery_method = request.form.get('delivery_method', '')
            auto_delivery = 'auto_delivery' in request.form
            category = request.form.get('category', 'general')
            
            # Handle delivery data (JSON)
            delivery_data = ""
            if product_type == 'role' and delivery_method == 'auto_role':
                role_id = request.form.get('role_id', '').strip()
                if role_id:
                    delivery_data = json.dumps({"role_id": role_id})
            elif product_type == 'game_code' and delivery_method == 'code_generation':
                code_pattern = request.form.get('code_pattern', 'GAME-{uuid}').strip()
                delivery_data = json.dumps({"code_pattern": code_pattern})
            elif delivery_method == 'download':
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
                category=category
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.name}" added successfully!')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error adding product: {str(e)}')
            print(f"Error in new_product: {e}")
    
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
                                print(f"Deleted old image: {product.image_url}")
                            except Exception as e:
                                print(f"Error deleting old image: {e}")
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    image_filename = unique_filename
                    print(f"New image uploaded successfully: {image_filename}")
                elif file and file.filename != '':
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images.')
                    return render_template('product_form.html', title='Edit Product', product=product)
            
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = int(request.form['price'])
            product.stock = int(request.form.get('stock', 0))
            product.image_url = image_filename
        
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!')
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}')
            print(f"Error in edit_product: {e}")
    
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
        # Delete associated image file if it exists
        if product.image_url:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_url)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"Deleted image file: {product.image_url}")
                except Exception as e:
                    print(f"Error deleting image file: {e}")
        
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product_name}" deleted successfully!')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}')
        print(f"Error in delete_product: {e}")
    
    return redirect(url_for('admin_panel'))

# Import bot after models are defined
from bot import run_bot, init_bot_with_app

# Initialize bot with app and models
init_bot_with_app(app, db, User, Achievement, UserAchievement, EconomySettings)

@app.route('/admin/digital-templates')
@login_required
def digital_templates():
    """Show pre-made digital product templates"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    # Digital product templates
    templates = {
        "roles": [
            {
                "name": "💎 VIP Role",
                "description": "Exclusive VIP status with special perms and color",
                "price": 500,
                "category": "roles",
                "product_type": "role",
                "delivery_method": "auto_role",
                "auto_delivery": True,
                "role_id_placeholder": "ROLE_ID_HERE"
            },
            {
                "name": "🎨 Color Master",
                "description": "Custom name color and hoisted role",
                "price": 300,
                "category": "roles", 
                "product_type": "role",
                "delivery_method": "auto_role",
                "auto_delivery": True,
                "role_id_placeholder": "ROLE_ID_HERE"
            },
            {
                "name": "⭐ Server Booster Plus",
                "description": "Enhanced booster perks and recognition",
                "price": 750,
                "category": "roles",
                "product_type": "role", 
                "delivery_method": "auto_role",
                "auto_delivery": True,
                "role_id_placeholder": "ROLE_ID_HERE"
            }
        ],
        "skins": [
            {
                "name": "🎮 Premium Minecraft Skin Pack",
                "description": "5 exclusive custom skins designed by our artists",
                "price": 200,
                "category": "minecraft",
                "product_type": "minecraft_skin",
                "delivery_method": "download",
                "auto_delivery": True,
                "file_path_placeholder": "skins/premium_pack.zip"
            },
            {
                "name": "🗡️ Medieval Knight Skin",
                "description": "Epic knight skin with armor details", 
                "price": 100,
                "category": "minecraft",
                "product_type": "minecraft_skin",
                "delivery_method": "download",
                "auto_delivery": True,
                "file_path_placeholder": "skins/knight.png"
            }
        ],
        "codes": [
            {
                "name": "🎯 Steam Game Code",
                "description": "Random steam game worth $10-20",
                "price": 1000,
                "category": "gaming",
                "product_type": "game_code",
                "delivery_method": "code_generation", 
                "auto_delivery": True,
                "code_pattern": "STEAM-{uuid}"
            },
            {
                "name": "🎁 Gift Card Code",
                "description": "$5 Amazon gift card",
                "price": 500,  
                "category": "gift_cards",
                "product_type": "gift_card",
                "delivery_method": "code_generation",
                "auto_delivery": True,
                "code_pattern": "GIFT-{uuid}"
            }
        ]
    }
    
    return render_template('digital_templates.html', templates=templates)

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
        auto_delivery = 'auto_delivery' in request.form
        
        # Get delivery configuration
        delivery_data = ""
        if delivery_method == 'auto_role':
            role_id = request.form.get('role_id', '').strip()
            if not role_id:
                flash('Role ID is required for role products')
                return redirect(url_for('digital_templates'))
            delivery_data = json.dumps({"role_id": role_id})
        elif delivery_method == 'download':
            file_path = request.form.get('file_path', '').strip()
            if not file_path:
                flash('File path is required for download products')
                return redirect(url_for('digital_templates'))
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
        
        flash(f'Digital product "{template_name}" created successfully!')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating product: {str(e)}')
        print(f"Error in create_from_template: {e}")
    
    return redirect(url_for('admin_panel'))

@app.route('/my-purchases')
@login_required
def my_purchases():
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.timestamp.desc()).all()
    return render_template('my_purchases.html', purchases=purchases)

if __name__ == '__main__':
    import signal
    import sys
    
    # Global variable to track bot thread
    bot_thread = None
    
    def signal_handler(sig, frame):
        """Handle graceful shutdown"""
        print("\nShutting down gracefully...")
        if bot_thread and bot_thread.is_alive():
            print("Waiting for bot thread to finish...")
            bot_thread.join(timeout=5)
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Discord bot in a separate thread
        bot_thread = threading.Thread(target=run_bot, name="DiscordBot")
        bot_thread.daemon = False  # Not daemon to allow graceful shutdown
        bot_thread.start()
        
        # Start Flask application
        print("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000, threaded=True)
        
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"Application error: {e}")
        signal_handler(None, None) 