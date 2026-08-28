import re

from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from model.Card import Card
from model.Comment import Comment
from model.Good import Good
from model.Images import Images
from model.InviteCode import InviteCode
from model.Tags import Tags
from model.User import User
from model.db import db
from utils.notification import notify_new_comment, notify_admins
from utils.rate_limit import check_rate_limit, get_remaining_time, record_failed_attempt, clear_attempts
from utils.system import get_config
from utils.upload import allowed_file, save_upload

api = Blueprint('api', __name__, url_prefix='/api/v1')

MAX_CONTENT_LENGTH = 2000


def _validate_cover_url(url):
    if not url:
        return None
    if url.startswith('/uploads/'):
        return url
    return None


@api.route('/auth/register', methods=['POST'])
def register():
    if get_config('siteAllowRegister') == 'false':
        return jsonify(code=403, message='站点已关闭注册'), 403

    ip = request.remote_addr
    if not check_rate_limit(ip, max_attempts=5, window=300):
        remaining = get_remaining_time(ip, window=300)
        return jsonify(code=429, message=f'操作过于频繁，请{remaining}秒后再试'), 429

    import time
    now = int(time.time())

    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    captcha_input = data.get('captcha', '').strip()
    invite_code_input = data.get('invite_code', '').strip()

    if not username or not email or not password:
        return jsonify(code=400, message='用户名、邮箱和密码不能为空'), 400

    captcha_answer = session.pop('api_captcha', '') or session.pop('captcha', '')
    captcha_time = session.pop('api_captcha_time', 0) or session.pop('captcha_time', 0)
    if not captcha_answer or not captcha_input or captcha_input.upper() != captcha_answer.upper():
        record_failed_attempt(ip, 'register')
        return jsonify(code=400, message='验证码错误'), 400
    if captcha_time and (now - captcha_time) > 300:
        return jsonify(code=400, message='验证码已过期，请刷新重试'), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify(code=400, message='用户名长度需在 3-20 个字符之间'), 400

    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', username):
        return jsonify(code=400, message='用户名只能包含字母、数字、下划线和中文'), 400

    if len(password) < 6:
        return jsonify(code=400, message='密码至少6位'), 400

    existing = db.session.execute(db.select(User).where(User.email == email)).scalar()
    username_existing = db.session.execute(db.select(User).where(User.username == username)).scalar()
    if existing or username_existing:
        record_failed_attempt(ip, 'register')
        return jsonify(code=409, message='用户名或邮箱已被使用'), 409

    require_invite_code = get_config('siteRequireInviteCode') == 'true'
    invite = None
    if require_invite_code:
        if not invite_code_input:
            return jsonify(code=400, message='邀请码不能为空'), 400
        invite = db.session.execute(
            db.select(InviteCode).where(InviteCode.code == invite_code_input)
        ).scalar()
        if not invite or not invite.is_valid:
            return jsonify(code=400, message='邀请码无效或已过期'), 400

    need_review = get_config('siteRegisterNeedReview') == 'true'
    require_email_verify = get_config('siteRequireEmailVerify') == 'true'
    initial_status = 2 if need_review else 0

    user = User(number='0', username=username, nickname=username, email=email, status=initial_status, roles_id=[2], email_verified=not require_email_verify)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    user.number = str(1000000000 + user.id)

    if require_invite_code and invite:
        invite.used_count += 1

    if need_review:
        notify_admins('user_pending', '新用户待审核', f'用户 {username} 注册待审核', {'user_id': user.id})

    if require_email_verify and not need_review:
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        s = URLSafeTimedSerializer(current_app.secret_key, salt='email-verify')
        token = s.dumps({'user_id': user.id, 'email': email})
        from utils.system import get_site_config
        from utils.email import send_email
        site_config = get_site_config()
        site_url = site_config.get('siteUrl', '').rstrip('/')
        verify_url = f"{site_url}/verify_email/{token}"
        html = f"""
        <div style="max-width:480px;margin:0 auto;font-family:sans-serif;">
            <h2 style="color:#667eea;">邮箱验证</h2>
            <p>你好，{username}：</p>
            <p>请点击下方按钮验证你的邮箱地址：</p>
            <a href="{verify_url}" style="display:inline-block;padding:10px 24px;background:#667eea;color:#fff;border-radius:8px;text-decoration:none;margin:12px 0;">验证邮箱</a>
            <p style="color:#999;font-size:13px;">此链接 24 小时内有效。如非本人操作，请忽略此邮件。</p>
            <p style="color:#999;font-size:13px;">如按钮无法点击，请复制链接到浏览器：<br>{verify_url}</p>
        </div>
        """
        send_email(email, f'{site_config.get("siteName", "LoveCards")} - 邮箱验证', html)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(code=409, message='用户名或邮箱已被使用'), 409
    clear_attempts(ip)

    if need_review:
        return jsonify(code=200, message='注册成功，账号正在审核中', data={'id': user.id, 'username': user.username, 'status': 'pending_review'})
    if require_email_verify:
        return jsonify(code=200, message='注册成功，验证邮件已发送至你的邮箱，请查收并完成验证后登录', data={'id': user.id, 'username': user.username, 'need_verify': True})
    return jsonify(code=200, message='注册成功', data={'id': user.id, 'username': user.username})


