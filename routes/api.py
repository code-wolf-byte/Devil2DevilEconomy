from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from shared import (
    db,
    bot,
    User,
    Product,
    Purchase,
    UserAchievement,
    DownloadToken,
    ProductMedia,
)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import asyncio

api = Blueprint('api', __name__, url_prefix='/api')

PURCHASES_DISABLED = os.getenv('PURCHASES_DISABLED', 'false').lower() in {'1', 'true', 'yes'}


def _json_response(payload, status=200):
    response = jsonify(payload)
    response.status_code = status
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@api.route('/store')
def store():
    """Store data API for React client."""
    products = Product.query.filter(
        Product.is_active == True,
        (Product.stock.is_(None)) | (Product.stock > 0)
    ).all()

    store_products = []
    for product in products:
        image_url = None
        display_image = product.display_image or product.image_url
        if display_image:
            if str(display_image).startswith("http"):
                image_url = display_image
            else:
                image_url = url_for('static', filename=f"uploads/{display_image}", _external=True)

        store_products.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_unlimited': product.stock is None,
            'in_stock': product.stock is None or product.stock > 0,
            'product_type': product.product_type,
            'image_url': image_url
        })

    return _json_response({'products': store_products})


@api.route('/product/<int:product_id>')
def product_details_api(product_id):
    """Product details API for React client."""
    product = Product.query.get_or_404(product_id)

    image_url = None
    if product.display_image:
        if product.display_image.startswith("http"):
            image_url = product.display_image
        else:
            image_url = url_for('static', filename=f"uploads/{product.display_image}", _external=True)

    media_items = []
    for media in product.media:
        media_url = media.url
        if media_url and not media_url.startswith("http") and not media_url.startswith("/"):
            media_url = url_for('static', filename=f"uploads/{media_url}", _external=True)
        media_items.append({
            'id': media.id,
            'type': media.media_type,
            'url': media_url,
            'alt_text': media.alt_text,
            'sort_order': media.sort_order,
            'is_primary': media.is_primary
        })

    if not media_items and image_url:
        media_items.append({
            'id': None,
            'type': 'image',
            'url': image_url,
            'alt_text': product.name,
            'sort_order': 0,
            'is_primary': True
        })

    product_data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'is_unlimited': product.stock is None,
        'in_stock': product.stock is None or product.stock > 0,
        'product_type': product.product_type,
        'image_url': image_url,
        'media': media_items
    }

    return _json_response({'product': product_data})


@api.route('/me')
def current_user_api():
    """Return current user session info for the React client."""
    if current_user.is_authenticated:
        is_admin = current_user.is_admin
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            try:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    member = guild.get_member(int(current_user.id))
                    if member and member.guild_permissions.administrator:
                        is_admin = True
                        if not current_user.is_admin:
                            current_user.is_admin = True
                            db.session.commit()
            except Exception:
                pass

        payload = {
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'avatar_url': current_user.avatar_url,
                'balance': current_user.balance,
                'is_admin': is_admin
            }
        }
    else:
        payload = {'authenticated': False, 'user': None}

    return _json_response(payload)


