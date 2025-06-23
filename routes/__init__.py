"""
Routes package for the Economy application.
Contains all Flask route handlers organized by functionality.
"""

def register_routes(app):
    """Register all route blueprints with the Flask app."""
    
    from .auth import auth_bp
    from .shop import shop_bp
    from .user import user_bp
    from .api import api_bp
    
    # Import categorized admin routes
    from .admin import register_admin_routes
    
    # Register main blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register categorized admin routes
    register_admin_routes(app)
    
    print("✅ All route blueprints registered successfully") 