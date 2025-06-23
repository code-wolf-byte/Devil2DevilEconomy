"""
Product and purchase-related models
"""

from datetime import datetime
import uuid
import json

from .base import db

class Product(db.Model):
    """Product model for the shop"""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=True, default=None)  # None = unlimited, 0 = out of stock, >0 = limited stock
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # True = visible in store, False = archived/hidden
    archived_at = db.Column(db.DateTime)  # When the product was archived
    
    # Digital product fields
    product_type = db.Column(db.String(50), default='physical')  # physical, role, minecraft_skin, game_code, custom
    delivery_method = db.Column(db.String(50))  # auto_role, manual, download, code_generation
    delivery_data = db.Column(db.Text)  # JSON data for delivery (role_id, file_path, etc.)
    auto_delivery = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='general')
    
    # Minecraft skin specific fields
    preview_image_url = db.Column(db.String(200))  # Preview image for minecraft skins
    download_file_url = db.Column(db.String(200))  # Actual downloadable file for minecraft skins

    def __repr__(self):
        return f'<Product {self.name} ({self.product_type})>'
    
    @property
    def is_digital(self):
        """Check if this is a digital product."""
        return self.product_type != 'physical'
    
    @property
    def delivery_config(self):
        """Parse delivery_data as JSON"""
        try:
            return json.loads(self.delivery_data) if self.delivery_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @property
    def display_image(self):
        """Get the appropriate image for display (preview for minecraft skins, regular image for others)"""
        if self.product_type == 'minecraft_skin' and self.preview_image_url:
            return self.preview_image_url
        return self.image_url
    
    @property
    def has_dual_files(self):
        """Check if this product uses dual-file system (minecraft skins)"""
        return (self.product_type == 'minecraft_skin' and 
                self.preview_image_url and 
                self.download_file_url)
    
    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if self.stock is None:  # Unlimited stock
            return True
        return self.stock > 0
    
    @property
    def is_available(self):
        """Check if product is available for purchase."""
        return self.is_active and self.is_in_stock
    
    def reduce_stock(self, quantity=1):
        """Reduce stock by quantity."""
        if self.stock is None:  # Unlimited stock
            return True
        
        if self.stock < quantity:
            return False
        
        self.stock -= quantity
        return True
    
    @classmethod
    def get_active_products(cls):
        """Get all active products."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_category(cls, category):
        """Get products by category."""
        return cls.query.filter_by(category=category, is_active=True).all()

class Purchase(db.Model):
    """Purchase model for tracking user purchases"""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_info = db.Column(db.Text)  # Store delivery details (codes, download links, etc.)
    status = db.Column(db.String(20), default='completed')  # completed, pending_delivery, failed

    user = db.relationship('User', backref=db.backref('purchases', lazy=True))
    product = db.relationship('Product', backref=db.backref('purchases', lazy=True))

    def __repr__(self):
        return f'<Purchase {self.id}>'
    
    @classmethod
    def get_user_purchases(cls, user_id):
        """Get all purchases for a specific user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_recent_purchases(cls, limit=10):
        """Get recent purchases across all users"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all() 