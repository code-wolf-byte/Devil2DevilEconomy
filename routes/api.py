"""
API routes for file management, downloads, and admin endpoints.
"""

import os
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import DownloadToken, db
from config import FileConfig

# Create blueprint
api_bp = Blueprint('api', __name__)

# Set up logging
api_logger = logging.getLogger('economy.api')


def allowed_file(filename):
    """Check if file extension is allowed."""
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in FileConfig.ALLOWED_EXTENSIONS)


def save_uploaded_file(file, file_type='misc'):
    """Save uploaded file and return the relative path."""
    try:
        filename = secure_filename(file.filename)
        
        # Add timestamp to prevent conflicts
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"
        
        # Create subdirectory based on file type
        file_ext = filename.lower().split('.')[-1]
        if file_ext in FileConfig.ALLOWED_IMAGE_EXTENSIONS:
            subfolder = 'images'
        elif file_ext in ['zip', 'rar', '7z', 'tar.gz']:
            subfolder = 'archives'
        elif file_ext in ['pdf', 'doc', 'docx', 'txt', 'md']:
            subfolder = 'documents'
        else:
            subfolder = file_type
        
        upload_path = os.path.join(current_app.static_folder, 'uploads', subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return os.path.join(subfolder, filename).replace('\\', '/')
        
    except Exception as e:
        api_logger.error(f"Error saving file: {e}")
        return None


@api_bp.route('/file-manager')
@login_required
def file_manager():
    """File manager for digital assets."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    
    upload_path = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    
    # Get all files in uploads directory
    files = []
    for root, dirs, filenames in os.walk(upload_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, upload_path)
            file_size = os.path.getsize(file_path)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            files.append({
                'name': filename,
                'path': relative_path.replace('\\', '/'),
                'size': file_size,
                'modified': file_modified,
                'is_image': filename.lower().endswith(tuple(FileConfig.ALLOWED_IMAGE_EXTENSIONS)),
                'is_archive': filename.lower().endswith(('.zip', '.rar', '.7z', '.tar.gz')),
                'is_document': filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.md'))
            })
    
    # Sort files by modification date (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('file_manager.html', files=files)


@api_bp.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    """Upload a file for digital products."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('api.file_manager'))
    
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('api.file_manager'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('api.file_manager'))
    
    if file and allowed_file(file.filename):
        relative_path = save_uploaded_file(file, 'uploads')
        if relative_path:
            flash(f'File uploaded successfully: {relative_path}')
        else:
            flash('Error uploading file.')
    else:
        allowed_ext = ', '.join(FileConfig.ALLOWED_EXTENSIONS)
        flash(f'Invalid file type. Allowed types: {allowed_ext}')
    
    return redirect(url_for('api.file_manager'))


@api_bp.route('/delete-file', methods=['POST'])
@login_required
def delete_file():
    """Delete a file from uploads."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('api.file_manager'))
    
    file_path = request.form.get('file_path')
    if not file_path:
        flash('No file specified')
        return redirect(url_for('api.file_manager'))
    
    full_path = os.path.join(current_app.static_folder, 'uploads', file_path)
    
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            flash(f'File deleted: {file_path}')
            api_logger.info(f"File deleted by {current_user.username}: {file_path}")
        else:
            flash('File not found')
    except Exception as e:
        api_logger.error(f"Error deleting file {file_path}: {e}")
        flash(f'Error deleting file: {str(e)}')
    
    return redirect(url_for('api.file_manager'))


@api_bp.route('/download/<token>')
@login_required
def download_file(token):
    """Secure download route for digital products."""
    try:
        # Find and validate download token
        download_token = DownloadToken.get_valid_token(token)
        
        if not download_token:
            # Check if token exists but is invalid
            expired_token = DownloadToken.query.filter_by(token=token).first()
            if expired_token:
                if expired_token.is_expired:
                    flash('Download link has expired')
                elif not expired_token.is_valid:
                    flash('Download limit exceeded')
                else:
                    flash('Invalid download link')
            else:
                flash('Invalid download link')
            return redirect(url_for('user.my_purchases'))
        
        # Check if user owns this download
        if download_token.user_id != current_user.id:
            flash('Access denied')
            api_logger.warning(f"Unauthorized download attempt: User {current_user.id} tried to access token for user {download_token.user_id}")
            return redirect(url_for('user.my_purchases'))
        
        # Build file path
        file_path = os.path.join(current_app.static_folder, 'uploads', download_token.file_path)
        
        if not os.path.exists(file_path):
            flash('File not found')
            api_logger.error(f"Download file not found: {file_path}")
            return redirect(url_for('user.my_purchases'))
        
        # Use download token
        if not download_token.use_download():
            flash('Download limit exceeded')
            return redirect(url_for('user.my_purchases'))
        
        db.session.commit()
        
        # Get filename for download
        filename = download_token.original_filename or os.path.basename(download_token.file_path)
        
        api_logger.info(f"File downloaded: {filename} by user {current_user.username}")
        
        # Send file for download
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        api_logger.error(f"Download error: {e}")
        flash('Download failed. Please try again.')
        return redirect(url_for('user.my_purchases'))


@api_bp.route('/cleanup-tokens', methods=['POST'])
@login_required
def cleanup_expired_tokens():
    """Clean up expired download tokens (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        cleaned_count = DownloadToken.cleanup_expired_tokens()
        api_logger.info(f"Cleaned up {cleaned_count} expired download tokens")
        return jsonify({'success': True, 'cleaned_count': cleaned_count})
    except Exception as e:
        api_logger.error(f"Error cleaning up tokens: {e}")
        return jsonify({'error': 'Failed to cleanup tokens'}), 500 