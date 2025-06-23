"""
Admin routes package - organized by functionality
"""

from flask import Blueprint

# Create main admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def register_admin_routes(app):
    """Register all admin route modules with the Flask app"""
    
    # Import all admin route modules
    from . import dashboard
    from . import products
    from . import users
    from . import logs
    from . import economy
    from . import files
    
    # Register the main admin blueprint and all sub-blueprints with the Flask app
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard.dashboard_bp, url_prefix='/admin')
    app.register_blueprint(products.products_bp, url_prefix='/admin')
    app.register_blueprint(users.users_bp, url_prefix='/admin')
    app.register_blueprint(logs.logs_bp, url_prefix='/admin')
    app.register_blueprint(economy.economy_bp, url_prefix='/admin')
    app.register_blueprint(files.files_bp, url_prefix='/admin') 