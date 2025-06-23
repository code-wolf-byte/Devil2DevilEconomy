"""
User-specific routes for purchases and information pages.
"""

import logging
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Purchase, Product, DownloadToken, db

# Create blueprint
user_bp = Blueprint('user', __name__)

# Set up logging
user_logger = logging.getLogger('economy.user')


@user_bp.route('/my-purchases')
@login_required
def my_purchases():
    """Show user's purchase history."""
    purchases = Purchase.get_user_purchases(current_user.id)
    return render_template('my_purchases.html', purchases=purchases)


@user_bp.route('/downloads')
@login_required
def downloads():
    """Show user's downloadable digital products."""
    # Get all purchases of digital products for the current user
    digital_purchases = db.session.query(Purchase)\
        .join(Product, Purchase.product_id == Product.id)\
        .filter(
            Purchase.user_id == current_user.id,
            Product.product_type.in_(['minecraft_skin', 'role', 'digital', 'game_code', 'custom']),
            Product.delivery_method == 'download'
        )\
        .order_by(Purchase.timestamp.desc())\
        .all()
    
    # Create fresh download tokens for each purchase
    downloads_data = []
    for purchase in digital_purchases:
        product = purchase.product
        
        # Create a new download token (valid for 24 hours)
        download_token = DownloadToken.create_token(
            user_id=current_user.id,
            purchase_id=purchase.id,
            file_path=product.download_file_url,
            hours=24,
            original_filename=product.name
        )
        
        db.session.add(download_token)
        
        downloads_data.append({
            'purchase': purchase,
            'product': product,
            'download_url': f'/download/{download_token.token}',
            'expires_at': download_token.expires_at
        })
    
    db.session.commit()
    
    return render_template('downloads.html', downloads=downloads_data)


@user_bp.route('/how-to-earn')
def how_to_earn():
    """Information page about earning points in the economy system."""
    return render_template('how_to_earn.html') 