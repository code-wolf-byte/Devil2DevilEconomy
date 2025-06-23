"""
Admin routes for product management and system configuration.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import Product, Purchase, User, EconomySettings, Achievement, UserAchievement, DownloadToken, RoleAssignment, db

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


@admin_bp.route('/leaderboard')
@login_required
def admin_leaderboard():
    """Admin leaderboard showing all users ranked by points/balance"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get sorting parameter (default to balance)
    sort_by = request.args.get('sort', 'balance')
    order = request.args.get('order', 'desc')
    
    # Get all non-admin users with their statistics
    query = User.query.filter(User.is_admin == False)
    
    if sort_by == 'balance':
        if order == 'desc':
            query = query.order_by(User.balance.desc())
        else:
            query = query.order_by(User.balance.asc())
    elif sort_by == 'points':
        if order == 'desc':
            query = query.order_by(User.points.desc())
        else:
            query = query.order_by(User.points.asc())
    elif sort_by == 'messages':
        if order == 'desc':
            query = query.order_by(User.message_count.desc())
        else:
            query = query.order_by(User.message_count.asc())
    elif sort_by == 'username':
        if order == 'desc':
            query = query.order_by(User.username.desc())
        else:
            query = query.order_by(User.username.asc())
    elif sort_by == 'created':
        if order == 'desc':
            query = query.order_by(User.created_at.desc())
        else:
            query = query.order_by(User.created_at.asc())
    
    users = query.all()
    
    # Calculate additional statistics
    total_users = len(users)
    total_balance = sum(user.balance or 0 for user in users)
    total_points_earned = sum(user.points or 0 for user in users)
    
    return render_template('admin_leaderboard.html', 
                         users=users,
                         total_users=total_users,
                         total_balance=total_balance,
                         total_points_earned=total_points_earned,
                         sort_by=sort_by,
                         order=order)


@admin_bp.route('/user/<user_id>/breakdown')
@login_required
def admin_user_breakdown(user_id):
    """Show detailed breakdown of how a user earned their points"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    user = User.query.get_or_404(user_id)
    
    # Get user's purchases
    from models import UserAchievement, Achievement
    purchases = Purchase.query.filter_by(user_id=user_id)\
        .join(Product, Purchase.product_id == Product.id)\
        .order_by(Purchase.timestamp.desc()).all()
    
    # Get user's achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user_id)\
        .join(Achievement, UserAchievement.achievement_id == Achievement.id)\
        .order_by(UserAchievement.achieved_at.desc()).all()
    
    # Calculate point sources
    points_breakdown = {
        'purchases_spent': sum(purchase.points_spent for purchase in purchases),
        'achievement_points': sum(ua.achievement.points for ua in user_achievements),
        'verification_bonus': user.verification_bonus_received,
        'onboarding_bonus': user.onboarding_bonus_received,
        'current_balance': user.balance or 0,
        'total_earned': user.points or 0
    }
    
    # Calculate estimated points from activities (these would be from bot interactions)
    estimated_activity_points = {
        'message_points': (user.message_count or 0) * 2,  # Estimate 2 points per message
        'reaction_points': (user.reaction_count or 0) * 1,  # Estimate 1 point per reaction
        'voice_points': (user.voice_minutes or 0) * 0.5,  # Estimate 0.5 points per voice minute
    }
    
    return render_template('admin_user_breakdown.html',
                         user=user,
                         purchases=purchases,
                         user_achievements=user_achievements,
                         points_breakdown=points_breakdown,
                         estimated_activity_points=estimated_activity_points)


@admin_bp.route('/logs')
@login_required
def admin_logs():
    """Admin log viewer with filtering and search capabilities"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get parameters
    log_type = request.args.get('type', 'app')  # app, error, all
    search_term = request.args.get('search', '')
    level_filter = request.args.get('level', '')  # INFO, ERROR, WARNING, DEBUG
    lines_limit = int(request.args.get('lines', 100))  # Number of lines to show
    page = int(request.args.get('page', 1))
    
    # Define log files
    log_files = {
        'app': 'logs/economy_app.log',
        'error': 'logs/economy_errors.log'
    }
    
    log_entries = []
    total_lines = 0
    
    try:
        files_to_read = []
        if log_type == 'all':
            files_to_read = list(log_files.values())
        elif log_type in log_files:
            files_to_read = [log_files[log_type]]
        
        # Read log files
        for log_file in files_to_read:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        
                        # Parse each line
                        for line_num, line in enumerate(lines):
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Parse log format: timestamp - logger - level - message
                            parts = line.split(' - ', 3)
                            if len(parts) >= 4:
                                timestamp_str, logger, level, message = parts
                                
                                # Apply level filter
                                if level_filter and level_filter.upper() not in level.upper():
                                    continue
                                
                                # Apply search filter
                                if search_term and search_term.lower() not in line.lower():
                                    continue
                                
                                # Try to parse timestamp
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                except:
                                    timestamp = None
                                
                                log_entries.append({
                                    'timestamp': timestamp,
                                    'timestamp_str': timestamp_str,
                                    'logger': logger,
                                    'level': level,
                                    'message': message,
                                    'file': os.path.basename(log_file),
                                    'line_number': line_num + 1,
                                    'raw_line': line
                                })
                            else:
                                # Handle malformed lines
                                log_entries.append({
                                    'timestamp': None,
                                    'timestamp_str': '',
                                    'logger': 'unknown',
                                    'level': 'INFO',
                                    'message': line,
                                    'file': os.path.basename(log_file),
                                    'line_number': line_num + 1,
                                    'raw_line': line
                                })
                
                except Exception as e:
                    admin_logger.error(f"Error reading log file {log_file}: {e}")
        
        # Sort by timestamp (newest first)
        log_entries.sort(key=lambda x: x['timestamp'] or datetime.min, reverse=True)
        
        # Pagination
        per_page = lines_limit
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_entries = log_entries[start_idx:end_idx]
        
        # Calculate pagination info
        total_entries = len(log_entries)
        total_pages = (total_entries + per_page - 1) // per_page
        
        # Calculate display range for pagination
        start_entry = (page - 1) * per_page + 1 if total_entries > 0 else 0
        end_entry = min(page * per_page, total_entries)
        
        # Get log file sizes and last modified times
        log_file_info = {}
        for name, path in log_files.items():
            if os.path.exists(path):
                stat = os.stat(path)
                log_file_info[name] = {
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'exists': True
                }
            else:
                log_file_info[name] = {'exists': False}
        
        return render_template('admin_logs.html',
                             log_entries=paginated_entries,
                             log_type=log_type,
                             search_term=search_term,
                             level_filter=level_filter,
                             lines_limit=lines_limit,
                             page=page,
                             total_pages=total_pages,
                             total_entries=total_entries,
                             total_lines=total_lines,
                             log_file_info=log_file_info,
                             has_prev=page > 1,
                             has_next=page < total_pages,
                             prev_page=page - 1 if page > 1 else None,
                             next_page=page + 1 if page < total_pages else None,
                             start_entry=start_entry,
                             end_entry=end_entry)
    
    except Exception as e:
        admin_logger.error(f"Error in admin_logs: {e}")
        flash(f'Error reading logs: {str(e)}')
        return redirect(url_for('admin.admin_panel'))


