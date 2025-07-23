# 🔄 Migration Guide - Step by Step Implementation

This guide walks you through migrating from the current structure to the new maintainable architecture.

## 🚀 Quick Start - Phase 1 Foundation

### Step 1: Create New Branch and Structure
```bash
# Create a new branch for the restructure
git checkout -b restructure/new-architecture

# Create the new directory structure
mkdir -p app/{config,core,models,services,web,discord_bot,shared,tasks}
mkdir -p app/web/{auth,main,admin,api,middleware}
mkdir -p app/discord_bot/{cogs,events,utils}
mkdir -p tests/{unit,integration,fixtures,helpers}
mkdir -p scripts docs docker deploy

# Create __init__.py files
find app tests -type d -exec touch {}/__init__.py \;
```

### Step 2: Setup Modern Python Packaging
```bash
# Replace requirements.txt approach with pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "devil2devil-economy"
version = "2.0.0"
description = "Discord Economy System with Web Interface"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "Flask==2.3.3",
    "Flask-SQLAlchemy==3.0.5",
    "Flask-Login==0.6.3",
    "Flask-Migrate==4.0.5",
    "discord.py==2.3.2",
    "python-dotenv==1.0.0",
    "Werkzeug==2.3.7",
    "SQLAlchemy==2.0.21",
    "alembic==1.12.0",
    "requests==2.31.0",
    "Pillow==10.0.1",
    "cryptography==41.0.7",
    "gunicorn==21.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.0",
    "pytest-flask==1.2.0",
    "pytest-cov==4.1.0",
    "black==23.7.0",
    "flake8==6.0.0",
    "mypy==1.5.0",
]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
EOF
```

### Step 3: Create Configuration System
```python
# app/config/__init__.py
import os
from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    return config.get(os.environ.get('FLASK_ENV', 'default'))
```

```python
# app/config/base.py
import os
from pathlib import Path

class Config:
    """Base configuration."""
    
    # App Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    # Discord
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
    DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI')
    
    # File Upload
    UPLOAD_FOLDER = Path('static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip'}
    
    # Economy Settings
    DAILY_POINTS = int(os.environ.get('DAILY_POINTS', 85))
    BIRTHDAY_POINTS = int(os.environ.get('BIRTHDAY_POINTS', 50))
    
    @staticmethod
    def init_app(app):
        """Initialize app with this config."""
        # Ensure upload directory exists
        Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_required_vars(cls):
        """Validate required environment variables."""
        required = ['DISCORD_TOKEN', 'DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET']
        missing = [var for var in required if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
```

## 📊 Step 4: Extract Models from shared.py

```python
# app/models/base.py
from app.core.database import db
from datetime import datetime

class BaseModel(db.Model):
    """Base model class with common fields."""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save model to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete model from database."""
        db.session.delete(self)
        db.session.commit()
```

```python
# app/models/user.py
from flask_login import UserMixin
from app.models.base import BaseModel
from app.core.database import db

class User(UserMixin, BaseModel):
    __tablename__ = 'users'
    
    id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    discord_id = db.Column(db.String(20), unique=True)
    avatar_url = db.Column(db.String(500))
    user_uuid = db.Column(db.String(36), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Economy fields
    points = db.Column(db.Integer, default=0)
    balance = db.Column(db.Integer, default=0)
    
    # Activity tracking
    message_count = db.Column(db.Integer, default=0)
    reaction_count = db.Column(db.Integer, default=0)
    voice_minutes = db.Column(db.Integer, default=0)
    
    # Special events
    last_daily = db.Column(db.DateTime)
    birthday = db.Column(db.Date)
    birthday_points_received = db.Column(db.Boolean, default=False)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def has_sufficient_balance(self, amount):
        return self.balance >= amount
    
    def spend_points(self, amount):
        if not self.has_sufficient_balance(amount):
            raise ValueError("Insufficient balance")
        self.balance -= amount
        return self
```

## 🔧 Step 5: Create Service Layer

```python
# app/services/base.py
from abc import ABC, abstractmethod
from app.core.database import db

class BaseService(ABC):
    """Base service class."""
    
    def __init__(self, db_session=None):
        self.db = db_session or db.session
    
    def commit(self):
        """Commit database transaction."""
        self.db.commit()
    
    def rollback(self):
        """Rollback database transaction."""
        self.db.rollback()
```

