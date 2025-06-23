"""
Admin Product Management Routes - Product CRUD, digital templates, and inventory
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import datetime as dt
import os
import uuid
import json

from models import Product, Purchase, RoleAssignment, DownloadToken, db
from utils import allowed_file, save_uploaded_file, get_logger
from flask import current_app

app_logger = get_logger('admin.products')

products_bp = Blueprint('products', __name__, url_prefix='/products')

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create a new product"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price')
            stock = request.form.get('stock')
            product_type = request.form.get('product_type', 'physical')
            
            # Validate required fields
            if not name:
                flash('Product name is required.', 'error')
                return render_template('product_form.html', title='Add New Product')
            
            if not price or not price.isdigit() or int(price) <= 0:
                flash('Valid price is required.', 'error')
                return render_template('product_form.html', title='Add New Product')
            
            price = int(price)
            
            # Handle stock (None = unlimited, 0+ = limited)
            # For digital products, force unlimited stock
            if product_type in ['minecraft_skin', 'role', 'digital']:
                stock = None  # Digital products should always be unlimited
            else:
                # Only physical products can have limited stock
                if stock and stock.isdigit():
                    stock = int(stock)
                    if stock < 0:
                        stock = None  # Unlimited
                else:
                    stock = None  # Unlimited
            
            # Create product
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                product_type=product_type,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Handle file uploads based on product type
            if product_type == 'minecraft_skin':
                # Handle preview media (image or video)
                preview_file = request.files.get('preview_image')
                if preview_file and preview_file.filename:
                    if allowed_file(preview_file.filename):
                        preview_filename = save_uploaded_file(preview_file, 'preview')
                        if preview_filename:
                            product.preview_image_url = preview_filename
                        else:
                            flash('Error uploading preview media.', 'error')
                            return render_template('product_form.html', title='Add New Product')
                    else:
                        flash('Invalid preview media file type.', 'error')
                        return render_template('product_form.html', title='Add New Product')
                
                # Handle download file
                download_file = request.files.get('download_file')
                if download_file and download_file.filename:
                    if allowed_file(download_file.filename):
                        download_filename = save_uploaded_file(download_file, 'download')
                        if download_filename:
                            product.download_file_url = download_filename
                            product.delivery_method = 'download'
                            product.auto_delivery = True
                        else:
                            flash('Error uploading download file.', 'error')
                            return render_template('product_form.html', title='Add New Product')
                    else:
                        flash('Invalid download file type.', 'error')
                        return render_template('product_form.html', title='Add New Product')
            
            else:
                # Handle regular image upload for other product types
                image_file = request.files.get('image')
                if image_file and image_file.filename:
                    if allowed_file(image_file.filename):
                        image_filename = save_uploaded_file(image_file, 'image')
                        if image_filename:
                            product.image_url = image_filename
                        else:
                            flash('Error uploading image.', 'error')
                            return render_template('product_form.html', title='Add New Product')
                    else:
                        flash('Invalid image file type.', 'error')
                        return render_template('product_form.html', title='Add New Product')
            
            # Save to database
            db.session.add(product)
            db.session.commit()
            
            app_logger.info(f"Product created: {product.name} (ID: {product.id}) by {current_user.username}")
            flash(f'Product "{product.name}" created successfully!', 'success')
            
            # Redirect based on product type
            if product_type == 'minecraft_skin':
                return redirect(url_for('products.digital_templates'))
            else:
                return redirect(url_for('dashboard.admin_panel'))
                
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"Error creating product: {e}")
            flash('Error creating product. Please try again.', 'error')
            return render_template('product_form.html', title='Add New Product')
    
    return render_template('product_form.html', title='Add New Product')

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price')
            stock = request.form.get('stock')
            
            # Validate required fields
            if not name:
                flash('Product name is required.', 'error')
                return render_template('product_form.html', title='Edit Product', product=product)
            
            if not price or not price.isdigit() or int(price) <= 0:
                flash('Valid price is required.', 'error')
                return render_template('product_form.html', title='Edit Product', product=product)
            
            price = int(price)
            
            # Handle stock (None = unlimited, 0+ = limited)
            # For digital products, force unlimited stock
            if product.product_type in ['minecraft_skin', 'role', 'digital']:
                stock = None  # Digital products should always be unlimited
            else:
                # Only physical products can have limited stock
                if stock and stock.isdigit():
                    stock = int(stock)
                    if stock < 0:
                        stock = None  # Unlimited
                else:
                    stock = None  # Unlimited
            
            # Update product fields
            product.name = name
            product.description = description
            product.price = price
            product.stock = stock
            
            # Handle file uploads based on product type
            if product.product_type == 'minecraft_skin':
                # Handle preview media (image or video) - only update if new file uploaded
                preview_file = request.files.get('preview_image')
                if preview_file and preview_file.filename:
                    if allowed_file(preview_file.filename):
                        preview_filename = save_uploaded_file(preview_file, 'preview')
                        if preview_filename:
                            product.preview_image_url = preview_filename
                        else:
                            flash('Error uploading preview media.', 'error')
                            return render_template('product_form.html', title='Edit Product', product=product)
                    else:
                        flash('Invalid preview media file type.', 'error')
                        return render_template('product_form.html', title='Edit Product', product=product)
                
                # Handle download file - only update if new file uploaded
                download_file = request.files.get('download_file')
                if download_file and download_file.filename:
                    if allowed_file(download_file.filename):
                        download_filename = save_uploaded_file(download_file, 'download')
                        if download_filename:
                            product.download_file_url = download_filename
                            product.delivery_method = 'download'
                            product.auto_delivery = True
                        else:
                            flash('Error uploading download file.', 'error')
                            return render_template('product_form.html', title='Edit Product', product=product)
                    else:
                        flash('Invalid download file type.', 'error')
                        return render_template('product_form.html', title='Edit Product', product=product)
            
            else:
                # Handle regular image upload for other product types - only update if new file uploaded
                image_file = request.files.get('image')
                if image_file and image_file.filename:
                    if allowed_file(image_file.filename):
                        image_filename = save_uploaded_file(image_file, 'image')
                        if image_filename:
                            product.image_url = image_filename
                        else:
                            flash('Error uploading image.', 'error')
                            return render_template('product_form.html', title='Edit Product', product=product)
                    else:
                        flash('Invalid image file type.', 'error')
                        return render_template('product_form.html', title='Edit Product', product=product)
            
            # Save changes to database
            db.session.commit()
            
            app_logger.info(f"Product updated: {product.name} (ID: {product.id}) by {current_user.username}")
            flash(f'Product "{product.name}" updated successfully!', 'success')
            
            # Redirect based on product type
            if product.product_type == 'minecraft_skin':
                return redirect(url_for('products.digital_templates'))
            else:
                return redirect(url_for('dashboard.admin_panel'))
                
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"Error updating product: {e}")
            flash('Error updating product. Please try again.', 'error')
            return render_template('product_form.html', title='Edit Product', product=product)
    
    return render_template('product_form.html', title='Edit Product', product=product)

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete or archive a product"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    
    flash(f'Product "{product.name}" has been archived successfully.', 'success')
    return redirect(url_for('dashboard.admin_panel'))

@products_bp.route('/<int:product_id>/restore', methods=['POST'])
@login_required
def restore_product(product_id):
    """Restore an archived product"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    product = Product.query.get_or_404(product_id)
    product.is_active = True
    db.session.commit()
    
    flash(f'Product "{product.name}" has been restored successfully.', 'success')
    return redirect(url_for('dashboard.admin_panel'))

@products_bp.route('/digital-templates')
@login_required
def digital_templates():
    """Show digital product templates"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get digital products for template management
    digital_products = Product.query.filter(Product.product_type.in_(['digital', 'role'])).all()
    
    return render_template('digital_templates.html', products=digital_products)

@products_bp.route('/create-role-product', methods=['POST'])
@login_required
def create_role_product():
    """Create a role-based digital product"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # For now, just flash a message - would implement actual role product creation
    flash('Role product creation functionality not yet fully implemented', 'info')
    return redirect(url_for('products.digital_templates')) 