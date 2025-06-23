"""
Admin User Management Routes - User analytics, leaderboard, and user details
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import User, Purchase, Achievement, UserAchievement, Product, db

users_bp = Blueprint('users', __name__, url_prefix='/users')

def require_admin():
    """Helper function to check admin privileges"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('shop.index'))
    return None

@users_bp.route('/leaderboard')
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

@users_bp.route('/<user_id>/breakdown')
@login_required
def admin_user_breakdown(user_id):
    """Show detailed breakdown of how a user earned their points"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    user = User.query.get_or_404(user_id)
    
    # Get user's purchases
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