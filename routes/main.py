from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from shared import db, User, Product, Purchase, Achievement, UserAchievement, EconomySettings, DownloadToken
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import time

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page"""
    # Get only active products that are not out of stock
    # Show products that are either unlimited (stock=None) or have stock available (stock>0)
    products = Product.query.filter(
        Product.is_active == True,
        (Product.stock.is_(None)) | (Product.stock > 0)
    ).all()
    
    return render_template('index.html', products=products)

@main.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's achievements
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    achievements = [ua.achievement for ua in user_achievements]
    
    # Get recent purchases
    recent_purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.timestamp.desc()).limit(5).all()
    
    # Get download tokens for recent purchases
    purchase_tokens = {}
    for purchase in recent_purchases:
        if purchase.product.product_type == 'minecraft_skin':
            token = DownloadToken.query.filter_by(
                purchase_id=purchase.id, 
                user_id=current_user.id
            ).first()
            if token and token.expires_at > datetime.utcnow():
                purchase_tokens[purchase.id] = token
    
    return render_template('dashboard.html', 
                         user=current_user, 
                         achievements=achievements,
                         recent_purchases=recent_purchases,
                         purchase_tokens=purchase_tokens)

@main.route('/shop')
@login_required
def shop():
    """Shop page"""
    return redirect(url_for('main.index'))

@main.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase_product(product_id):
    """Purchase a product"""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        flash('This product is no longer available.', 'error')
        return redirect(url_for('main.shop'))
    
    if product.stock is not None and product.stock <= 0:
        flash('This product is out of stock.', 'error')
        return redirect(url_for('main.shop'))
    
    if current_user.balance < product.price:
        flash('Insufficient balance to purchase this item.', 'error')
        return redirect(url_for('main.shop'))
    
    # Create purchase
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        points_spent=product.price,
        timestamp=datetime.utcnow()
    )
    
    # Update user balance
    current_user.balance -= product.price
    
    # Update product stock
    if product.stock is not None:
        product.stock -= 1
    
    db.session.add(purchase)
    db.session.commit()
    
    # Handle digital product delivery
    if product.product_type == 'minecraft_skin' and product.download_file_url:
        # Create download token for minecraft skin
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)  # Token expires in 30 days
        
        download_token = DownloadToken(
            token=token,
            user_id=current_user.id,
            purchase_id=purchase.id,
            file_path=product.download_file_url,
            expires_at=expires_at
        )
        
        db.session.add(download_token)
        db.session.commit()
        
        # Update purchase with delivery info
        purchase.delivery_info = f"Download token created: {token}"
        db.session.commit()
        
        flash(f'Successfully purchased {product.name}! Your download is now available.', 'success')
    else:
        flash(f'Successfully purchased {product.name}!', 'success')
    
    return redirect(url_for('main.dashboard'))

@main.route('/admin/create-missing-download-tokens')
@login_required
def create_missing_download_tokens():
    """Create download tokens for existing minecraft skin purchases that don't have them"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Find all minecraft skin purchases without download tokens
        minecraft_purchases = db.session.query(Purchase).join(Product).filter(
            Product.product_type == 'minecraft_skin',
            Product.download_file_url.isnot(None)
        ).all()
        
        created_count = 0
        for purchase in minecraft_purchases:
            # Check if token already exists
            existing_token = DownloadToken.query.filter_by(purchase_id=purchase.id).first()
            if not existing_token:
                # Create new token
                token = str(uuid.uuid4())
                expires_at = datetime.utcnow() + timedelta(days=30)
                
                download_token = DownloadToken(
                    token=token,
                    user_id=purchase.user_id,
                    purchase_id=purchase.id,
                    file_path=purchase.product.download_file_url,
                    expires_at=expires_at
                )
                
                db.session.add(download_token)
                
                # Update purchase with delivery info if not already set
                if not purchase.delivery_info:
                    purchase.delivery_info = f"Download token created: {token}"
                
                created_count += 1
        
        db.session.commit()
        flash(f'Successfully created {created_count} download tokens for existing purchases!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating download tokens: {str(e)}', 'error')
    
    return redirect(url_for('main.admin'))

@main.route('/download/<token>')
@login_required
def download_file(token):
    """Download a digital product using a secure token"""
    download_token = DownloadToken.query.filter_by(token=token).first()
    
    if not download_token:
        flash('Invalid download token.', 'error')
        abort(404)
    
    # Check if token has expired
    if download_token.expires_at < datetime.utcnow():
        flash('Download token has expired.', 'error')
        abort(404)
    
    # Check if user owns this token
    if download_token.user_id != current_user.id:
        flash('Access denied.', 'error')
        abort(403)
    
    # Update download count
    download_token.download_count += 1
    download_token.downloaded = True
    db.session.commit()
    
    # Serve the file
    try:
        file_path = os.path.join('static', 'uploads', download_token.file_path)
        if os.path.exists(file_path):
            return send_from_directory('static/uploads', download_token.file_path, as_attachment=True)
        else:
            flash('File not found.', 'error')
            abort(404)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        abort(500)

