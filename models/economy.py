"""
Economy-related models for achievements and settings
"""

import json
import uuid
from datetime import datetime, timedelta

from .base import db

class Achievement(db.Model):
    """Achievement model for tracking user milestones"""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    requirement = db.Column(db.Integer, nullable=False)
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f'<Achievement {self.name}>'

class EconomySettings(db.Model):
    """Economy system configuration and settings."""
    
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
        """Get onboarding role IDs as a list."""
        try:
            return json.loads(self.onboarding_role_ids) if self.onboarding_role_ids else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_onboarding_roles(self, role_ids):
        """Set onboarding role IDs from a list."""
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
    original_filename = db.Column(db.String(200))  # Store original filename for download
    downloaded = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship('User', backref='download_tokens')
    purchase = db.relationship('Purchase', backref='download_tokens')
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not expired and under download limit)"""
        return not self.is_expired and self.download_count < 5  # Allow up to 5 downloads
    
    def use_download(self):
        """Use the download token (increment counter)"""
        if not self.is_valid:
            return False
        
        self.download_count += 1
        self.downloaded = True
        return True
    
    @classmethod
    def get_valid_token(cls, token_str):
        """Get a valid download token by token string"""
        token = cls.query.filter_by(token=token_str).first()
        if token and token.is_valid:
            return token
        return None
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired download tokens"""
        expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        count = len(expired_tokens)
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        return count
    
    @classmethod
    def create_token(cls, user_id, purchase_id, file_path, hours=24, original_filename=None):
        """Create a new download token"""
        token = cls(
            token=str(uuid.uuid4()),
            user_id=user_id,
            purchase_id=purchase_id,
            file_path=file_path,
            original_filename=original_filename,
            expires_at=datetime.utcnow() + timedelta(hours=hours)
        )
        return token


 