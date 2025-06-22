"""
User-specific routes for purchases and information pages.
"""

import logging
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Purchase

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


@user_bp.route('/how-to-earn')
def how_to_earn():
    """Information page about earning points in the economy system."""
    return render_template('how_to_earn.html') 