```python
# app/services/purchase_service.py
from typing import Tuple, Optional
from app.services.base import BaseService
from app.models.user import User
from app.models.product import Product
from app.models.purchase import Purchase
from app.core.exceptions import InsufficientBalanceError, ProductNotFoundError

class PurchaseService(BaseService):
    """Service for handling purchases."""
    
    def process_purchase(self, user_id: str, product_id: int) -> Tuple[bool, str, Optional[Purchase]]:
        """Process a product purchase."""
        try:
            user = User.query.get(user_id)
            product = Product.query.get(product_id)
            
            if not product or not product.is_active:
                return False, "Product not found or inactive", None
            
            if not user.has_sufficient_balance(product.price):
                return False, "Insufficient balance", None
            
            if product.stock is not None and product.stock <= 0:
                return False, "Product out of stock", None
            
            # Create purchase
            purchase = Purchase(
                user_id=user_id,
                product_id=product_id,
                points_spent=product.price,
                status='pending'
            )
            
            # Update user balance
            user.spend_points(product.price)
            
            # Update product stock
            if product.stock is not None:
                product.stock -= 1
            
            # Save all changes
            purchase.save()
            user.save()
            product.save()
            
            # Handle digital delivery
            if product.is_digital:
                self._handle_digital_delivery(purchase)
            
            return True, "Purchase successful", purchase
            
        except Exception as e:
            self.rollback()
            return False, str(e), None
    
    def _handle_digital_delivery(self, purchase: Purchase):
        """Handle digital product delivery."""
        product = purchase.product
        
        if product.product_type == 'role':
            self._assign_discord_role(purchase)
        elif product.product_type == 'minecraft_skin':
            self._create_download_token(purchase)
        # Add more delivery types as needed
    
    def _assign_discord_role(self, purchase: Purchase):
        """Assign Discord role (async task)."""
        from app.tasks.discord import assign_role_task
        assign_role_task.delay(purchase.id)
    
    def _create_download_token(self, purchase: Purchase):
        """Create download token for file downloads."""
        from app.services.file_service import FileService
        file_service = FileService()
        file_service.create_download_token(purchase)
```

## 🌐 Step 6: Refactor Web Application

```python
# app/web/app.py
from flask import Flask
from app.config import get_config
from app.core.extensions import init_extensions
from app.web.main import bp as main_bp
from app.web.auth import bp as auth_bp
from app.web.admin import bp as admin_bp

def create_app(config_name=None):
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
```

```python
# app/web/main/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.purchase_service import PurchaseService
from app.services.product_service import ProductService

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page."""
    product_service = ProductService()
    products = product_service.get_active_products()
    return render_template('main/index.html', products=products)

@bp.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase_product(product_id):
    """Purchase a product."""
    purchase_service = PurchaseService()
    success, message, purchase = purchase_service.process_purchase(
        current_user.id, product_id
    )
    
    if success:
        flash(f'Successfully purchased {purchase.product.name}!', 'success')
    else:
        flash(f'Purchase failed: {message}', 'error')
    
    return redirect(url_for('main.shop'))
```

## 🤖 Step 7: Restructure Discord Bot

```python
# app/discord_bot/bot.py
import discord
from discord.ext import commands
from app.config import get_config

class EconomyBot(commands.Bot):
    def __init__(self):
        config = get_config()
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = config
    
    async def setup_hook(self):
        """Setup bot and load cogs."""
        await self.load_extension('app.discord_bot.cogs.economy')
        await self.load_extension('app.discord_bot.cogs.admin')
        await self.load_extension('app.discord_bot.cogs.user')
        
        # Sync commands
        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} commands")
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
```

```python
# app/discord_bot/cogs/economy.py
import discord
from discord.ext import commands
from discord import app_commands
from app.services.user_service import UserService
from app.services.economy_service import EconomyService

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_service = UserService()
        self.economy_service = EconomyService()
    
    @app_commands.command(name="balance", description="Check your balance")
    async def balance(self, interaction: discord.Interaction):
        """Check user balance."""
        user = self.user_service.get_or_create_user(str(interaction.user.id))
        
        embed = discord.Embed(
            title="💰 Your Balance",
            description=f"You have **{user.balance:,}** pitchforks!",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily reward."""
        success, message, points = self.economy_service.claim_daily_reward(
            str(interaction.user.id)
        )
        
        if success:
            embed = discord.Embed(
                title="🎁 Daily Reward Claimed!",
                description=f"You received **{points}** pitchforks!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Daily Reward",
                description=message,
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
```

## 🧪 Step 8: Create Testing Framework

```python
# tests/conftest.py
import pytest
from app.web.app import create_app
from app.core.database import db as _db
from app.models.user import User
from app.models.product import Product

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def db(app):
    """Create database for testing."""
    with app.app_context():
        yield _db
        _db.session.rollback()

@pytest.fixture
def user(db):
    """Create test user."""
    user = User(
        id='123456789',
        username='testuser',
        discord_id='123456789',
        balance=1000
    )
    user.save()
    return user

@pytest.fixture
def product(db):
    """Create test product."""
    product = Product(
        name='Test Product',
        description='A test product',
        price=100,
        is_active=True
    )
    product.save()
    return product
```

## 🚀 Step 9: Update Deployment

```dockerfile
# docker/Dockerfile.web
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml ./
RUN pip install build && python -m build

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY --from=builder /app/dist/*.whl ./
RUN pip install *.whl

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app.web.app:create_app()"]
```

## 📋 Migration Commands

Run these commands to complete the migration:

```bash
# 1. Setup new environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .[dev]

# 2. Run tests
pytest tests/

# 3. Format code
black app/ tests/

# 4. Type checking
mypy app/

# 5. Run application locally
export FLASK_ENV=development
python -m app.web.app

# 6. Build and run with Docker
docker build -f docker/Dockerfile.web -t devil2devil-economy:latest .
docker run -p 5000:5000 devil2devil-economy:latest
```

## ✅ Validation Checklist

After migration, verify:

- [ ] All tests pass
- [ ] Application starts without errors
- [ ] Discord bot connects successfully
- [ ] Web interface loads correctly
- [ ] Database migrations work
- [ ] File uploads function
- [ ] Purchase flow works end-to-end
- [ ] Docker build succeeds
- [ ] Health checks respond correctly

This migration transforms your monolithic codebase into a maintainable, testable, and scalable application following modern Python best practices! 