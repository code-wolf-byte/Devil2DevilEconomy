"""
File handling utilities
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {
        # Images
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz', 'tar.gz',
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'md', 'rtf',
        # Audio
        'mp3', 'wav', 'ogg', 'flac', 'm4a',
        # Video
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'ogv',
        # Minecraft specific
        'mcpack', 'mcworld', 'mctemplate', 'mcaddon',
        # Other
        'json', 'xml', 'csv', 'exe', 'msi'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, file_type='image'):
    """Save uploaded file securely and return filename"""
    try:
        # Generate secure filename (prevent any directory traversal)
        original_filename = secure_filename(file.filename)
        # Remove any remaining path separators and dots
        safe_filename = original_filename.replace('..', '').replace('/', '').replace('\\', '')
        if not safe_filename:
            safe_filename = 'upload'
        
        # Generate completely new filename with safe extension
        file_ext = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else 'jpg'
        
        # Validate extension based on file type
        if file_type == 'image':
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                file_ext = 'jpg'
        elif file_type == 'preview':
            # Allow both images and videos for preview
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'ogv', 'mov'}:
                file_ext = 'jpg'
        
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Ensure upload directory exists and is secure
        upload_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create full file path and verify it's within upload directory
        file_path = os.path.abspath(os.path.join(upload_dir, unique_filename))
        if not file_path.startswith(upload_dir):
            current_app.logger.error('Invalid file path detected during upload')
            return None
        
        # Validate file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            current_app.logger.error(f'File too large: {file_size} bytes')
            return None
        
        # Save file
        file.save(file_path)
        current_app.logger.info(f"{file_type.capitalize()} uploaded successfully: {unique_filename}")
        return unique_filename
        
    except Exception as e:
        current_app.logger.error(f"Error saving uploaded file: {e}")
        return None 