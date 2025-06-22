"""
Admin routes for product management and system configuration.
Note: This is a simplified version. Full admin routes will be added in a future phase.
"""

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import Product, Purchase, User, db

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Set up logging
admin_logger = logging.getLogger('economy.admin')


def require_admin():
    """Decorator-like function to check admin access."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None


@admin_bp.route('/')
@login_required
def admin_panel():
    """Main admin panel."""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Show all products in admin panel (active and archived)
    products = Product.query.order_by(Product.is_active.desc(), Product.created_at.desc()).all()
    
    # Fix any None values in products before sending to template
    for product in products:
        if product.stock is None:
            product.stock = -1  # Use -1 to represent unlimited stock
    
    return render_template('admin.html', products=products)


@admin_bp.route('/purchases')
@login_required
def admin_purchases():
    """Admin view of all purchases."""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of purchases per page
    
    # Get purchases with user and product information, ordered by most recent first
    purchases_pagination = db.session.query(Purchase)\
        .join(User, Purchase.user_id == User.id)\
        .join(Product, Purchase.product_id == Product.id)\
        .order_by(Purchase.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    purchases = purchases_pagination.items
    
    return render_template('admin_purchases.html', 
                         purchases=purchases,
                         pagination=purchases_pagination)


# TODO: Add more admin routes for product management, economy config, etc.
# These will be extracted in a future phase to keep this PR focused. 