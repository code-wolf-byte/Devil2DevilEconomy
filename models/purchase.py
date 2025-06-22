"""
Purchase model for tracking user transactions.
"""

from datetime import datetime
from .base import db, TimestampMixin


class Purchase(db.Model, TimestampMixin):
    """Purchase model to track user transactions and product purchases."""
    
    __tablename__ = 'purchase'
    
    # Basic purchase information
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Delivery tracking
    delivery_info = db.Column(db.Text)  # Store delivery details (codes, download links, etc.)
    status = db.Column(db.String(20), default='completed')  # completed, pending_delivery, failed
    
    # Relationships are defined via backref in User and Product models
    # user = db.relationship('User', backref=db.backref('purchases', lazy=True))
    # product = db.relationship('Product', backref=db.backref('purchases', lazy=True))

    def __repr__(self):
        return f'<Purchase {self.id} - {self.user_id} bought {self.product_id}>'
    
    @property
    def is_completed(self):
        """Check if purchase is completed."""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if purchase is pending delivery."""
        return self.status == 'pending_delivery'
    
    @property
    def is_failed(self):
        """Check if purchase failed."""
        return self.status == 'failed'
    
    @property
    def delivery_details(self):
        """Get delivery information as text."""
        if not self.delivery_info:
            return "No delivery information available"
        return self.delivery_info
    
    def mark_completed(self, delivery_info=None):
        """Mark purchase as completed."""
        self.status = 'completed'
        if delivery_info:
            self.delivery_info = delivery_info
    
    def mark_pending(self, reason=None):
        """Mark purchase as pending delivery."""
        self.status = 'pending_delivery'
        if reason:
            self.delivery_info = f"Pending: {reason}"
    
    def mark_failed(self, error_message=None):
        """Mark purchase as failed."""
        self.status = 'failed'
        if error_message:
            self.delivery_info = f"Failed: {error_message}"
    
    def set_delivery_info(self, info):
        """Set delivery information."""
        self.delivery_info = info
    
    def to_dict(self):
        """Convert purchase to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'points_spent': self.points_spent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'delivery_info': self.delivery_info,
            'status': self.status,
            'is_completed': self.is_completed,
            'is_pending': self.is_pending,
            'is_failed': self.is_failed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_user_purchases(cls, user_id):
        """Get all purchases for a specific user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_product_purchases(cls, product_id):
        """Get all purchases for a specific product."""
        return cls.query.filter_by(product_id=product_id).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_recent_purchases(cls, limit=10):
        """Get recent purchases across all users."""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_pending_purchases(cls):
        """Get all purchases pending delivery."""
        return cls.query.filter_by(status='pending_delivery').all()
    
    @classmethod
    def get_failed_purchases(cls):
        """Get all failed purchases."""
        return cls.query.filter_by(status='failed').all() 