@main.route('/admin')
@login_required
def admin():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_purchases = Purchase.query.count()
    
    # Get all products for the dashboard
    products = Product.query.order_by(Product.created_at.desc()).all()
    
    # Get recent purchases
    recent_purchases = Purchase.query.order_by(Purchase.timestamp.desc()).limit(10).all()
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_purchases=total_purchases,
                         products=products,
                         recent_purchases=recent_purchases)

@main.route('/admin/products')
@login_required
def admin_products():
    """Admin products management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@main.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = int(request.form.get('price'))
        stock = request.form.get('stock')
        product_type = request.form.get('product_type', 'physical')
        
        # Handle stock
        if stock == '' or stock == 'unlimited':
            stock = None
        else:
            stock = int(stock)
        
        # Handle file uploads
        image_url = None
        preview_image_url = None
        download_file_url = None
        
        # Regular image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                image_url = os.path.basename(unique_filename)
        
        # Minecraft skin preview image
        if 'preview_image' in request.files:
            file = request.files['preview_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                preview_image_url = os.path.basename(unique_filename)
        
        # Minecraft skin download file
        if 'download_file' in request.files:
            file = request.files['download_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                download_file_url = os.path.basename(unique_filename)
        
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image_url=image_url,
            product_type=product_type,
            preview_image_url=preview_image_url,
            download_file_url=download_file_url,
            created_at=datetime.utcnow()
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('main.admin_products'))
    
    return render_template('add_product.html')

@main.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = int(request.form.get('price'))
        stock = request.form.get('stock')
        product.product_type = request.form.get('product_type', 'physical')
        
        # Handle stock
        if stock == '' or stock == 'unlimited':
            product.stock = None
        else:
            product.stock = int(stock)
        
        # Handle file uploads
        # Regular image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                product.image_url = os.path.basename(unique_filename)
        
        # Minecraft skin preview image
        if 'preview_image' in request.files:
            file = request.files['preview_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                product.preview_image_url = os.path.basename(unique_filename)
        
        # Minecraft skin download file
        if 'download_file' in request.files:
            file = request.files['download_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                product.download_file_url = os.path.basename(unique_filename)
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('main.admin_products'))
    
    return render_template('edit_product.html', product=product)

@main.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    product.archived_at = datetime.utcnow()
    db.session.commit()
    
    flash('Product archived successfully!', 'success')
    return redirect(url_for('main.admin_products'))

@main.route('/admin/products/restore/<int:product_id>', methods=['POST'])
@login_required
def restore_product(product_id):
    """Restore archived product"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    product = Product.query.get_or_404(product_id)
    product.is_active = True
    product.archived_at = None
    db.session.commit()
    
    flash('Product restored successfully!', 'success')
    return redirect(url_for('main.admin_products'))

@main.route('/admin/purchases')
@login_required
def admin_purchases():
    """Admin purchases view"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    pagination = Purchase.query.order_by(Purchase.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin_purchases.html', pagination=pagination)

@main.route('/leaderboard')
def leaderboard():
    """Leaderboard page"""
    top_users = User.query.order_by(User.balance.desc()).limit(10).all()
    return render_template('leaderboard.html', users=top_users)

@main.route('/how-to-earn')
def how_to_earn():
    """How to earn pitchforks page"""
    return render_template('how_to_earn.html')

@main.route('/my-purchases')
@login_required
def my_purchases():
    """User's purchase history"""
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.timestamp.desc()).all()
    
    # Get download tokens for each purchase
    purchase_tokens = {}
    for purchase in purchases:
        if purchase.product.product_type == 'minecraft_skin':
            token = DownloadToken.query.filter_by(
                purchase_id=purchase.id, 
                user_id=current_user.id
            ).first()
            if token and token.expires_at > datetime.utcnow():
                purchase_tokens[purchase.id] = token
    
    return render_template('my_purchases.html', purchases=purchases, purchase_tokens=purchase_tokens)

