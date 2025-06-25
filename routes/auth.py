from flask import Blueprint, redirect, request, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from shared import app, db, User
import requests
import os
import uuid
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    """Redirect to Discord OAuth"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Discord OAuth URL
    client_id = os.getenv('DISCORD_CLIENT_ID')
    redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
    scope = 'identify'
    
    oauth_url = f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}'
    return redirect(oauth_url)

def handle_callback():
    """Handle Discord OAuth callback logic"""
    code = request.args.get('code')
    if not code:
        flash('Authentication failed. No authorization code received.', 'error')
        return redirect(url_for('auth.login'))
    
    # Exchange code for token
    client_id = os.getenv('DISCORD_CLIENT_ID')
    client_secret = os.getenv('DISCORD_CLIENT_SECRET')
    redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
    
    # Check if environment variables are set
    if not client_id or not client_secret or not redirect_uri:
        flash('Server configuration error. Please contact an administrator.', 'error')
        return redirect(url_for('main.index'))
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
        
        if response.status_code != 200:
            flash(f'Authentication failed. Discord API error: {response.status_code}', 'error')
            return redirect(url_for('auth.login'))
        
        token_data = response.json()
        access_token = token_data['access_token']
        
        # Get user info from Discord
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get('https://discord.com/api/users/@me', headers=headers)
        
        if user_response.status_code != 200:
            flash('Failed to get user information from Discord.', 'error')
            return redirect(url_for('auth.login'))
        
        user_data = user_response.json()
        discord_id = user_data['id']
        username = user_data['username']
        avatar = user_data.get('avatar')
        
        # Create avatar URL
        if avatar:
            avatar_url = f'https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png'
        else:
            avatar_url = 'https://cdn.discordapp.com/embed/avatars/0.png'
        
        # Check if user exists
        user = User.query.filter_by(discord_id=discord_id).first()
        
        if not user:
            # Create new user
            user = User(
                id=discord_id,
                username=username,
                discord_id=discord_id,
                avatar_url=avatar_url,
                user_uuid=str(uuid.uuid4()),
                points=0,
                balance=0,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        # Update user info
        user.username = username
        user.avatar_url = avatar_url
        db.session.commit()
        
        # Log in user
        login_user(user)
        
        flash('Successfully logged in!', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/callback')
def callback():
    """Handle Discord OAuth callback"""
    return handle_callback()

@auth.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('main.index')) 