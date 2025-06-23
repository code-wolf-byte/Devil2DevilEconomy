"""
Admin File Management Routes - Upload, manage, and organize digital assets
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import os

from utils import get_logger, allowed_file
from flask import current_app

app_logger = get_logger('admin.files')

files_bp = Blueprint('files', __name__, url_prefix='/files')

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@files_bp.route('/manager')
@login_required
def file_manager():
    """File manager for digital assets"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get list of uploaded files
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    files = []
    
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if os.path.isfile(os.path.join(upload_folder, filename)):
                file_path = os.path.join(upload_folder, filename)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                files.append({
                    'name': filename,
                    'size': file_size,
                    'modified': file_modified
                })
    
    return render_template('file_manager.html', files=files)

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a file for digital products"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('files.file_manager'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('files.file_manager'))
    
    # For now, just flash a message - would implement actual file upload
    flash(f'File upload functionality not yet implemented', 'info')
    return redirect(url_for('files.file_manager'))

@files_bp.route('/delete', methods=['POST'])
@login_required
def delete_file():
    """Delete a file from uploads"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    filename = request.form.get('filename')
    if not filename:
        flash('No filename provided', 'error')
        return redirect(url_for('files.file_manager'))
    
    # For now, just flash a message - would implement actual file deletion
    flash(f'File deletion functionality not yet implemented', 'info')
    return redirect(url_for('files.file_manager')) 