@admin_bp.route('/logs/download/<log_type>')
@login_required
def admin_logs_download(log_type):
    """Download log files"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    log_files = {
        'app': 'logs/economy_app.log',
        'error': 'logs/economy_errors.log'
    }
    
    if log_type not in log_files:
        flash('Invalid log type')
        return redirect(url_for('admin.admin_logs'))
    
    log_file = log_files[log_type]
    
    if not os.path.exists(log_file):
        flash(f'Log file not found: {log_file}')
        return redirect(url_for('admin.admin_logs'))
    
    try:
        return send_from_directory(
            os.path.dirname(os.path.abspath(log_file)),
            os.path.basename(log_file),
            as_attachment=True,
            download_name=f'economy_{log_type}_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
    except Exception as e:
        admin_logger.error(f"Error downloading log file: {e}")
        flash('Error downloading log file')
        return redirect(url_for('admin.admin_logs'))


@admin_bp.route('/logs/clear/<log_type>', methods=['POST'])
@login_required
def admin_logs_clear(log_type):
    """Clear log files (admin only)"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    log_files = {
        'app': 'logs/economy_app.log',
        'error': 'logs/economy_errors.log'
    }
    
    if log_type not in log_files:
        flash('Invalid log type')
        return redirect(url_for('admin.admin_logs'))
    
    log_file = log_files[log_type]
    
    try:
        if os.path.exists(log_file):
            # Backup the log file before clearing
            backup_name = f"{log_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(log_file, backup_name)
            
            # Create new empty log file
            with open(log_file, 'w') as f:
                f.write('')
            
            flash(f'{log_type.title()} log cleared successfully. Backup saved as {os.path.basename(backup_name)}')
            admin_logger.info(f"Admin {current_user.username} cleared {log_type} log file")
        else:
            flash(f'Log file not found: {log_file}')
    
    except Exception as e:
        admin_logger.error(f"Error clearing log file: {e}")
        flash('Error clearing log file')
    
    return redirect(url_for('admin.admin_logs')) 