"""
Application settings and configuration management.
"""

import os
from dotenv import load_dotenv
from .constants import EnvVars

# Load environment variables
load_dotenv()


class Settings:
    """Centralized application settings."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv(EnvVars.SECRET_KEY, 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv(EnvVars.DATABASE_URL, 'sqlite:///store.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Discord Configuration
    DISCORD_TOKEN = os.getenv(EnvVars.DISCORD_TOKEN)
    DISCORD_CLIENT_ID = os.getenv(EnvVars.DISCORD_CLIENT_ID)
    DISCORD_CLIENT_SECRET = os.getenv(EnvVars.DISCORD_CLIENT_SECRET)
    DISCORD_REDIRECT_URI = os.getenv(EnvVars.DISCORD_REDIRECT_URI, 'http://localhost:6000/callback')
    
    # Guild Configuration
    GUILD_ID = os.getenv(EnvVars.GUILD_ID)
    GENERAL_CHANNEL_ID = os.getenv(EnvVars.GENERAL_CHANNEL_ID)
    VERIFIED_ROLE_ID = os.getenv(EnvVars.VERIFIED_ROLE_ID)
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/economy_app.log')
    
    # Application Configuration
    FLASK_PORT = int(os.getenv('FLASK_PORT', 6000))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    
    @classmethod
    def validate_required_settings(cls):
        """Validate that all required settings are present."""
        required_settings = [
            (cls.DISCORD_TOKEN, 'DISCORD_TOKEN'),
            (cls.DISCORD_CLIENT_ID, 'DISCORD_CLIENT_ID'),
            (cls.DISCORD_CLIENT_SECRET, 'DISCORD_CLIENT_SECRET'),
        ]
        
        missing_settings = []
        for value, name in required_settings:
            if not value or value == f'your_{name.lower()}_here':
                missing_settings.append(name)
        
        return missing_settings
    
    @classmethod
    def is_properly_configured(cls):
        """Check if the application is properly configured."""
        return len(cls.validate_required_settings()) == 0
    
    @classmethod
    def get_discord_oauth_url(cls):
        """Get Discord OAuth authorization URL."""
        if not cls.DISCORD_CLIENT_ID:
            return None
        
        base_url = "https://discord.com/api/oauth2/authorize"
        params = {
            'client_id': cls.DISCORD_CLIENT_ID,
            'redirect_uri': cls.DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify guilds'
        }
        
        from urllib.parse import urlencode
        return f"{base_url}?{urlencode(params)}" 