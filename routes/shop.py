"""
Shop routes for product browsing and purchasing.
"""

import uuid
import logging
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import Product, Purchase, User, db
from models.base import db_transaction

# Create blueprint
shop_bp = Blueprint('shop', __name__)

# Set up logging
shop_logger = logging.getLogger('economy.shop')


def validate_user_balance(user):
    """Ensure user has valid balance and points values."""
    if user.balance is None:
        user.balance = 0
    if user.points is None:
        user.points = 0
    db.session.commit()


@shop_bp.route('/')
def index():
    """Main shop page showing all available products."""
    # Get all active products
    products = Product.get_active_products()
    
    # Note: Template will handle None stock values properly
    
    # Get current user's purchases if they're logged in
    user_purchases = []
    if current_user.is_authenticated:
        validate_user_balance(current_user)
        user_purchases = Purchase.get_user_purchases(current_user.id)
    
    return render_template('index.html', products=products, purchases=user_purchases)


@shop_bp.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase(product_id):
    """Handle product purchase with atomic transaction."""
    try:
        with db_transaction() as session:
            # Re-fetch current user with lock to prevent race conditions
            current_user_fresh = session.query(User).with_for_update().filter_by(id=current_user.id).first()
            if not current_user_fresh:
                flash('User not found')
                return redirect(url_for('shop.index'))
            
            # Lock the product row to prevent race conditions
            product = session.query(Product).with_for_update().filter_by(id=product_id).first()
            if not product:
                flash('Product not found')
                return redirect(url_for('shop.index'))
            
            # Validate product availability
            if not product.is_available:
                if not product.is_active:
                    flash('Product is no longer available')
                elif not product.is_in_stock:
                    flash('Product is out of stock')
                return redirect(url_for('shop.index'))
            
            # Validate user balance
            if current_user_fresh.balance < product.price:
                flash(f'Insufficient balance. You need {product.price} points but only have {current_user_fresh.balance}.')
                return redirect(url_for('shop.index'))
            
            # Generate UUID if user doesn't have one
            if not current_user_fresh.user_uuid:
                current_user_fresh.user_uuid = str(uuid.uuid4())
                shop_logger.info(f"Generated new UUID for user {current_user_fresh.username}: {current_user_fresh.user_uuid}")
            
            # Process the purchase
            success, message = _process_purchase(current_user_fresh, product, session)
            
            if success:
                # Update current_user object for session
                current_user.balance = current_user_fresh.balance
                current_user.user_uuid = current_user_fresh.user_uuid
                
                flash(message)
                shop_logger.info(f"Purchase completed: User {current_user_fresh.username} bought {product.name} for {product.price} points")
                
                # Check for auto-download redirect
                if 'download_token' in message:
                    token_match = re.search(r'/download/([a-f0-9-]+)', message)
                    if token_match:
                        download_token = token_match.group(1)
                        return redirect(url_for('api.download_file', token=download_token))
            else:
                flash(f'Purchase failed: {message}')
                shop_logger.error(f"Purchase failed for user {current_user_fresh.username}: {message}")
            
            return redirect(url_for('shop.index'))
            
    except Exception as e:
        shop_logger.error(f"Purchase error: {str(e)}")
        flash('Purchase failed. Please try again.')
        return redirect(url_for('shop.index'))


def _process_purchase(user, product, session):
    """Process the actual purchase transaction."""
    try:
        # Deduct points from user balance
        user.spend_points(product.price, f"Purchase of {product.name}")
        
        # Reduce stock if limited
        if not product.reduce_stock():
            return False, "Product went out of stock during purchase"
        
        # Create purchase record
        purchase = Purchase(
            user_id=user.id, 
            product_id=product.id, 
            points_spent=product.price
        )
        session.add(purchase)
        session.flush()  # Get purchase ID for digital delivery
        
        # Handle digital product delivery
        if product.is_digital and product.auto_delivery:
            delivery_success, delivery_message = _handle_digital_delivery(user, product, purchase, session)
            
            if delivery_success:
                purchase.status = 'completed'
                purchase.delivery_info = delivery_message
                
                # Special handling for Minecraft skins with auto-download
                if product.product_type == 'minecraft_skin' and product.delivery_method == 'download':
                    return True, f'Purchase successful! Visit the Downloads page to access your new skin.'
                
                return True, f'Purchase successful! Visit the Downloads page to access your digital content.'
            else:
                purchase.status = 'pending_delivery'
                purchase.delivery_info = delivery_message
                return True, f'Purchase completed but delivery pending: {delivery_message}'
        else:
            purchase.status = 'completed'
            purchase.delivery_info = f'Manual delivery - UUID: {user.user_uuid}'
            return True, f'Purchase successful! Your UUID: {user.user_uuid}'
            
    except ValueError as e:
        # This handles insufficient balance errors
        return False, str(e)
    except Exception as e:
        shop_logger.error(f"Error processing purchase: {e}")
        return False, "Internal error during purchase processing"


def _handle_digital_delivery(user, product, purchase, session):
    """Handle digital product delivery (placeholder for now)."""
    # TODO: Move DigitalDeliveryService logic here or create a proper service class
    
    if product.delivery_method == 'download':
        # Create download token
        try:
            from models import DownloadToken
            from datetime import datetime, timedelta
            
            # Get file path from delivery config
            delivery_config = product.delivery_config
            file_path = delivery_config.get('file_path', product.download_file_url)
            
            if not file_path:
                return False, "No download file configured"
            
            # Create download token
            token = DownloadToken.create_token(
                user_id=user.id,
                purchase_id=purchase.id,
                file_path=file_path,
                hours=24,  # Token valid for 24 hours
                original_filename=product.name
            )
            
            session.add(token)
            session.flush()
            
            download_url = f"/download/{token.token}"
            return True, f"Download ready: <a href='{download_url}'>Click here to download</a>"
            
        except Exception as e:
            shop_logger.error(f"Error creating download token: {e}")
            return False, "Failed to create download link"
    
    elif product.delivery_method == 'auto_role':
        # Queue role assignment
        try:
            from models import RoleAssignment
            
            delivery_config = product.delivery_config
            role_id = delivery_config.get('role_id')
            
            if not role_id:
                return False, "No role configured for this product"
            
            role_assignment = RoleAssignment(
                user_id=user.id,
                role_id=role_id,
                purchase_id=purchase.id,
                status='pending'
            )
            
            session.add(role_assignment)
            session.flush()
            
            return True, f"Discord role assignment queued. You will receive the role shortly."
            
        except Exception as e:
            shop_logger.error(f"Error queuing role assignment: {e}")
            return False, "Failed to queue role assignment"
    
    elif product.delivery_method == 'code_generation':
        # Generate a simple code
        try:
            import secrets
            import string
            
            # Generate a random code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            return True, f"Your code: <strong>{code}</strong>"
            
        except Exception as e:
            shop_logger.error(f"Error generating code: {e}")
            return False, "Failed to generate code"
    
    else:
        # Manual delivery
        return True, "Your purchase will be processed manually. Please contact an administrator." 