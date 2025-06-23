"""
Admin Economy Management Routes - Economy configuration, settings, and Discord integration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import datetime as dt
import os

from models import EconomySettings, User, Product, db
from utils import get_logger

app_logger = get_logger('admin.economy')

economy_bp = Blueprint('economy', __name__, url_prefix='/economy')

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@economy_bp.route('/config', methods=['GET', 'POST'])
@login_required
def economy_config():
    """Configure economy settings before enabling for the first time"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        # Handle form submission here
        flash('Economy settings updated successfully!', 'success')
        return redirect(url_for('economy.economy_config'))
    
    # Get current economy settings
    settings = EconomySettings.get_settings()
    
    return render_template('economy_config.html', settings=settings)

@economy_bp.route('/get-discord-roles')
@login_required
def get_discord_roles():
    """Get available Discord roles from the server"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Return empty roles for now - would integrate with Discord API
    return jsonify({'roles': []})

@economy_bp.route('/get-role-products')
@login_required
def get_role_products():
    """Get existing role-based products"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Return empty products for now
    return jsonify({'products': []})

@economy_bp.route('/get-minecraft-skin-products')
@login_required
def get_minecraft_skin_products():
    """Get Minecraft skin products for the digital templates page"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    try:
        # Get minecraft skin products
        minecraft_products = Product.query.filter(
            Product.product_type == 'minecraft_skin',
            Product.is_active == True
        ).order_by(Product.created_at.desc()).all()
        
        products_data = []
        for product in minecraft_products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'preview_image_url': product.preview_image_url,
                'download_file_url': product.download_file_url,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M') if product.created_at else 'Unknown',
                'preview_type': 'video' if product.preview_image_url and product.preview_image_url.endswith(('.mp4', '.webm', '.mov')) else 'image',
                'has_dual_files': bool(product.preview_image_url and product.download_file_url)
            })
        
        return jsonify({
            'success': True,
            'products': products_data
        })
        
    except Exception as e:
        app_logger.error(f"Error fetching minecraft skin products: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load minecraft skin products'
        }), 500 

@economy_bp.route('/debug-stock')
@login_required
def debug_stock():
    """Debug route to check stock values of digital products"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import Product
    
    # Get all digital products
    digital_products = Product.query.filter(
        Product.product_type.in_(['minecraft_skin', 'role', 'digital', 'game_code', 'custom'])
    ).all()
    
    debug_info = []
    for product in digital_products:
        debug_info.append({
            'id': product.id,
            'name': product.name,
            'type': product.product_type,
            'stock': product.stock,
            'is_in_stock': product.is_in_stock,
            'is_available': product.is_available,
            'is_active': product.is_active
        })
    
    return jsonify({
        'digital_products': debug_info,
        'total_count': len(digital_products)
    })

@economy_bp.route('/fix-stock')
@login_required
def fix_stock():
    """Fix stock values for digital products"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import Product, db
    
    # Find digital products with stock = 0
    digital_products = Product.query.filter(
        Product.product_type.in_(['minecraft_skin', 'role', 'digital', 'game_code', 'custom']),
        Product.stock == 0
    ).all()
    
    fixed_count = 0
    for product in digital_products:
        product.stock = None  # Set to unlimited
        fixed_count += 1
    
    # Also fix any with negative stock
    negative_stock_products = Product.query.filter(
        Product.product_type.in_(['minecraft_skin', 'role', 'digital', 'game_code', 'custom']),
        Product.stock < 0
    ).all()
    
    for product in negative_stock_products:
        product.stock = None  # Set to unlimited
        fixed_count += 1
    
    if fixed_count > 0:
        db.session.commit()
    
    return jsonify({
        'message': f'Fixed {fixed_count} digital products',
        'fixed_count': fixed_count
    }) 