@api.route('/dashboard')
@login_required
def dashboard_api():
    """Admin dashboard data API for React client."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    achievements = [ua.achievement for ua in user_achievements]

    recent_purchases = (
        Purchase.query.filter_by(user_id=current_user.id)
        .order_by(Purchase.timestamp.desc())
        .limit(5)
        .all()
    )

    purchase_tokens = {}
    for purchase in recent_purchases:
        if purchase.product.product_type == 'minecraft_skin':
            token = DownloadToken.query.filter_by(
                purchase_id=purchase.id,
                user_id=current_user.id
            ).first()
            if token and token.expires_at > datetime.utcnow():
                purchase_tokens[purchase.id] = token

    recent_payload = []
    for purchase in recent_purchases:
        display_image = purchase.product.display_image or purchase.product.image_url
        image_url = None
        if display_image:
            if str(display_image).startswith("http"):
                image_url = display_image
            else:
                image_url = url_for(
                    'static',
                    filename=f"uploads/{display_image}",
                    _external=True
                )

        token = purchase_tokens.get(purchase.id)
        download_url = None
        if token:
            download_url = url_for(
                'main.download_file',
                token=token.token,
                _external=True
            )

        recent_payload.append({
            'id': purchase.id,
            'product_id': purchase.product_id,
            'product_name': purchase.product.name,
            'product_type': purchase.product.product_type,
            'points_spent': purchase.points_spent,
            'timestamp': purchase.timestamp.isoformat(),
            'image_url': image_url,
            'download_url': download_url
        })

    payload = {
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'avatar_url': current_user.avatar_url,
            'balance': current_user.balance,
            'points': current_user.points,
            'message_count': current_user.message_count,
            'voice_minutes': current_user.voice_minutes,
            'is_admin': True
        },
        'achievements': [
            {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'points': achievement.points,
                'type': achievement.type,
                'requirement': achievement.requirement
            }
            for achievement in achievements
        ],
        'recent_purchases': recent_payload
    }

    return _json_response(payload)


@api.route('/admin/products')
@login_required
def admin_products_api():
    """Admin products list API."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    products = Product.query.order_by(Product.created_at.desc()).all()
    payload = []
    for product in products:
        display_image = product.display_image or product.image_url
        image_url = None
        if display_image:
            if str(display_image).startswith("http"):
                image_url = display_image
            else:
                image_url = url_for(
                    'static',
                    filename=f"uploads/{display_image}",
                    _external=True
                )

        preview_image_url = None
        if product.preview_image_url:
            if str(product.preview_image_url).startswith("http"):
                preview_image_url = product.preview_image_url
            else:
                preview_image_url = url_for(
                    'static',
                    filename=f"uploads/{product.preview_image_url}",
                    _external=True
                )

        payload.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_active': product.is_active,
            'product_type': product.product_type,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'image_url': image_url,
            'preview_image_url': preview_image_url,
            'download_file_url': product.download_file_url
        })

    return _json_response({'products': payload})


