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
    Category,
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
            'image_url': image_url,
            'category': product.category or 'general'
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
            'category': product.category or 'general',
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
            'category': product.category or 'general',
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
    category = request.form.get('category', 'general') or 'general'

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
        category=category,
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
    product.category = request.form.get('category', 'general') or 'general'

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


@api.route('/admin/products/<int:product_id>/media/<int:media_id>', methods=['DELETE'])
@login_required
def admin_product_delete_media_api(product_id, media_id):
    """Delete a media item from a product."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    media = ProductMedia.query.filter_by(id=media_id, product_id=product_id).first()
    if not media:
        return _json_response({'error': 'Media not found.'}, status=404)

    was_primary = media.is_primary
    media_url = media.url

    db.session.delete(media)
    db.session.commit()

    # Delete the file from disk if it's a local file
    if media_url and not media_url.startswith('http') and not media_url.startswith('/'):
        file_path = os.path.join('static', 'uploads', media_url)
        if os.path.exists(file_path):
            os.remove(file_path)

    # If the deleted media was primary, promote the next available image
    if was_primary:
        next_image = ProductMedia.query.filter_by(
            product_id=product_id, media_type='image'
        ).order_by(ProductMedia.sort_order).first()
        if next_image:
            next_image.is_primary = True
            db.session.commit()

    return _json_response({'ok': True})


@api.route('/admin/products/<int:product_id>/media/<int:media_id>/primary', methods=['POST'])
@login_required
def admin_product_set_primary_media_api(product_id, media_id):
    """Set a media item as the primary image for a product."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    media = ProductMedia.query.filter_by(id=media_id, product_id=product_id).first()
    if not media:
        return _json_response({'error': 'Media not found.'}, status=404)

    # Clear primary on all media for this product
    ProductMedia.query.filter_by(product_id=product_id).update({'is_primary': False})
    media.is_primary = True
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
    """Leaderboard data API. Admins are excluded."""
    users = (
        User.query
        .filter(User.is_admin == False)
        .order_by(User.balance.desc())
        .limit(10)
        .all()
    )
    payload = [
        {
            'id': user.id,
            'username': user.username,
            'avatar_url': user.avatar_url,
            'points': user.points or 0,
            'balance': user.balance or 0
        }
        for user in users
    ]
    # Community-wide totals (all non-admin users, not just the top 10)
    total_users = User.query.filter(User.is_admin == False).count()
    total_balance = db.session.query(db.func.sum(User.balance)).filter(User.is_admin == False).scalar() or 0
    total_points = db.session.query(db.func.sum(User.points)).filter(User.is_admin == False).scalar() or 0
    totals = {
        'total_users': total_users,
        'total_balance': total_balance,
        'total_points': total_points
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


# ============================================================================
# CONFIG PAGE APIs
# ============================================================================

@api.route('/admin/economy-config')
@login_required
def admin_economy_config_api():
    """Get economy configuration settings."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    from shared import EconomySettings
    settings = EconomySettings.query.first()

    if not settings:
        return _json_response({
            'settings': {
                'economy_enabled': False,
                'verified_role_id': None,
                'verified_bonus_points': 200,
                'onboarding_role_ids': [],
                'onboarding_bonus_points': 500,
                'roles_configured': False
            }
        })

    onboarding_roles = []
    if settings.onboarding_role_ids:
        try:
            import json
            onboarding_roles = json.loads(settings.onboarding_role_ids)
        except (json.JSONDecodeError, TypeError):
            onboarding_roles = []

    return _json_response({
        'settings': {
            'economy_enabled': settings.economy_enabled,
            'verified_role_id': settings.verified_role_id,
            'verified_bonus_points': settings.verified_bonus_points or 200,
            'onboarding_role_ids': onboarding_roles,
            'onboarding_bonus_points': settings.onboarding_bonus_points or 500,
            'roles_configured': settings.roles_configured
        }
    })


@api.route('/admin/economy-config', methods=['POST'])
@login_required
def admin_economy_config_save_api():
    """Save economy configuration settings."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    import json
    from shared import EconomySettings

    data = request.get_json() or {}
    action = data.get('action', 'save_config')

    settings = EconomySettings.query.first()
    if not settings:
        settings = EconomySettings()
        db.session.add(settings)

    settings.verified_role_id = data.get('verified_role_id')
    settings.verified_bonus_points = int(data.get('verified_bonus_points', 200))
    settings.onboarding_bonus_points = int(data.get('onboarding_bonus_points', 500))

    onboarding_roles = data.get('onboarding_role_ids', [])
    settings.onboarding_role_ids = json.dumps(onboarding_roles) if onboarding_roles else None
    settings.roles_configured = bool(settings.verified_role_id or onboarding_roles)

    if action == 'enable_economy':
        if not settings.roles_configured:
            return _json_response({'error': 'Please configure roles before enabling the economy.'}, status=400)
        settings.economy_enabled = True
        settings.enabled_at = datetime.utcnow()

    db.session.commit()

    return _json_response({'ok': True, 'message': 'Configuration saved successfully.'})


@api.route('/admin/discord-roles')
@login_required
def admin_discord_roles_api():
    """Get Discord roles for admin interface."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    try:
        from shared import bot
        import time

        max_wait = 10
        wait_time = 0
        while not bot.is_ready() and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5

        if not bot.is_ready():
            return _json_response({'error': 'Discord bot is not ready. Please try again.'}, status=503)

        guild_id = os.getenv('DISCORD_GUILD_ID')
        if not guild_id:
            return _json_response({'error': 'DISCORD_GUILD_ID not configured.'}, status=500)

        guild = bot.get_guild(int(guild_id))
        if not guild:
            return _json_response({'error': f'Bot is not in the configured Discord server.'}, status=404)

        roles = []
        for role in guild.roles:
            if role.name == '@everyone':
                continue
            if guild.me.top_role > role:
                roles.append({
                    'id': str(role.id),
                    'name': role.name,
                    'color': f'#{role.color.value:06x}',
                    'position': role.position
                })

        roles.sort(key=lambda x: x['position'], reverse=True)
        return _json_response({'roles': roles})

    except Exception as e:
        return _json_response({'error': f'Failed to fetch Discord roles: {str(e)}'}, status=500)


@api.route('/admin/files')
@login_required
def admin_files_api():
    """Get list of uploaded files."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    uploads_dir = os.path.join('static', 'uploads')
    if not os.path.exists(uploads_dir):
        return _json_response({'files': [], 'stats': {'total': 0, 'images': 0, 'archives': 0, 'documents': 0}})

    files = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.mcpack', '.mcworld', '.mcaddon'}
    document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md', '.json', '.xml'}

    for filename in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            ext = os.path.splitext(filename)[1].lower()
            files.append({
                'name': filename,
                'path': f'/static/uploads/{filename}',
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_image': ext in image_extensions,
                'is_archive': ext in archive_extensions,
                'is_document': ext in document_extensions
            })

    files.sort(key=lambda x: x['modified'], reverse=True)

    stats = {
        'total': len(files),
        'images': sum(1 for f in files if f['is_image']),
        'archives': sum(1 for f in files if f['is_archive']),
        'documents': sum(1 for f in files if f['is_document'])
    }

    return _json_response({'files': files, 'stats': stats})


@api.route('/admin/files', methods=['POST'])
@login_required
def admin_files_upload_api():
    """Upload a file."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    if 'file' not in request.files:
        return _json_response({'error': 'No file provided.'}, status=400)

    file = request.files['file']
    if not file or not file.filename:
        return _json_response({'error': 'No file selected.'}, status=400)

    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join('static', 'uploads', unique_filename)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    return _json_response({
        'ok': True,
        'file': {
            'name': unique_filename,
            'path': f'/static/uploads/{unique_filename}'
        }
    })


@api.route('/admin/files', methods=['DELETE'])
@login_required
def admin_files_delete_api():
    """Delete a file."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    data = request.get_json() or {}
    file_path = data.get('file_path', '')

    if not file_path:
        return _json_response({'error': 'No file path provided.'}, status=400)

    if file_path.startswith('/static/uploads/'):
        file_path = file_path[1:]
    elif file_path.startswith('static/uploads/'):
        pass
    else:
        return _json_response({'error': 'Invalid file path.'}, status=400)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        return _json_response({'ok': True, 'message': 'File deleted successfully.'})
    else:
        return _json_response({'error': 'File not found.'}, status=404)


@api.route('/admin/digital-templates/roles')
@login_required
def admin_digital_templates_roles_api():
    """Get existing role products for digital templates."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    role_products = Product.query.filter_by(product_type='role').all()
    products = []

    for product in role_products:
        image_url = None
        if product.image_url:
            if str(product.image_url).startswith("http"):
                image_url = product.image_url
            else:
                image_url = url_for('static', filename=f"uploads/{product.image_url}", _external=True)

        import json
        delivery_data = {}
        if product.delivery_data:
            try:
                delivery_data = json.loads(product.delivery_data)
            except (json.JSONDecodeError, TypeError):
                pass

        products.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_active': product.is_active,
            'created_at': product.created_at.strftime('%m/%d/%Y') if product.created_at else None,
            'image_url': image_url,
            'role_id': delivery_data.get('role_id'),
            'auto_delivery': product.delivery_method == 'auto_role'
        })

    return _json_response({'products': products})


@api.route('/admin/digital-templates/roles', methods=['POST'])
@login_required
def admin_digital_templates_create_role_api():
    """Create a new role product."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    import json

    name = request.form.get('product_name')
    description = request.form.get('description', '')
    price_str = request.form.get('price')
    role_id = request.form.get('role_id')
    stock_str = request.form.get('stock')

    if not name or not name.strip():
        return _json_response({'error': 'Product name is required.'}, status=400)
    if not price_str:
        return _json_response({'error': 'Price is required.'}, status=400)
    if not role_id:
        return _json_response({'error': 'Discord role selection is required.'}, status=400)

    try:
        price = int(price_str)
        if price < 0:
            return _json_response({'error': 'Price must be positive.'}, status=400)
    except (ValueError, TypeError):
        return _json_response({'error': 'Price must be a valid number.'}, status=400)

    stock = None
    if stock_str and stock_str.strip():
        try:
            stock = int(stock_str)
            if stock < 0:
                return _json_response({'error': 'Stock must be positive.'}, status=400)
        except (ValueError, TypeError):
            return _json_response({'error': 'Stock must be a valid number.'}, status=400)

    image_url = None
    if 'role_image' in request.files:
        file = request.files['role_image']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            image_url = unique_filename

    product = Product(
        name=name.strip(),
        description=description.strip() if description else '',
        price=price,
        stock=stock,
        image_url=image_url,
        product_type='role',
        delivery_method='auto_role',
        delivery_data=json.dumps({'role_id': role_id}),
        created_at=datetime.utcnow()
    )

    db.session.add(product)
    db.session.commit()

    return _json_response({'ok': True, 'product_id': product.id})


@api.route('/admin/digital-templates/minecraft-skins')
@login_required
def admin_digital_templates_skins_api():
    """Get existing minecraft skin products for digital templates."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    skin_products = Product.query.filter_by(product_type='minecraft_skin').all()
    products = []

    for product in skin_products:
        preview_url = None
        preview_type = 'image'
        if product.preview_image_url:
            if str(product.preview_image_url).startswith("http"):
                preview_url = product.preview_image_url
            else:
                preview_url = url_for('static', filename=f"uploads/{product.preview_image_url}", _external=True)
            if any(product.preview_image_url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.mov']):
                preview_type = 'video'

        products.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_active': product.is_active,
            'created_at': product.created_at.strftime('%m/%d/%Y') if product.created_at else None,
            'preview_image_url': preview_url,
            'preview_type': preview_type,
            'download_file_url': product.download_file_url,
            'has_dual_files': bool(product.preview_image_url and product.download_file_url)
        })

    return _json_response({'products': products})


@api.route('/admin/digital-templates/minecraft-skins', methods=['POST'])
@login_required
def admin_digital_templates_create_skin_api():
    """Create a new minecraft skin product."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    name = request.form.get('name')
    description = request.form.get('description', '')
    price_str = request.form.get('price')
    stock_str = request.form.get('stock')

    if not name or not name.strip():
        return _json_response({'error': 'Product name is required.'}, status=400)
    if not price_str:
        return _json_response({'error': 'Price is required.'}, status=400)

    try:
        price = int(price_str)
        if price < 0:
            return _json_response({'error': 'Price must be positive.'}, status=400)
    except (ValueError, TypeError):
        return _json_response({'error': 'Price must be a valid number.'}, status=400)

    stock = None
    if stock_str and stock_str.strip():
        try:
            stock = int(stock_str)
            if stock < 0:
                return _json_response({'error': 'Stock must be positive.'}, status=400)
        except (ValueError, TypeError):
            return _json_response({'error': 'Stock must be a valid number.'}, status=400)

    preview_image_url = None
    download_file_url = None

    if 'preview_image' in request.files:
        file = request.files['preview_image']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            preview_image_url = unique_filename

    if 'download_file' in request.files:
        file = request.files['download_file']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join('static', 'uploads', unique_filename)
            file.save(file_path)
            download_file_url = unique_filename

    product = Product(
        name=name.strip(),
        description=description.strip() if description else '',
        price=price,
        stock=stock,
        product_type='minecraft_skin',
        preview_image_url=preview_image_url,
        download_file_url=download_file_url,
        created_at=datetime.utcnow()
    )

    db.session.add(product)
    db.session.commit()

    return _json_response({'ok': True, 'product_id': product.id})


# ============================================================================
# ADMIN PAGE APIs
# ============================================================================

@api.route('/admin/leaderboard')
@login_required
def admin_leaderboard_api():
    """Admin leaderboard API with pagination."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    total_users = User.query.count()
    total_balance = db.session.query(db.func.sum(User.balance)).scalar() or 0
    total_purchases = Purchase.query.count()
    total_spent = db.session.query(db.func.sum(Purchase.points_spent)).scalar() or 0
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

    pagination = User.query.order_by(User.balance.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    leaderboard_stats = []
    for i, user in enumerate(pagination.items, (page - 1) * per_page + 1):
        user_purchases = Purchase.query.filter_by(user_id=user.id).all()
        user_achievements = UserAchievement.query.filter_by(user_id=user.id).count()
        total_user_spent = sum(p.points_spent for p in user_purchases)
        activity_score = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)

        leaderboard_stats.append({
            'rank': i,
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'balance': user.balance or 0,
                'is_admin': user.is_admin,
                'has_boosted': user.has_boosted,
                'message_count': user.message_count or 0,
                'voice_minutes': user.voice_minutes or 0,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'total_spent': total_user_spent,
            'purchase_count': len(user_purchases),
            'achievement_count': user_achievements,
            'activity_score': activity_score
        })

    top_spenders_query = db.session.query(
        User,
        db.func.sum(Purchase.points_spent).label('total_spent'),
        db.func.count(Purchase.id).label('purchase_count')
    ).join(Purchase).group_by(User.id).order_by(db.desc('total_spent')).limit(10).all()

    top_spenders = []
    for user, spent, count in top_spenders_query:
        top_spenders.append({
            'user': {'id': user.id, 'username': user.username},
            'total_spent': spent or 0,
            'purchase_count': count or 0
        })

    most_active = User.query.order_by(
        (User.message_count + User.reaction_count + User.voice_minutes).desc()
    ).limit(10).all()

    most_active_list = []
    for user in most_active:
        activity = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)
        most_active_list.append({
            'user': {'id': user.id, 'username': user.username, 'message_count': user.message_count or 0},
            'activity_score': activity
        })

    return _json_response({
        'economy_stats': economy_stats,
        'leaderboard_stats': leaderboard_stats,
        'top_spenders': top_spenders,
        'most_active': most_active_list,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    })


@api.route('/admin/purchases')
@login_required
def admin_purchases_api():
    """Admin purchases API with pagination."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Purchase.query.order_by(Purchase.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    purchases = []
    for purchase in pagination.items:
        user = purchase.user
        product = purchase.product

        user_avatar = user.avatar_url if user else None
        product_image = None
        if product:
            display_image = product.display_image or product.image_url
            if display_image:
                if str(display_image).startswith("http"):
                    product_image = display_image
                else:
                    product_image = url_for('static', filename=f"uploads/{display_image}", _external=True)

        purchases.append({
            'id': purchase.id,
            'points_spent': purchase.points_spent,
            'timestamp': purchase.timestamp.isoformat(),
            'user': {
                'id': user.id if user else None,
                'username': user.username if user else 'Unknown',
                'avatar_url': user_avatar,
                'user_uuid': user.user_uuid if user else None,
                'discord_id': user.id if user else None
            },
            'product': {
                'id': product.id if product else None,
                'name': product.name if product else 'Unknown Product',
                'description': product.description[:50] + '...' if product and product.description and len(product.description) > 50 else (product.description if product else ''),
                'image_url': product_image
            }
        })

    total_points_on_page = sum(p['points_spent'] for p in purchases)

    return _json_response({
        'purchases': purchases,
        'stats': {
            'total_points_on_page': total_points_on_page
        },
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    })


@api.route('/admin/users/<user_id>')
@login_required
def admin_user_detail_api(user_id):
    """Admin user detail API."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    user = User.query.get_or_404(user_id)

    purchases = Purchase.query.filter_by(user_id=user.id).order_by(Purchase.timestamp.desc()).all()
    user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    achievements = [ua.achievement for ua in user_achievements]

    total_spent = sum(p.points_spent for p in purchases)
    total_earned = (user.balance or 0) + total_spent
    activity_score = (user.message_count or 0) + (user.reaction_count or 0) + (user.voice_minutes or 0)

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_purchases = [p for p in purchases if p.timestamp >= thirty_days_ago]
    recent_achievements = [ua for ua in user_achievements if ua.achieved_at >= thirty_days_ago]

    earning_breakdown = {
        'messages': user.message_count or 0,
        'reactions': user.reaction_count or 0,
        'voice_minutes': user.voice_minutes or 0,
        'daily_claims': getattr(user, 'daily_claims_count', 0) or 0,
        'campus_photos': getattr(user, 'campus_photos_count', 0) or 0,
        'daily_engagement': getattr(user, 'daily_engagement_count', 0) or 0,
        'achievements': sum(a.points for a in achievements),
        'verification_bonus': 200 if getattr(user, 'verification_bonus_received', False) else 0,
        'onboarding_bonus': 500 if getattr(user, 'onboarding_bonus_received', False) else 0,
        'enrollment_deposit': 1000 if getattr(user, 'enrollment_deposit_received', False) else 0,
        'birthday_bonus': 100 if getattr(user, 'birthday_points_received', False) else 0,
        'boost_bonus': 500 if user.has_boosted else 0
    }

    spending_breakdown = {}
    for purchase in purchases:
        product_type = purchase.product.product_type if purchase.product else 'unknown'
        if product_type not in spending_breakdown:
            spending_breakdown[product_type] = 0
        spending_breakdown[product_type] += purchase.points_spent

    all_users = User.query.order_by(User.balance.desc()).all()
    user_rank = None
    for i, u in enumerate(all_users, 1):
        if u.id == user.id:
            user_rank = i
            break

    recent_purchases_data = []
    for p in recent_purchases[:10]:
        recent_purchases_data.append({
            'id': p.id,
            'product_name': p.product.name if p.product else 'Unknown Product',
            'points_spent': p.points_spent,
            'timestamp': p.timestamp.isoformat()
        })

    recent_achievements_data = []
    for ua in recent_achievements[:10]:
        recent_achievements_data.append({
            'name': ua.achievement.name,
            'points': ua.achievement.points,
            'achieved_at': ua.achieved_at.isoformat()
        })

    achievements_data = []
    for a in achievements:
        achievements_data.append({
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'points': a.points
        })

    return _json_response({
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar_url': user.avatar_url,
            'balance': user.balance or 0,
            'is_admin': user.is_admin,
            'has_boosted': user.has_boosted,
            'birthday': user.birthday.strftime('%m/%d') if user.birthday else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'discord_id': user.id
        },
        'stats': {
            'user_rank': user_rank,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'activity_score': activity_score,
            'total_purchases': len(purchases),
            'total_achievements': len(achievements)
        },
        'earning_breakdown': earning_breakdown,
        'spending_breakdown': spending_breakdown,
        'achievements': achievements_data,
        'recent_purchases': recent_purchases_data,
        'recent_achievements': recent_achievements_data
    })


# ============================================================================
# CATEGORY APIs
# ============================================================================

def _slugify(name):
    """Convert a category name to a URL-safe slug."""
    import re
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


@api.route('/categories')
def categories_api():
    """Public endpoint to list all categories (used by store filter)."""
    categories = Category.query.order_by(Category.name).all()
    return _json_response({
        'categories': [
            {'id': c.id, 'name': c.name, 'slug': c.slug}
            for c in categories
        ]
    })


@api.route('/admin/categories')
@login_required
def admin_categories_api():
    """Admin: list all categories with product counts."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    categories = Category.query.order_by(Category.name).all()
    payload = []
    for cat in categories:
        count = Product.query.filter_by(category=cat.slug).count()
        payload.append({
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'product_count': count,
            'created_at': cat.created_at.isoformat() if cat.created_at else None
        })

    return _json_response({'categories': payload})


@api.route('/admin/categories', methods=['POST'])
@login_required
def admin_category_create_api():
    """Admin: create a new category."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return _json_response({'error': 'Category name is required.'}, status=400)

    slug = _slugify(name)
    if not slug:
        return _json_response({'error': 'Invalid category name.'}, status=400)

    if Category.query.filter_by(name=name).first():
        return _json_response({'error': 'A category with that name already exists.'}, status=400)
    if Category.query.filter_by(slug=slug).first():
        return _json_response({'error': 'A category with that slug already exists.'}, status=400)

    cat = Category(name=name, slug=slug)
    db.session.add(cat)
    db.session.commit()

    return _json_response({'ok': True, 'category': {'id': cat.id, 'name': cat.name, 'slug': cat.slug}})


@api.route('/admin/categories/<int:category_id>', methods=['POST'])
@login_required
def admin_category_update_api(category_id):
    """Admin: rename a category."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    cat = Category.query.get_or_404(category_id)
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return _json_response({'error': 'Category name is required.'}, status=400)

    new_slug = _slugify(name)
    if not new_slug:
        return _json_response({'error': 'Invalid category name.'}, status=400)

    existing_name = Category.query.filter(Category.name == name, Category.id != category_id).first()
    if existing_name:
        return _json_response({'error': 'A category with that name already exists.'}, status=400)

    old_slug = cat.slug
    cat.name = name
    cat.slug = new_slug

    # Update all products that reference the old slug
    if old_slug != new_slug:
        Product.query.filter_by(category=old_slug).update({'category': new_slug})

    db.session.commit()
    return _json_response({'ok': True, 'category': {'id': cat.id, 'name': cat.name, 'slug': cat.slug}})


@api.route('/admin/categories/<int:category_id>', methods=['DELETE'])
@login_required
def admin_category_delete_api(category_id):
    """Admin: delete a category and reset its products to 'general'."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    cat = Category.query.get_or_404(category_id)
    Product.query.filter_by(category=cat.slug).update({'category': 'general'})
    db.session.delete(cat)
    db.session.commit()

    return _json_response({'ok': True})


@api.route('/admin/categories/<int:category_id>/assign-all', methods=['POST'])
@login_required
def admin_category_assign_all_api(category_id):
    """Admin: retroactively assign this category to all products."""
    if not current_user.is_admin:
        return _json_response({'error': 'forbidden'}, status=403)

    cat = Category.query.get_or_404(category_id)
    data = request.get_json() or {}
    uncategorized_only = data.get('uncategorized_only', False)

    if uncategorized_only:
        updated = Product.query.filter(
            (Product.category == 'general') | (Product.category.is_(None))
        ).update({'category': cat.slug})
    else:
        updated = Product.query.update({'category': cat.slug})

    db.session.commit()
    return _json_response({'ok': True, 'updated': updated})
