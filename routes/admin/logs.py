"""
Admin Log Management Routes - View, download, and manage application logs
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from datetime import datetime
import os

from utils import get_logger

app_logger = get_logger('admin.logs')

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@logs_bp.route('/')
@login_required
def admin_logs():
    """Admin log viewer with filtering and search capabilities"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Log viewing logic here
    # This would contain the full log viewing code from the original admin.py
    pass

@logs_bp.route('/download/<log_type>')
@login_required
def admin_logs_download(log_type):
    """Download log files"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Log download logic here
    pass

@logs_bp.route('/clear/<log_type>', methods=['POST'])
@login_required
def admin_logs_clear(log_type):
    """Clear log files (admin only)"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Log clearing logic here
    pass 