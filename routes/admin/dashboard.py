"""
Admin Dashboard Routes - Main admin panel and overview
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import Product, Purchase, User, db

dashboard_bp = Blueprint('dashboard', __name__)

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@dashboard_bp.route('/')
@login_required
def admin_panel():
    """Main admin dashboard"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Show all products in admin panel (active and archived), ordered by status and creation date
    products = Product.query.order_by(Product.is_active.desc(), Product.created_at.desc()).all()
    
    # Fix any None values in products before sending to template
    for product in products:
        if product.stock is None:
            product.stock = -1  # Use -1 to represent unlimited stock
    
    return render_template('admin.html', products=products)

@dashboard_bp.route('/purchases')
@login_required
def admin_purchases():
    """View all purchases"""
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