import re

from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc

from model.Card import Card
from model.Comment import Comment
from model.Good import Good
from model.Images import Images
from model.InviteCode import InviteCode
from model.Tags import Tags
from model.User import User
from model.db import db
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

    import time
    now = int(time.time())
    last_attempt = session.get('register_last_attempt', 0)
    if now - last_attempt < 10:
        return jsonify(code=429, message='操作过于频繁，请稍后再试'), 429
    session['register_last_attempt'] = now

    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    captcha_input = data.get('captcha', '').strip()
    invite_code_input = data.get('invite_code', '').strip()

    if not username or not email or not password:
        return jsonify(code=400, message='用户名、邮箱和密码不能为空'), 400

    captcha_answer = session.pop('captcha', '')
    captcha_time = session.pop('captcha_time', 0)
    if not captcha_answer or not captcha_input or captcha_input != captcha_answer:
        return jsonify(code=400, message='验证码错误'), 400
    if captcha_time and (now - captcha_time) > 300:
        return jsonify(code=400, message='验证码已过期，请刷新重试'), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify(code=400, message='用户名长度需在 3-20 个字符之间'), 400

    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', username):
        return jsonify(code=400, message='用户名只能包含字母、数字、下划线和中文'), 400

    if len(password) < 6:
        return jsonify(code=400, message='密码至少6位'), 400

    if db.session.execute(db.select(User).where(User.email == email)).scalar():
        return jsonify(code=409, message='邮箱已被注册'), 409

    if db.session.execute(db.select(User).where(User.username == username)).scalar():
        return jsonify(code=409, message='用户名已被占用'), 409

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
    initial_status = 2 if need_review else 0

    user = User(number='0', username=username, email=email, status=initial_status, roles_id=[2])
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    user.number = str(1000000000 + user.id)

    if require_invite_code and invite:
        invite.used_count += 1

    db.session.commit()

    if need_review:
        return jsonify(code=200, message='注册成功，账号正在审核中', data={'id': user.id, 'username': user.username, 'status': 'pending_review'})
    return jsonify(code=200, message='注册成功', data={'id': user.id, 'username': user.username})


@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify(code=400, message='邮箱和密码不能为空'), 400

    user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    if not user or not user.check_password(password):
        return jsonify(code=401, message='邮箱或密码错误'), 401

    if user.status == 2:
        return jsonify(code=403, message='账号正在审核中，请等待管理员通过'), 403

    if user.status != 0:
        return jsonify(code=403, message='账号已被禁用'), 403

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

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    if username and username != current_user.username:
        if len(username) < 3 or len(username) > 20:
            return jsonify(code=400, message='用户名长度需在 3-20 个字符之间'), 400
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', username):
            return jsonify(code=400, message='用户名只能包含字母、数字、下划线和中文'), 400
        existing = db.session.execute(
            db.select(User).where(User.username == username, User.id != current_user.id)
        ).scalar()
        if existing:
            return jsonify(code=409, message='用户名已被占用'), 409
        current_user.username = username

    if email and email != current_user.email:
        existing = db.session.execute(
            db.select(User).where(User.email == email, User.id != current_user.id)
        ).scalar()
        if existing:
            return jsonify(code=409, message='邮箱已被注册'), 409
        current_user.email = email

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

    url = save_upload(file, sub_dir='avatars')
    current_user.avatar = url
    db.session.commit()
    return jsonify(code=200, message='头像上传成功', data={'avatar': url})


@api.route('/cards', methods=['GET'])
def get_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    per_page = min(per_page, 50)
    tag_id = request.args.get('tag', type=int)

    query = db.select(Card).where(Card.status == 1, Card.deleted_at.is_(None))
    if tag_id:
        query = query.where(Card.tags.contains(tag_id))
    query = query.order_by(desc(Card.is_top), desc(Card.created_at))

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

    items = []
    for card in pagination.items:
        author_name = '匿名'
        if not (card.data and card.data.get('anonymous')):
            author_name = card.author.username if card.author else '未知'

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
        author_name = card.author.username if card.author else '未知'

    comments = db.session.execute(
        db.select(Comment).where(
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
            'author': c.author.username if c.author else '未知',
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
        cover_url = save_upload(cover_file, sub_dir='cards')

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
            img_url = save_upload(f, sub_dir='cards')
            img = Images(aid=1, pid=new_card.id, user_id=current_user.id, url=img_url)
            db.session.add(img)

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
    db.session.commit()

    message = '评论成功，等待审核' if comment_status == 0 else '评论成功'
    return jsonify(code=200, message=message, data={
        'id': new_comment.id,
        'content': new_comment.content,
        'author': current_user.username,
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
    url = save_upload(file, sub_dir=sub_dir)
    return jsonify(code=200, message='上传成功', data={'url': url})


def _user_info(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar,
        'status': user.status,
        'roles_id': user.roles_id or [],
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }