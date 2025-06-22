"""
Routes package for the Economy application.
Contains all Flask route handlers organized by functionality.
"""

def register_routes(app):
    """Register all route blueprints with the Flask app."""
    
    from .auth import auth_bp
    from .shop import shop_bp
    from .admin import admin_bp
    from .user import user_bp
    from .api import api_bp
    
    # Register all blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    print("✅ All route blueprints registered successfully") 