@api.route('/admin/products/<int:product_id>')
@login_required
def admin_product_detail_api(product_id):
    """Admin product detail API."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    product = Product.query.get_or_404(product_id)
    display_image = product.display_image or product.image_url
    image_url = None
    if display_image:
        if str(display_image).startswith("http"):
            image_url = display_image
        else:
            image_url = url_for(
                'static',
                filename=f"uploads/{display_image}",
                _external=True
            )

    preview_image_url = None
    if product.preview_image_url:
        if str(product.preview_image_url).startswith("http"):
            preview_image_url = product.preview_image_url
        else:
            preview_image_url = url_for(
                'static',
                filename=f"uploads/{product.preview_image_url}",
                _external=True
            )

    media_payload = []
    for media in product.media:
        media_url = media.url
        if media_url and not media_url.startswith("http") and not media_url.startswith("/"):
            media_url = url_for('static', filename=f"uploads/{media_url}", _external=True)
        media_payload.append({
            'id': media.id,
            'type': media.media_type,
            'url': media_url,
            'alt_text': media.alt_text,
            'sort_order': media.sort_order,
            'is_primary': media.is_primary
        })

    return _json_response({
        'product': {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_active': product.is_active,
            'product_type': product.product_type,
            'image_url': image_url,
            'preview_image_url': preview_image_url,
            'download_file_url': product.download_file_url,
            'media': media_payload
        }
    })


@api.route('/admin/products', methods=['POST'])
@login_required
def admin_product_create_api():
    """Admin product create API."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    name = request.form.get('name')
    description = request.form.get('description')
    price = int(request.form.get('price')) if request.form.get('price') else 0
    stock = request.form.get('stock')
    product_type = request.form.get('product_type', 'physical')

    if stock == '' or stock == 'unlimited':
        stock = None
    else:
        stock = int(stock) if stock is not None and stock != '' else None

    image_url = None
    preview_image_url = None
    download_file_url = None

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            image_url = os.path.basename(unique_filename)

    if 'preview_image' in request.files:
        file = request.files['preview_image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            preview_image_url = os.path.basename(unique_filename)

    if 'download_file' in request.files:
        file = request.files['download_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            download_file_url = os.path.basename(unique_filename)

    gallery_files = request.files.getlist('gallery_images')
    media_items = []
    for file in gallery_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            media_items.append(ProductMedia(
                media_type='image',
                url=os.path.basename(unique_filename)
            ))

    preview_video_url = request.form.get('preview_video_url')
    if preview_video_url:
        media_items.append(ProductMedia(
            media_type='video',
            url=preview_video_url
        ))

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

    if media_items:
        has_primary = any(item.media_type == 'image' and item.is_primary for item in media_items)
        if not has_primary:
            for item in media_items:
                if item.media_type == 'image':
                    item.is_primary = True
                    break
        for item in media_items:
            item.product_id = product.id
            db.session.add(item)
        db.session.commit()

    return _json_response({'ok': True, 'product_id': product.id})


@api.route('/admin/products/<int:product_id>', methods=['POST'])
@login_required
def admin_product_update_api(product_id):
    """Admin product update API."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    product = Product.query.get_or_404(product_id)

    product.name = request.form.get('name')
    product.description = request.form.get('description')
    product.price = int(request.form.get('price')) if request.form.get('price') else 0
    stock = request.form.get('stock')
    product.product_type = request.form.get('product_type', 'physical')

    if stock == '' or stock == 'unlimited':
        product.stock = None
    else:
        product.stock = int(stock) if stock is not None and stock != '' else None

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            product.image_url = os.path.basename(unique_filename)

    if 'preview_image' in request.files:
        file = request.files['preview_image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            product.preview_image_url = os.path.basename(unique_filename)

    if 'download_file' in request.files:
        file = request.files['download_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            product.download_file_url = os.path.basename(unique_filename)

    gallery_files = request.files.getlist('gallery_images')
    new_media = []
    for file in gallery_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            new_media.append(ProductMedia(
                product_id=product.id,
                media_type='image',
                url=os.path.basename(unique_filename)
            ))

    preview_video_url = request.form.get('preview_video_url')
    if preview_video_url:
        new_media.append(ProductMedia(
            product_id=product.id,
            media_type='video',
            url=preview_video_url
        ))

    db.session.commit()

    if new_media:
        has_primary = any(
            media.media_type == 'image' and media.is_primary for media in product.media
        )
        if not has_primary:
            for item in new_media:
                if item.media_type == 'image':
                    item.is_primary = True
                    break
        for item in new_media:
            db.session.add(item)
        db.session.commit()

    return _json_response({'ok': True})


@api.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase_api(product_id):
    """Purchase a product via API."""
    if PURCHASES_DISABLED:
        return _json_response(
            {'error': 'purchases_disabled', 'message': 'Purchases are currently closed.'},
            status=403
        )

    product = Product.query.get_or_404(product_id)

    if not product.is_active:
        return _json_response(
            {'error': 'inactive', 'message': 'This product is no longer available.'},
            status=400
        )

    if product.stock is not None and product.stock <= 0:
        return _json_response(
            {'error': 'out_of_stock', 'message': 'This product is out of stock.'},
            status=400
        )

    discounted_price = int(product.price * 0.8)

    if current_user.balance < discounted_price:
        return _json_response(
            {'error': 'insufficient_balance', 'message': 'Insufficient balance.'},
            status=400
        )

    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        points_spent=discounted_price,
        timestamp=datetime.utcnow()
    )

    current_user.balance -= discounted_price

    if product.stock is not None:
        product.stock -= 1

    db.session.add(purchase)
    db.session.commit()

    try:
        from shared import bot
        if bot.is_ready():
            economy_cog = bot.get_cog('EconomyCog')
            if economy_cog:
                future = asyncio.run_coroutine_threadsafe(
                    economy_cog.send_purchase_notification(
                        current_user, product, discounted_price, purchase.id
                    ),
                    bot.loop
                )
                try:
                    future.result(timeout=2)
                except Exception:
                    pass
    except Exception as e:
        print(f"Warning: Could not send Discord purchase notification: {e}")

    download_url = None
    delivery_status = 'completed'
    message = f'Successfully purchased {product.name}!'

    if product.product_type == 'minecraft_skin' and product.download_file_url:
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)
        download_token = DownloadToken(
            token=token,
            user_id=current_user.id,
            purchase_id=purchase.id,
            file_path=product.download_file_url,
            expires_at=expires_at
        )
        db.session.add(download_token)
        db.session.commit()
        purchase.delivery_info = f"Download token created: {token}"
        db.session.commit()
        download_url = url_for('main.download_file', token=token, _external=True)
        message = f'Successfully purchased {product.name}! Your download is now available.'
    elif product.product_type == 'role' and product.delivery_method == 'auto_role':
        try:
            import json
            from shared import bot
            delivery_config = json.loads(product.delivery_data) if product.delivery_data else {}
            role_id = delivery_config.get('role_id')
            if role_id and bot.is_ready():
                economy_cog = bot.get_cog('EconomyCog')
                if economy_cog:
                    future = asyncio.run_coroutine_threadsafe(
                        economy_cog.assign_role_to_user(current_user.id, role_id, purchase.id),
                        bot.loop
                    )
                    success, role_message = future.result(timeout=10)
                    if success:
                        purchase.delivery_info = f"Role assigned successfully: {role_message}"
                        purchase.status = 'completed'
                        message = f'Successfully purchased {product.name}! Your Discord role has been assigned.'
                    else:
                        purchase.delivery_info = f"Role assignment failed: {role_message}"
                        purchase.status = 'failed'
                        delivery_status = 'failed'
                        message = f'Purchase successful, but role assignment failed: {role_message}'
                else:
                    purchase.delivery_info = "Economy cog not found"
                    purchase.status = 'failed'
                    delivery_status = 'failed'
                    message = 'Purchase successful, but Discord bot is not properly configured.'
            elif not bot.is_ready():
                purchase.delivery_info = "Discord bot not ready"
                purchase.status = 'pending'
                delivery_status = 'pending'
                message = 'Purchase successful! Discord bot is starting up - role will be assigned shortly.'
            else:
                purchase.delivery_info = "No role ID configured"
                purchase.status = 'failed'
                delivery_status = 'failed'
                message = 'Purchase successful! Please contact an admin for role assignment.'
            db.session.commit()
        except asyncio.TimeoutError:
            purchase.delivery_info = "Role assignment timed out"
            purchase.status = 'failed'
            delivery_status = 'failed'
            db.session.commit()
            message = 'Purchase successful, but role assignment timed out.'
        except Exception as e:
            purchase.delivery_info = f"Role assignment error: {str(e)}"
            purchase.status = 'failed'
            delivery_status = 'failed'
            db.session.commit()
            message = 'Purchase successful, but role assignment failed.'

    return _json_response({
        'ok': True,
        'purchase_id': purchase.id,
        'new_balance': current_user.balance,
        'download_url': download_url,
        'status': delivery_status,
        'message': message
    })


@api.route('/leaderboard')
def leaderboard_api():
    """Leaderboard data API."""
    users = User.query.order_by(User.balance.desc()).limit(10).all()
    payload = [
        {
            'id': user.id,
            'username': user.username,
            'avatar_url': user.avatar_url,
            'points': user.points,
            'balance': user.balance
        }
        for user in users
    ]
    totals = {
        'total_users': len(payload),
        'total_balance': sum(user['balance'] or 0 for user in payload),
        'total_points': sum(user['points'] or 0 for user in payload)
    }
    return _json_response({'users': payload, 'totals': totals})


@api.route('/my-purchases')
@login_required
def my_purchases_api():
    """Current user's purchase history API."""
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(
        Purchase.timestamp.desc()
    ).all()

    purchase_tokens = {}
    for purchase in purchases:
        if purchase.product.product_type == 'minecraft_skin':
            token = DownloadToken.query.filter_by(
                purchase_id=purchase.id,
                user_id=current_user.id
            ).first()
            if token and token.expires_at > datetime.utcnow():
                purchase_tokens[purchase.id] = token

    payload = []
    for purchase in purchases:
        display_image = purchase.product.display_image or purchase.product.image_url
        image_url = None
        if display_image:
            if str(display_image).startswith("http"):
                image_url = display_image
            else:
                image_url = url_for(
                    'static',
                    filename=f"uploads/{display_image}",
                    _external=True
                )

        token = purchase_tokens.get(purchase.id)
        download_url = None
        if token:
            download_url = url_for(
                'main.download_file',
                token=token.token,
                _external=True
            )

        payload.append({
            'id': purchase.id,
            'product_id': purchase.product_id,
            'product_name': purchase.product.name,
            'product_description': purchase.product.description,
            'product_type': purchase.product.product_type,
            'points_spent': purchase.points_spent,
            'timestamp': purchase.timestamp.isoformat(),
            'image_url': image_url,
            'download_url': download_url
        })

    return _json_response({'purchases': payload})
