"""
User-related models
"""

from flask_login import UserMixin
from datetime import datetime

from .base import db

class User(UserMixin, db.Model):
    """User model for authentication and economy tracking"""
    
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

    def __repr__(self):
        return f'<User {self.username}>'

    def spend_points(self, amount, description=None):
        """Spend points from user's balance."""
        if self.balance < amount:
            raise ValueError(f"Insufficient balance. Required: {amount}, Available: {self.balance}")
        
        self.balance -= amount
        
        # Log the transaction
        import logging
        logging.getLogger('economy.user').info(
            f"User {self.username} spent {amount} points. "
            f"Reason: {description or 'Unknown'}. "
            f"New balance: {self.balance}"
        )
    
    def add_points(self, amount, description=None):
        """Add points to user's account."""
        self.points += amount
        self.balance += amount
        
        # Log the transaction
        import logging
        logging.getLogger('economy.user').info(
            f"User {self.username} gained {amount} points. "
            f"Reason: {description or 'Unknown'}. "
            f"New balance: {self.balance}"
        )

class UserAchievement(db.Model):
    """Junction table for users and their achievements"""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>' 