@api.route('/auth/login', methods=['POST'])
def login():
    ip = request.remote_addr or '0.0.0.0'
    if not check_rate_limit(ip, max_attempts=10, window=300):
        remaining = get_remaining_time(ip, window=300)
        return jsonify(code=429, message=f'登录尝试过于频繁，请 {remaining} 秒后再试'), 429

    data = request.get_json(silent=True) or {}
    account = data.get('account', '').strip() or data.get('email', '').strip()
    password = data.get('password', '')

    if not account or not password:
        return jsonify(code=400, message='账号和密码不能为空'), 400

    if '@' in account:
        user = db.session.execute(db.select(User).where(User.email == account)).scalar()
    else:
        user = db.session.execute(db.select(User).where(User.username == account)).scalar()

    if not user or not user.check_password(password):
        record_failed_attempt(ip)
        return jsonify(code=401, message='账号或密码错误'), 401

    if user.status == 2:
        return jsonify(code=403, message='账号正在审核中，请等待管理员通过'), 403

    if user.status != 0:
        return jsonify(code=403, message='账号已被禁用'), 403

    if not user.email_verified and get_config('siteRequireEmailVerify') == 'true':
        return jsonify(code=403, message='邮箱未验证，请先验证邮箱后再登录', need_verify=True), 403

    clear_attempts(ip)
    login_user(user, remember=True)
    return jsonify(code=200, message='登录成功', data=_user_info(user))


@api.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify(code=200, message='已退出登录')


