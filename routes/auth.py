"""
Authentication routes for Discord OAuth login/logout.
"""

import os
import requests
import logging
from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from models import User, db
from config import Settings

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Set up logging
auth_logger = logging.getLogger('economy.auth')

# Discord API constants
DISCORD_API_BASE_URL = "https://discord.com/api/v10"
DISCORD_OAUTH_SCOPE = "identify guilds"

def get_discord_avatar_url(user_id, avatar_hash):
    """Get Discord avatar URL from user ID and avatar hash."""
    if not avatar_hash:
        # Default Discord avatar
        return f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png"
    
    # Check if avatar is animated (starts with 'a_')
    if avatar_hash.startswith('a_'):
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.gif"
    else:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"


def check_discord_admin_status(user_data, access_token):
    """Check if user has admin permissions in the Discord server."""
    is_admin = False
    guild_id = Settings.GUILD_ID or "1082823852322725888"  # Fallback for testing
    
    auth_logger.info(f"Checking admin status for user: {user_data['username']} (ID: {user_data['id']})")
    
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Try to get guild member info using user token
        guild_member_response = requests.get(
            f"{DISCORD_API_BASE_URL}/users/@me/guilds/{guild_id}/member",
            headers=headers
        )
        
        if guild_member_response.status_code == 200:
            member_data = guild_member_response.json()
            roles = member_data.get('roles', [])
            auth_logger.debug(f"User roles: {roles}")
            
            # Get guild roles to check for admin permissions
            bot_token = Settings.DISCORD_TOKEN
            if bot_token:
                bot_headers = {'Authorization': f'Bot {bot_token}'}
                roles_response = requests.get(
                    f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/roles",
                    headers=bot_headers
                )
                
                if roles_response.status_code == 200:
                    guild_roles = roles_response.json()
                    
                    for role_id in roles:
                        for guild_role in guild_roles:
                            if guild_role['id'] == role_id:
                                permissions = int(guild_role.get('permissions', 0))
                                
                                # Check for Administrator permission (0x8) or Manage Server (0x20)
                                if permissions & 0x8:
                                    is_admin = True
                                    auth_logger.info(f"User has Administrator permission via role: {guild_role['name']}")
                                    break
                                elif permissions & 0x20:
                                    is_admin = True
                                    auth_logger.info(f"User has Manage Server permission via role: {guild_role['name']}")
                                    break
                        if is_admin:
                            break
                else:
                    auth_logger.warning(f"Failed to get guild roles: {roles_response.text}")
            else:
                auth_logger.warning("Bot token not available for role checking")
        else:
            auth_logger.warning(f"Failed to get guild member info: {guild_member_response.text}")
            
            # Alternative method: Try using bot token to get member info
            bot_token = Settings.DISCORD_TOKEN
            if bot_token:
                bot_headers = {'Authorization': f'Bot {bot_token}'}
                bot_member_response = requests.get(
                    f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/members/{user_data['id']}",
                    headers=bot_headers
                )
                
                if bot_member_response.status_code == 200:
                    member_data = bot_member_response.json()
                    roles = member_data.get('roles', [])
                    
                    # Get guild roles and check permissions
                    roles_response = requests.get(
                        f"{DISCORD_API_BASE_URL}/guilds/{guild_id}/roles",
                        headers=bot_headers
                    )
                    
                    if roles_response.status_code == 200:
                        guild_roles = roles_response.json()
                        
                        for role_id in roles:
                            for guild_role in guild_roles:
                                if guild_role['id'] == role_id:
                                    permissions = int(guild_role.get('permissions', 0))
                                    
                                    # Check for admin permissions
                                    if permissions & 0x8 or permissions & 0x20:
                                        is_admin = True
                                        auth_logger.info(f"User has admin permission via role: {guild_role['name']}")
                                        break
                            if is_admin:
                                break
                else:
                    auth_logger.warning(f"Failed to get member info via bot: {bot_member_response.text}")
                    
    except Exception as e:
        auth_logger.error(f"Error checking admin status: {e}")
        import traceback
        auth_logger.error(traceback.format_exc())
    
    auth_logger.info(f"Final admin status for {user_data['username']}: {is_admin}")
    return is_admin