@main.route('/new_product', methods=['GET', 'POST'])
@login_required
def new_product():
    """Add new product (alias for add_product)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = int(request.form.get('price'))
        stock = request.form.get('stock')
        product_type = request.form.get('product_type', 'physical')
        
        # Handle stock
        if stock == '' or stock == 'unlimited':
            stock = None
        else:
            stock = int(stock)
        
        # Handle file uploads
        image_url = None
        preview_image_url = None
        download_file_url = None
        
        # Regular image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                image_url = os.path.basename(unique_filename)
        
        # Minecraft skin preview image
        if 'preview_image' in request.files:
            file = request.files['preview_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                preview_image_url = os.path.basename(unique_filename)
        
        # Minecraft skin download file
        if 'download_file' in request.files:
            file = request.files['download_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join('static', 'uploads', unique_filename)
                file.save(file_path)
                download_file_url = os.path.basename(unique_filename)
        
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image_url=image_url,
            product_type=product_type,
            preview_image_url=preview_image_url,
            download_file_url=download_file_url,
            created_at=datetime.utcnow()
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('main.admin_products'))
    
    return render_template('new_product.html')

@main.route('/digital_templates')
@login_required
def digital_templates():
    """Digital templates page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('digital_templates.html')

@main.route('/file_manager')
@login_required
def file_manager():
    """File manager page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('file_manager.html')

@main.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """Upload file endpoint"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Basic file upload logic
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            flash('File uploaded successfully!', 'success')
        else:
            flash('No file selected.', 'error')
    else:
        flash('No file provided.', 'error')
    
    return redirect(url_for('main.file_manager'))

@main.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    """Delete file endpoint"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Basic file deletion logic
    filename = request.form.get('filename')
    if filename:
        try:
            file_path = os.path.join('static', 'uploads', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash('File deleted successfully!', 'success')
            else:
                flash('File not found.', 'error')
        except Exception as e:
            flash(f'Error deleting file: {str(e)}', 'error')
    else:
        flash('No filename provided.', 'error')
    
    return redirect(url_for('main.file_manager'))

@main.route('/create_role_product', methods=['POST'])
@login_required
def create_role_product():
    """Create role product endpoint"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Basic role product creation logic
    name = request.form.get('name')
    description = request.form.get('description')
    price = int(request.form.get('price'))
    role_id = request.form.get('role_id')
    
    product = Product(
        name=name,
        description=description,
        price=price,
        product_type='role',
        delivery_method='auto_role',
        delivery_data=f'{{"role_id": "{role_id}"}}',
        created_at=datetime.utcnow()
    )
    
    db.session.add(product)
    db.session.commit()
    
    flash('Role product created successfully!', 'success')
    return redirect(url_for('main.admin_products'))

@main.route('/economy_config')
@login_required
def economy_config():
    """Economy configuration page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Fetch the settings from the database
    settings = EconomySettings.query.first()
    
    return render_template('economy_config.html', settings=settings)

@main.route('/admin/get-discord-roles')
@login_required
def get_discord_roles():
    """Get Discord roles for admin interface"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Import the bot from shared to access guild roles
        from shared import bot
        import time
        
        # Wait for bot to be ready (with timeout)
        max_wait = 10  # seconds
        wait_time = 0
        while not bot.is_ready() and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
        
        if not bot.is_ready():
            return jsonify({'error': 'Discord bot is not ready. Please try again in a few moments.'}), 503
        
        # Get the first guild (server) the bot is in
        guild = None
        for g in bot.guilds:
            guild = g
            break
        
        if not guild:
            return jsonify({'error': 'Bot is not in any Discord server'}), 404
        
        # Get all roles that the bot can manage
        roles = []
        for role in guild.roles:
            # Skip @everyone role and roles higher than bot's top role
            if role.name == '@everyone':
                continue
            
            # Check if bot can manage this role
            if guild.me.top_role > role:
                roles.append({
                    'id': str(role.id),
                    'name': role.name,
                    'color': f'#{role.color.value:06x}',
                    'position': role.position,
                    'mentionable': role.mentionable,
                    'hoist': role.hoist
                })
        
        # Sort by position (highest first)
        roles.sort(key=lambda x: x['position'], reverse=True)
        
        return jsonify({'roles': roles})
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch Discord roles: {str(e)}'}), 500

@main.route('/admin/get-role-products')
@login_required
def get_role_products():
    """Get existing role products"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        role_products = Product.query.filter_by(product_type='role').all()
        products = []
        
        for product in role_products:
            products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'is_active': product.is_active,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'delivery_data': product.delivery_data
            })
        
        return jsonify({'products': products})
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch role products: {str(e)}'}), 500

@main.route('/admin/get-minecraft-skin-products')
@login_required
def get_minecraft_skin_products():
    """Get existing minecraft skin products"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        skin_products = Product.query.filter_by(product_type='minecraft_skin').all()
        products = []
        
        for product in skin_products:
            products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'is_active': product.is_active,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'preview_image_url': product.preview_image_url,
                'download_file_url': product.download_file_url
            })
        
        return jsonify({'products': products})
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch minecraft skin products: {str(e)}'}), 500

