import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import secrets
import uuid
import json

from flask import Flask, session, request
from flask_login import LoginManager
from flask_migrate import Migrate

# Import models and database
from models import db, User
from config.settings import config_mapping
from config.constants import DISCORD_SCOPES

# Import routes
from routes import register_routes

# Configure logging first
def setup_logging(app):
    """Configure application logging"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # General application log
    app_handler = RotatingFileHandler('logs/economy.log', maxBytes=10240000, backupCount=10)
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app_handler.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    
    # Error log
    error_handler = RotatingFileHandler('logs/error.log', maxBytes=10240000, backupCount=10)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Economy application startup')

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_class = config_mapping.get(config_name, config_mapping['default'])
    app.config.from_object(config_class)
    
    # Set up logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created/verified successfully")
    
    # Set up login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter_by(id=str(user_id)).first()
    
    # Register all routes
    register_routes(app)
    
    # Session and security setup
    @app.before_request
    def before_request():
        # Generate session ID if not exists
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # Session timeout (24 hours)
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=24)
    
    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates"""
        return {
            'DISCORD_CLIENT_ID': app.config.get('DISCORD_CLIENT_ID'),
            'SITE_NAME': app.config.get('SITE_NAME', 'Economy Bot'),
        }
    
    return app

# Create the Flask application
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f'Starting development server on port {port}')
    app.run( port=port, debug=debug)  