"""
Achievement models for the economy system.
"""

from datetime import datetime
from .base import db, TimestampMixin


class Achievement(db.Model, TimestampMixin):
    """Achievement model for tracking user milestones and rewards."""
    
    __tablename__ = 'achievement'
    
    # Basic achievement information
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    
    # Achievement configuration
    type = db.Column(db.String(50), nullable=False)  # message, reaction, voice, special
    requirement = db.Column(db.Integer, nullable=False)  # Number required to unlock
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    @property
    def unlock_requirement_text(self):
        """Get human-readable requirement text."""
        type_map = {
            'message': 'messages sent',
            'reaction': 'reactions given',  
            'voice': 'minutes in voice chat',
            'special': 'special requirement'
        }
        
        type_text = type_map.get(self.type, self.type)
        return f"{self.requirement} {type_text}"
    
    def check_eligibility(self, user):
        """Check if a user is eligible for this achievement."""
        if self.type == 'message':
            return user.message_count >= self.requirement
        elif self.type == 'reaction':
            return user.reaction_count >= self.requirement
        elif self.type == 'voice':
            return user.voice_minutes >= self.requirement
        # Special achievements are handled separately
        return False
    
    def to_dict(self):
        """Convert achievement to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'points': self.points,
            'type': self.type,
            'requirement': self.requirement,
            'unlock_requirement_text': self.unlock_requirement_text,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_active_achievements(cls):
        """Get all active achievements."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_type(cls, achievement_type):
        """Get achievements by type."""
        return cls.query.filter_by(type=achievement_type, is_active=True).all()


class UserAchievement(db.Model, TimestampMixin):
    """Junction table for user achievements with timestamp tracking."""
    
    __tablename__ = 'user_achievement'
    
    # Primary key and relationships
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    
    # Achievement tracking
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_awarded = db.Column(db.Integer, default=0)  # Track points awarded for this achievement
    
    # Ensure unique constraint on user-achievement combination
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),)

    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>'
    
    def to_dict(self):
        """Convert user achievement to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def has_achievement(cls, user_id, achievement_id):
        """Check if user has a specific achievement."""
        return cls.query.filter_by(
            user_id=user_id, 
            achievement_id=achievement_id
        ).first() is not None
    
    @classmethod
    def get_user_achievements(cls, user_id):
        """Get all achievements for a specific user."""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_achievement_holders(cls, achievement_id):
        """Get all users who have a specific achievement."""
        return cls.query.filter_by(achievement_id=achievement_id).all()
    
    @classmethod
    def get_recent_achievements(cls, limit=10):
        """Get recent achievements across all users."""
        return cls.query.order_by(cls.achieved_at.desc()).limit(limit).all() 