@api.route('/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify(code=200, data=_user_info(current_user))


@api.route('/user/profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}

    nickname = data.get('nickname', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    if len(nickname) > 30:
        return jsonify(code=400, message='昵称长度不能超过 30 个字符'), 400
    current_user.nickname = nickname

    if email and email != current_user.email:
        existing = db.session.execute(
            db.select(User).where(User.email == email, User.id != current_user.id)
        ).scalar()
        if existing:
            return jsonify(code=409, message='邮箱已被注册'), 409
        current_user.email = email
        current_user.email_verified = False

    if phone is not None:
        current_user.phone = phone

    db.session.commit()
    return jsonify(code=200, message='更新成功', data=_user_info(current_user))


@api.route('/user/password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify(code=400, message='旧密码和新密码不能为空'), 400

    if not current_user.check_password(old_password):
        return jsonify(code=401, message='旧密码不正确'), 401

    if len(new_password) < 6:
        return jsonify(code=400, message='新密码至少6位'), 400

    current_user.set_password(new_password)
    db.session.commit()
    logout_user()
    return jsonify(code=200, message='密码修改成功，请重新登录')


@api.route('/user/avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')
    if not file or not file.filename or not allowed_file(file.filename):
        return jsonify(code=400, message='请上传有效的图片文件'), 400

    try:
        url = save_upload(file, sub_dir='avatars')
    except ValueError:
        return jsonify(code=400, message='图片格式无效，请上传真实的图片文件'), 400
    current_user.avatar = url
    db.session.commit()
    return jsonify(code=200, message='头像上传成功', data={'avatar': url})


@api.route('/cards', methods=['GET'])
def get_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    per_page = min(per_page, 50)
    tag_id = request.args.get('tag', type=int)

    query = db.select(Card).options(joinedload(Card.author)).where(Card.status == 1, Card.deleted_at.is_(None))
    if tag_id:
        query = query.where(Card.tags.contains(tag_id))
    query = query.order_by(desc(Card.is_top), desc(Card.created_at))

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

    items = []
    for card in pagination.items:
        author_name = '匿名'
        if not (card.data and card.data.get('anonymous')):
            author_name = card.author.display_name if card.author else '未知'

        items.append({
            'id': card.id,
            'content': card.content,
            'cover': card.cover,
            'good': card.good,
            'views': card.views,
            'comments': card.comments,
            'is_top': card.is_top,
            'author': author_name,
            'is_anonymous': bool(card.data and card.data.get('anonymous')),
            'tags': card.tags or [],
            'created_at': card.created_at.isoformat() if card.created_at else None,
        })

    return jsonify(code=200, data={
        'items': items,
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
    })


@api.route('/cards/<int:card_id>', methods=['GET'])
def get_card_detail(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None or card.status != 1:
        return jsonify(code=404, message='卡片不存在'), 404

    card.views = (card.views or 0) + 1
    db.session.commit()

    author_name = '匿名'
    if not (card.data and card.data.get('anonymous')):
        author_name = card.author.display_name if card.author else '未知'

    comments = db.session.execute(
        db.select(Comment).options(joinedload(Comment.user)).where(
            Comment.aid == 1, Comment.pid == card_id,
            Comment.status == 1, Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at.desc())
    ).scalars().all()

    images = db.session.execute(
        db.select(Images).where(
            Images.aid == 1, Images.pid == card_id, Images.deleted_at.is_(None)
        )
    ).scalars().all()

    is_liked = False
    if current_user.is_authenticated:
        is_liked = db.session.execute(
            db.select(Good).where(Good.aid == 1, Good.pid == card_id, Good.uid == current_user.id)
        ).scalar() is not None

    return jsonify(code=200, data={
        'id': card.id,
        'content': card.content,
        'cover': card.cover,
        'good': card.good,
        'views': card.views,
        'comments': card.comments,
        'is_top': card.is_top,
        'author': author_name,
        'is_anonymous': bool(card.data and card.data.get('anonymous')),
        'tags': card.tags or [],
        'created_at': card.created_at.isoformat() if card.created_at else None,
        'is_liked': is_liked,
        'comment_list': [{
            'id': c.id,
            'content': c.content,
            'author': c.author.display_name if c.author else '未知',
            'created_at': c.created_at.isoformat() if c.created_at else None,
        } for c in comments],
        'image_list': [{'id': i.id, 'url': i.url} for i in images],
    })


@api.route('/cards', methods=['POST'])
@login_required
def create_card():
    if get_config('siteAllowPublish') == 'false':
        return jsonify(code=403, message='站点已关闭发布'), 403

    content = request.form.get('content', '').strip()
    is_anonymous = request.form.get('is_anonymous') == '1'
    tag_ids = request.form.getlist('tags', type=int)

    if not content:
        return jsonify(code=400, message='内容不能为空'), 400

    if len(content) > MAX_CONTENT_LENGTH:
        return jsonify(code=400, message=f'内容不能超过 {MAX_CONTENT_LENGTH} 个字符'), 400

    cover_url = None
    cover_file = request.files.get('cover_file')
    if cover_file and cover_file.filename and allowed_file(cover_file.filename):
        try:
            cover_url = save_upload(cover_file, sub_dir='cards')
        except ValueError:
            return jsonify(code=400, message='封面图片格式无效'), 400

    cover_input = request.form.get('cover', '').strip()
    if not cover_url:
        cover_url = _validate_cover_url(cover_input)

    need_review = get_config('siteCardNeedReview') != 'false'
    initial_status = 0 if need_review else 1

    new_card = Card(
        user_id=current_user.id,
        content=content,
        cover=cover_url,
        tags=tag_ids if tag_ids else None,
        status=initial_status,
        is_top=0,
        data={'anonymous': is_anonymous}
    )
    db.session.add(new_card)
    db.session.flush()

    extra_files = request.files.getlist('images')
    for f in extra_files:
        if f and f.filename and allowed_file(f.filename):
            try:
                img_url = save_upload(f, sub_dir='cards')
                img = Images(aid=1, pid=new_card.id, user_id=current_user.id, url=img_url)
                db.session.add(img)
            except ValueError:
                pass

    if need_review:
        notify_admins('card_pending', '新卡片待审核', f'用户 {current_user.display_name} 发布的卡片待审核', {'card_id': new_card.id})
    db.session.commit()
    message = '发布成功，等待审核' if need_review else '发布成功'
    return jsonify(code=200, message=message, data={'id': new_card.id})


@api.route('/cards/<int:card_id>/like', methods=['POST'])
@login_required
def toggle_like(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        return jsonify(code=404, message='卡片不存在'), 404

    existing = db.session.execute(
        db.select(Good).where(Good.aid == 1, Good.pid == card_id, Good.uid == current_user.id)
    ).scalar()

    if existing:
        db.session.delete(existing)
        card.good = max((card.good or 1) - 1, 0)
        db.session.commit()
        return jsonify(code=200, data={'liked': False, 'count': card.good})
    else:
        new_good = Good(aid=1, pid=card_id, uid=current_user.id, ip=request.remote_addr or '0.0.0.0')
        db.session.add(new_good)
        card.good = (card.good or 0) + 1
        db.session.commit()
        return jsonify(code=200, data={'liked': True, 'count': card.good})


@api.route('/cards/<int:card_id>/comments', methods=['POST'])
@login_required
def add_comment(card_id):
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify(code=400, message='评论内容不能为空'), 400

    if len(content) > 500:
        return jsonify(code=400, message='评论内容不能超过 500 个字符'), 400

    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        return jsonify(code=404, message='卡片不存在'), 404

    need_review = get_config('siteCommentNeedReview') != 'false'
    comment_status = 0 if need_review else 1

    new_comment = Comment(
        aid=1, pid=card_id, user_id=current_user.id,
        content=content, status=comment_status,
    )
    db.session.add(new_comment)
    if comment_status == 1:
        card.comments = (card.comments or 0) + 1
        notify_new_comment(card, current_user.id)
    else:
        notify_admins('comment_pending', '新评论待审核', f'用户 {current_user.display_name} 的评论待审核', {'card_id': card.id})
    db.session.commit()

    message = '评论成功，等待审核' if comment_status == 0 else '评论成功'
    return jsonify(code=200, message=message, data={
        'id': new_comment.id,
        'content': new_comment.content,
        'author': current_user.display_name,
        'created_at': new_comment.created_at.isoformat() if new_comment.created_at else None,
    })


@api.route('/tags', methods=['GET'])
def get_tags():
    tags = db.session.execute(
        db.select(Tags).where(Tags.status == 0, Tags.deleted_at.is_(None))
    ).scalars().all()

    return jsonify(code=200, data=[{
        'id': t.id,
        'name': t.name,
    } for t in tags])


@api.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file or not file.filename or not allowed_file(file.filename):
        return jsonify(code=400, message='不支持的文件类型'), 400

    sub_dir = request.form.get('sub_dir', 'cards')
    try:
        url = save_upload(file, sub_dir=sub_dir)
    except ValueError:
        return jsonify(code=400, message='图片格式无效，请上传真实的图片文件'), 400
    return jsonify(code=200, message='上传成功', data={'url': url})


def _user_info(user):
    return {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'display_name': user.display_name,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'status': user.status,
        'roles_id': user.roles_id or [],
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }