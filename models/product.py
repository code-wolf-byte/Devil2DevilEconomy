"""
Product model for the economy store.
"""

import json
from datetime import datetime
from .base import db, TimestampMixin


class Product(db.Model, TimestampMixin):
    """Product model for the economy store with digital and physical product support."""
    
    __tablename__ = 'product'
    
    # Basic product information
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    
    # Stock management
    stock = db.Column(db.Integer, nullable=True, default=None)  # None = unlimited, 0 = out of stock, >0 = limited stock
    
    # Media
    image_url = db.Column(db.String(200))
    preview_image_url = db.Column(db.String(200))  # Preview image for minecraft skins
    download_file_url = db.Column(db.String(200))  # Actual downloadable file for minecraft skins
    
    # Product status
    is_active = db.Column(db.Boolean, default=True)  # True = visible in store, False = archived/hidden
    archived_at = db.Column(db.DateTime)  # When the product was archived
    
    # Digital product configuration
    product_type = db.Column(db.String(50), default='physical')  # physical, role, minecraft_skin, game_code, custom
    delivery_method = db.Column(db.String(50))  # auto_role, manual, download, code_generation
    delivery_data = db.Column(db.Text)  # JSON data for delivery (role_id, file_path, etc.)
    auto_delivery = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), default='general')
    
    # Relationships
    purchases = db.relationship('Purchase', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name} ({self.product_type})>'
    
    @property
    def is_digital(self):
        """Check if this is a digital product."""
        return self.product_type != 'physical'
    
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
    
    @property
    def stock_display(self):
        """Get stock display text."""
        if self.stock is None:
            return "Unlimited"
        elif self.stock == 0:
            return "Out of Stock"
        else:
            return str(self.stock)
    
    @property
    def delivery_config(self):
        """Parse delivery_data as JSON."""
        try:
            return json.loads(self.delivery_data) if self.delivery_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @property
    def display_image(self):
        """Get the appropriate image for display."""
        if self.product_type == 'minecraft_skin' and self.preview_image_url:
            return self.preview_image_url
        return self.image_url
    
    @property
    def has_dual_files(self):
        """Check if this product uses dual-file system (minecraft skins)."""
        return (self.product_type == 'minecraft_skin' and 
                self.preview_image_url and 
                self.download_file_url)
    
    def set_delivery_config(self, config_dict):
        """Set delivery configuration from dictionary."""
        self.delivery_data = json.dumps(config_dict) if config_dict else None
    
    def reduce_stock(self, quantity=1):
        """Reduce stock by quantity."""
        if self.stock is None:  # Unlimited stock
            return True
        
        if self.stock < quantity:
            return False
        
        self.stock -= quantity
        return True
    
    def archive(self):
        """Archive the product."""
        self.is_active = False
        self.archived_at = datetime.utcnow()
    
    def restore(self):
        """Restore the product from archive."""
        self.is_active = True
        self.archived_at = None
    
    def to_dict(self):
        """Convert product to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'stock_display': self.stock_display,
            'image_url': self.image_url,
            'display_image': self.display_image,
            'is_active': self.is_active,
            'is_digital': self.is_digital,
            'is_available': self.is_available,
            'product_type': self.product_type,
            'delivery_method': self.delivery_method,
            'delivery_config': self.delivery_config,
            'auto_delivery': self.auto_delivery,
            'category': self.category,
            'has_dual_files': self.has_dual_files,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_active_products(cls):
        """Get all active products."""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_by_category(cls, category):
        """Get products by category."""
        return cls.query.filter_by(category=category, is_active=True).all()
    
    @classmethod
    def get_digital_products(cls):
        """Get all digital products."""
        return cls.query.filter(cls.product_type != 'physical', cls.is_active == True).all() 