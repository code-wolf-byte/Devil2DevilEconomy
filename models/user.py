"""
User model for the economy application.
"""

from flask_login import UserMixin
from datetime import datetime
from .base import db, TimestampMixin


class User(UserMixin, db.Model, TimestampMixin):
    """User model with Discord integration and economy features."""
    
    __tablename__ = 'user'
    
    # Primary identification
    id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    discord_id = db.Column(db.String(20), unique=True)
    avatar_url = db.Column(db.String(500))  # Store Discord avatar URL
    user_uuid = db.Column(db.String(36), unique=True)  # Store unique UUID for each user
    
    # User status and permissions
    is_admin = db.Column(db.Boolean, default=False)
    
    # Economy fields
    points = db.Column(db.Integer, default=0)  # Total points earned
    balance = db.Column(db.Integer, default=0)  # Current spendable balance
    
    # Activity tracking (legacy fields - kept for compatibility)
    messages_sent = db.Column(db.Integer, default=0)
    messages_reacted_to = db.Column(db.Integer, default=0)
    
    # Activity tracking (current fields with limits)
    message_count = db.Column(db.Integer, default=0)
    reaction_count = db.Column(db.Integer, default=0)
    voice_minutes = db.Column(db.Integer, default=0)
    
    # Daily rewards tracking
    last_daily = db.Column(db.DateTime)
    last_daily_engagement = db.Column(db.DateTime)
    
    # Bonus tracking
    has_boosted = db.Column(db.Boolean, default=False)
    enrollment_deposit_received = db.Column(db.Boolean, default=False)
    verification_bonus_received = db.Column(db.Boolean, default=False)
    onboarding_bonus_received = db.Column(db.Boolean, default=False)
    birthday_points_received = db.Column(db.Boolean, default=False)
    
    # Birthday system
    birthday = db.Column(db.Date)  # Store user's birthday (month/day)
    
    # Earning limit tracking
    daily_claims_count = db.Column(db.Integer, default=0)  # Track number of daily claims used
    campus_photos_count = db.Column(db.Integer, default=0)  # Track number of campus photo approvals
    daily_engagement_count = db.Column(db.Integer, default=0)  # Track number of daily engagement approvals
    
    # Relationships
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    role_assignments = db.relationship('RoleAssignment', backref='user', lazy=True)
    download_tokens = db.relationship('DownloadToken', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def display_name(self):
        """Get the display name for the user."""
        return self.username or f"User {self.id}"
    
    @property
    def has_birthday_set(self):
        """Check if user has set their birthday."""
        return self.birthday is not None
    
    def can_claim_daily(self):
        """Check if user can claim daily reward."""
        if not self.last_daily:
            return True
        
        # Check if 24 hours have passed
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.last_daily >= timedelta(hours=24)
    
    def can_claim_daily_engagement(self):
        """Check if user can claim daily engagement reward."""
        if not self.last_daily_engagement:
            return True
        
        # Check if 20 hours have passed
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.last_daily_engagement >= timedelta(hours=20)
    
    def add_points(self, amount: int, description: str = None):
        """Add points to user's account."""
        self.points += amount
        self.balance += amount
        
        # Log the transaction (could be expanded to a proper transaction log)
        import logging
        logging.getLogger('economy.user').info(
            f"User {self.username} gained {amount} points. "
            f"Reason: {description or 'Unknown'}. "
            f"New balance: {self.balance}"
        )
    
    def spend_points(self, amount: int, description: str = None):
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
    
    def to_dict(self):
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'username': self.username,
            'discord_id': self.discord_id,
            'avatar_url': self.avatar_url,
            'is_admin': self.is_admin,
            'points': self.points,
            'balance': self.balance,
            'message_count': self.message_count,
            'reaction_count': self.reaction_count,
            'voice_minutes': self.voice_minutes,
            'has_birthday_set': self.has_birthday_set,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        } 