@main.route('/admin_leaderboard')
@login_required
def admin_leaderboard():
    """Admin leaderboard page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get page parameter for pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of users per page
    
    # Get basic statistics
    total_users = User.query.count()
    total_balance = sum(user.balance or 0 for user in User.query.all())
    total_purchases = Purchase.query.count()
    total_spent = sum(purchase.points_spent for purchase in Purchase.query.all())
    total_achievements = UserAchievement.query.count()
    average_balance = total_balance // total_users if total_users > 0 else 0
    
    economy_stats = {
        'total_users': total_users,
        'total_balance': total_balance,
        'total_spent': total_spent,
        'total_purchases': total_purchases,
        'total_achievements': total_achievements,
        'average_balance': average_balance
    }
    
    # Get paginated users
    pagination = User.query.order_by(User.balance.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get users with their stats for the current page
    leaderboard_stats = []
    
    for i, user in enumerate(pagination.items, (page - 1) * per_page + 1):
        user_purchases = Purchase.query.filter_by(user_id=user.id).all()
        user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
        total_spent = sum(p.points_spent for p in user_purchases)
        activity_score = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)
        
        leaderboard_stats.append({
            'rank': i,
            'user': user,
            'total_spent': total_spent,
            'purchase_count': len(user_purchases),
            'achievement_count': len(user_achievements),
            'activity_score': activity_score
        })
    
    # Get top spenders (from all users, not just current page)
    all_users = User.query.all()
    all_leaderboard_stats = []
    
    for i, user in enumerate(all_users, 1):
        user_purchases = Purchase.query.filter_by(user_id=user.id).all()
        user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
        total_spent = sum(p.points_spent for p in user_purchases)
        activity_score = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)
        
        all_leaderboard_stats.append({
            'rank': i,
            'user': user,
            'total_spent': total_spent,
            'purchase_count': len(user_purchases),
            'achievement_count': len(user_achievements),
            'activity_score': activity_score
        })
    
    # Get top spenders
    top_spenders = sorted(all_leaderboard_stats, key=lambda x: x['total_spent'], reverse=True)[:10]
    
    # Get most active users
    most_active = sorted(all_leaderboard_stats, key=lambda x: x['activity_score'], reverse=True)[:10]
    
    return render_template('admin_leaderboard.html', 
                         economy_stats=economy_stats,
                         leaderboard_stats=leaderboard_stats,
                         top_spenders=top_spenders,
                         most_active=most_active,
                         pagination=pagination)

@main.route('/admin/user/<user_id>')
@login_required
def admin_user_detail(user_id):
    """Detailed user profile page for admins"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the user
    user = User.query.get_or_404(user_id)
    
    # Get user's purchases
    purchases = Purchase.query.filter_by(user_id=user.id).order_by(Purchase.timestamp.desc()).all()
    
    # Get user's achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    achievements = [ua.achievement for ua in user_achievements]
    
    # Calculate detailed statistics
    total_spent = sum(p.points_spent for p in purchases)
    total_earned = (user.balance or 0) + total_spent
    activity_score = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)
    
    # Get recent activity (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_purchases = [p for p in purchases if p.timestamp >= thirty_days_ago]
    recent_achievements = [ua for ua in user_achievements if ua.achieved_at >= thirty_days_ago]
    
    # Calculate earning breakdown
    earning_breakdown = {
        'messages': user.message_count or 0,
        'reactions': user.reaction_count or 0,
        'voice_minutes': user.voice_minutes or 0,
        'daily_claims': user.daily_claims_count or 0,
        'campus_photos': user.campus_photos_count or 0,
        'daily_engagement': user.daily_engagement_count or 0,
        'achievements': sum(achievement.points for achievement in achievements),
        'verification_bonus': 200 if user.verification_bonus_received else 0,
        'onboarding_bonus': 500 if user.onboarding_bonus_received else 0,
        'enrollment_deposit': 1000 if user.enrollment_deposit_received else 0,
        'birthday_bonus': 100 if user.birthday_points_received else 0,
        'boost_bonus': 500 if user.has_boosted else 0
    }
    
    # Calculate spending breakdown by product type
    spending_breakdown = {}
    for purchase in purchases:
        product_type = purchase.product.product_type if purchase.product else 'unknown'
        if product_type not in spending_breakdown:
            spending_breakdown[product_type] = 0
        spending_breakdown[product_type] += purchase.points_spent
    
    # Get user's rank
    all_users = User.query.order_by(User.balance.desc()).all()
    user_rank = None
    for i, u in enumerate(all_users, 1):
        if u.id == user.id:
            user_rank = i
            break
    
    return render_template('admin_user_detail.html',
                         user=user,
                         purchases=purchases,
                         achievements=achievements,
                         total_spent=total_spent,
                         total_earned=total_earned,
                         activity_score=activity_score,
                         recent_purchases=recent_purchases,
                         recent_achievements=recent_achievements,
                         earning_breakdown=earning_breakdown,
                         spending_breakdown=spending_breakdown,
                         user_rank=user_rank) 