def create_or_update_user(user_data, is_admin):
    """Create or update user in database."""
    avatar_url = get_discord_avatar_url(user_data['id'], user_data.get('avatar'))
    
    # Try to get user by primary key (id) first, then by discord_id
    user = User.query.filter_by(id=user_data['id']).first()
    if not user:
        user = User.query.filter_by(discord_id=user_data['id']).first()
    
    if not user:
        try:
            user = User(
                id=user_data['id'],  # Use Discord ID as primary key
                username=user_data['username'],
                discord_id=user_data['id'],
                avatar_url=avatar_url,
                is_admin=is_admin,
                points=0,
                balance=0
            )
            db.session.add(user)
            db.session.commit()
            auth_logger.info(f"Created new user: {user.username} (Admin: {is_admin})")
        except Exception as e:
            # Rollback and try to get user again in case of race condition
            db.session.rollback()
            user = User.query.filter_by(id=user_data['id']).first()
            if not user:
                user = User.query.filter_by(discord_id=user_data['id']).first()
            if not user:
                raise e  # Re-raise if we still can't find the user
            auth_logger.info(f"Race condition resolved, found existing user: {user.username}")
    
    # Update user information and fix any null balance issues
    user.is_admin = is_admin
    user.username = user_data['username']  # Update username in case it changed
    user.avatar_url = avatar_url
    
    # Fix any None balance or points (for existing users)
    if user.balance is None:
        user.balance = 0
    if user.points is None:
        user.points = 0
    
    try:
        db.session.commit()
        auth_logger.info(f"Updated existing user: {user.username} (Admin: {is_admin})")
    except Exception as e:
        db.session.rollback()
        auth_logger.error(f"Error updating user: {e}")
    
    return user


@auth_bp.route('/login')
def login():
    """Redirect to Discord OAuth authorization."""
    oauth_url = Settings.get_discord_oauth_url()
    if not oauth_url:
        flash('Discord OAuth not configured')
        return redirect(url_for('shop.index'))
    
    return redirect(oauth_url)


@auth_bp.route('/callback')
def callback():
    """Handle Discord OAuth callback."""
    try:
        code = request.args.get('code')
        if not code:
            flash('No authorization code provided')
            return redirect(url_for('shop.index'))
        
        # Exchange code for access token
        data = {
            'client_id': Settings.DISCORD_CLIENT_ID,
            'client_secret': Settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': Settings.DISCORD_REDIRECT_URI
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        auth_logger.debug(f"Requesting token with client_id: {Settings.DISCORD_CLIENT_ID}")
        response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=data, headers=headers)
        
        if response.status_code != 200:
            auth_logger.error(f"Failed to get access token: {response.text}")
            flash('Failed to get access token from Discord')
            return redirect(url_for('shop.index'))
        
        access_token = response.json()['access_token']
        
        # Get user information
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers)
        
        if user_response.status_code != 200:
            auth_logger.error(f"Failed to get user info: {user_response.text}")
            flash('Failed to get user information from Discord')
            return redirect(url_for('shop.index'))
        
        user_data = user_response.json()
        auth_logger.debug(f"User data: {user_data}")
        
        # Verify the Discord user ID is valid
        if not user_data.get('id'):
            flash('Invalid Discord user data received')
            return redirect(url_for('shop.index'))
        
        # Additional validation: Re-request user info to verify token
        verify_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=headers)
        if verify_response.status_code != 200 or verify_response.json().get('id') != user_data['id']:
            flash('Authentication verification failed')
            return redirect(url_for('shop.index'))
        
        # Check admin status
        is_admin = check_discord_admin_status(user_data, access_token)
        
        # Create or update user
        user = create_or_update_user(user_data, is_admin)
        
        # Log in the user
        login_user(user)
        
        if is_admin:
            flash(f"Welcome, Admin {user.username}!")
        else:
            flash(f"Welcome, {user.username}!")
        
        return redirect(url_for('shop.index'))
        
    except Exception as e:
        auth_logger.error(f"Error in OAuth callback: {str(e)}")
        import traceback
        auth_logger.error(traceback.format_exc())
        flash(f'Authentication error: {str(e)}')
        return redirect(url_for('shop.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out successfully')
    return redirect(url_for('shop.index')) 