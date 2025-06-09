from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import requests
import threading
import os
import uuid
from dotenv import load_dotenv

# Load environment variables with explicit path
load_dotenv()

# Initialize Flask app and extensions
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Discord configuration with fallbacks and debugging
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')
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

    def __repr__(self):
        return f'<Product {self.name}>'

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
    return User.query.get(int(user_id))

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

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
        
        user = User.query.filter_by(discord_id=user_data['id']).first()
        if not user:
            user = User(
                id=user_data['id'],  # Use Discord ID as primary key
                username=user_data['username'],
                discord_id=user_data['id'],
                is_admin=is_admin,
                points=0,
                balance=0
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created new user: {user.username} (Admin: {is_admin})")
        else:
            # Update admin status in case it changed
            user.is_admin = is_admin
            user.username = user_data['username']  # Update username in case it changed
            db.session.commit()
            print(f"Updated existing user: {user.username} (Admin: {is_admin})")
        
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
    product = Product.query.get_or_404(product_id)
    if current_user.balance < product.price:
        flash('Insufficient balance')
        return redirect(url_for('index'))
    
    current_user.balance -= product.price
    purchase = Purchase(user_id=current_user.id, product_id=product.id)
    db.session.add(purchase)
    db.session.commit()
    
    flash('Purchase successful!')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin.html', products=products)

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
                    # Generate unique filename
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    image_filename = unique_filename
                    print(f"Image uploaded successfully: {image_filename}")
                elif file and file.filename != '':
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images.')
                    return render_template('product_form.html', title='Add New Product')
            
            product = Product(
                name=request.form['name'],
                description=request.form['description'],
                price=int(request.form['price']),
                stock=int(request.form.get('stock', 0)),
                image_url=image_filename  # Store filename instead of URL
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
init_bot_with_app(app, db, User, Achievement, UserAchievement)

if __name__ == '__main__':
    # Start Discord bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask application
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000) 