"""
Economy system models for configuration and digital product delivery.
"""

import json
import uuid
from datetime import datetime, timedelta
from .base import db, TimestampMixin


class EconomySettings(db.Model, TimestampMixin):
    """Economy system configuration and settings."""
    
    __tablename__ = 'economy_settings'
    
    # Primary configuration
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


class RoleAssignment(db.Model, TimestampMixin):
    """Queue for Discord role assignments for digital product delivery."""
    
    __tablename__ = 'role_assignment'
    
    # Basic assignment information
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.String(20), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)


class DownloadToken(db.Model, TimestampMixin):
    """Secure download tokens for digital products."""
    
    __tablename__ = 'download_token'
    
    # Token information
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    
    # File information
    file_path = db.Column(db.String(500), nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=False) 