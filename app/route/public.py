from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, get_flashed_messages
from flask_login import login_required, current_user, logout_user
from sqlalchemy import desc, asc, or_
from datetime import datetime, timedelta

from model.Card import Card
from model.Comment import Comment
from model.Images import Images
from model.Tags import Tags
from model.User import User
from model.Good import Good
from model.DeletedUser import DeletedUser
from model.BanRecord import BanRecord
from model.db import db
from utils.upload import allowed_file, save_upload

public = Blueprint('public', __name__)


@public.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    tag_id = request.args.get('tag', type=int)
    search = request.args.get('search', '').strip()

    query = db.select(Card).where(
        Card.status == 1,
        Card.deleted_at.is_(None)
    )

    if tag_id:
        query = query.where(Card.tags.contains(tag_id))

    if search:
        conditions = [Card.content.ilike(f'%{search}%')]
        author_subq = db.select(User.id).where(User.username.ilike(f'%{search}%'))
        conditions.append(Card.user_id.in_(author_subq))
        query = query.where(or_(*conditions))

    query = query.order_by(desc(Card.is_top), Card.created_at.asc())

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    cards = pagination.items

    tags = db.session.execute(
        db.select(Tags).where(Tags.status == 0, Tags.deleted_at.is_(None))
    ).scalars().all()

    return render_template("public/index.html", cards=cards, tags=tags, pagination=pagination, current_tag=tag_id, search=search)


@public.route('/card/<int:card_id>')
def card_detail(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        return render_template("public/404.html"), 404

    card.views = (card.views or 0) + 1
    db.session.commit()

    comments = db.session.execute(
        db.select(Comment).where(
            Comment.aid == 1,
            Comment.pid == card_id,
            Comment.status == 1,
            Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at.desc())
    ).scalars().all()

    if current_user.is_authenticated:
        for c in comments:
            c.is_liked = db.session.execute(
                db.select(Good).where(Good.aid == 2, Good.pid == c.id, Good.uid == current_user.id)
            ).scalar() is not None

    images = db.session.execute(
        db.select(Images).where(
            Images.aid == 1,
            Images.pid == card_id,
            Images.deleted_at.is_(None)
        )
    ).scalars().all()

    is_liked = False
    if current_user.is_authenticated:
        is_liked = db.session.execute(
            db.select(Good).where(Good.aid == 1, Good.pid == card_id, Good.uid == current_user.id)
        ).scalar() is not None

    return render_template("public/card_detail.html", card=card, comments=comments, images=images, is_liked=is_liked)


@public.route('/comment', methods=['POST'])
@login_required
def add_comment():
    aid = request.form.get('aid', 1, type=int)
    pid = request.form.get('pid', type=int)
    content = request.form.get('content', '').strip()

    if not pid or not content:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message='评论内容不能为空'), 400
        flash('评论内容不能为空', 'error')
        return redirect(request.referrer or '/')

    card = db.session.get(Card, pid)
    if not card or card.deleted_at is not None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message='卡片不存在'), 404
        flash('卡片不存在', 'error')
        return redirect('/')

    new_comment = Comment(
        aid=aid,
        pid=pid,
        user_id=current_user.id,
        content=content,
        status=1,
    )
    db.session.add(new_comment)

    card.comments = (card.comments or 0) + 1
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message='评论成功')
    flash('评论成功', 'success')
    return redirect(url_for('public.card_detail', card_id=pid))


@public.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        is_anonymous = request.form.get('is_anonymous') == '1'

        if not content:
            flash('内容不能为空', 'error')
            return redirect(url_for('public.publish'))

        tag_ids = request.form.getlist('tags', type=int)

        cover_url = None
        cover_file = request.files.get('cover_file')
        if cover_file and cover_file.filename and allowed_file(cover_file.filename):
            cover_url = save_upload(cover_file, sub_dir='cards')

        cover_input = request.form.get('cover', '').strip()
        if not cover_url and cover_input:
            cover_url = cover_input

        new_card = Card(
            user_id=current_user.id,
            content=content,
            cover=cover_url,
            tags=tag_ids if tag_ids else None,
            status=0,
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
        flash('发布成功，等待审核通过后将在首页展示', 'success')
        return redirect(url_for('public.index'))

    tags = db.session.execute(
        db.select(Tags).where(Tags.status == 0, Tags.deleted_at.is_(None))
    ).scalars().all()

    return render_template("public/publish.html", tags=tags)


@public.route('/profile', methods=['GET'])
@login_required
def profile():
    my_cards_count = db.session.execute(
        db.select(db.func.count()).select_from(Card).where(
            Card.user_id == current_user.id, Card.deleted_at.is_(None)
        )
    ).scalar() or 0

    my_good_count = db.session.execute(
        db.select(db.func.count()).select_from(Good).where(Good.uid == current_user.id)
    ).scalar() or 0

    my_comment_count = db.session.execute(
        db.select(db.func.count()).select_from(Comment).where(
            Comment.user_id == current_user.id, Comment.deleted_at.is_(None)
        )
    ).scalar() or 0

    my_cards = db.session.execute(
        db.select(Card).where(
            Card.user_id == current_user.id, Card.deleted_at.is_(None)
        ).order_by(desc(Card.created_at)).limit(10)
    ).scalars().all()

    my_comments = db.session.execute(
        db.select(Comment).where(
            Comment.user_id == current_user.id, Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at.desc()).limit(10)
    ).scalars().all()

    return render_template("public/user/profile.html",
                           my_cards_count=my_cards_count,
                           my_good_count=my_good_count,
                           my_comment_count=my_comment_count,
                           my_cards=my_cards,
                           my_comments=my_comments)


@public.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if username and username != current_user.username:
            existing = db.session.execute(
                db.select(User).where(User.username == username, User.id != current_user.id)
            ).scalar()
            if existing:
                flash('用户名已被占用', 'error')
            else:
                current_user.username = username

        if email and email != current_user.email:
            existing = db.session.execute(
                db.select(User).where(User.email == email, User.id != current_user.id)
            ).scalar()
            if existing:
                flash('邮箱已被注册', 'error')
            else:
                current_user.email = email

        current_user.phone = phone

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
            avatar_url = save_upload(avatar_file, sub_dir='avatars')
            current_user.avatar = avatar_url

        db.session.commit()
        if not any(m[1] == 'error' for m in get_flashed_messages(with_categories=True)):
            flash('个人信息已更新', 'success')
        return redirect(url_for('public.profile_edit'))

    return render_template("public/user/profile_edit.html")


@public.route('/profile/security')
@login_required
def profile_security():
    return render_template("public/user/profile_security.html")


@public.route('/profile/security/password', methods=['POST'])
@login_required
def security_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not old_password or not new_password:
        flash('请填写完整信息', 'error')
        return redirect(url_for('public.profile_security'))

    if not current_user.check_password(old_password):
        flash('当前密码不正确', 'error')
        return redirect(url_for('public.profile_security'))

    if len(new_password) < 6:
        flash('新密码长度至少 6 位', 'error')
        return redirect(url_for('public.profile_security'))

    if new_password != confirm_password:
        flash('两次输入的新密码不一致', 'error')
        return redirect(url_for('public.profile_security'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('密码修改成功，请重新登录', 'success')
    logout_user()
    return redirect(url_for('auth.login'))


@public.route('/profile/security/email', methods=['POST'])
@login_required
def security_email():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('请填写完整信息', 'error')
        return redirect(url_for('public.profile_security'))

    if not current_user.check_password(password):
        flash('密码验证失败', 'error')
        return redirect(url_for('public.profile_security'))

    if email == current_user.email:
        flash('新邮箱与当前邮箱相同', 'error')
        return redirect(url_for('public.profile_security'))

    existing = db.session.execute(
        db.select(User).where(User.email == email, User.id != current_user.id)
    ).scalar()
    if existing:
        flash('该邮箱已被其他账号使用', 'error')
        return redirect(url_for('public.profile_security'))

    current_user.email = email
    db.session.commit()
    flash('邮箱修改成功', 'success')
    return redirect(url_for('public.profile_security'))


@public.route('/profile/security/phone', methods=['POST'])
@login_required
def security_phone():
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')

    if not password:
        flash('请输入密码验证', 'error')
        return redirect(url_for('public.profile_security'))

    if not current_user.check_password(password):
        flash('密码验证失败', 'error')
        return redirect(url_for('public.profile_security'))

    current_user.phone = phone
    db.session.commit()
    flash('手机号修改成功', 'success')
    return redirect(url_for('public.profile_security'))


@public.route('/profile/security/delete', methods=['POST'])
@login_required
def security_delete_account():
    password = request.form.get('password', '')

    if not password or not current_user.check_password(password):
        flash('密码验证失败，无法注销', 'error')
        return redirect(url_for('public.profile_security'))

    existing = db.session.execute(
        db.select(DeletedUser).where(DeletedUser.original_id == current_user.id)
    ).scalar()
    if existing:
        flash('账号已在注销流程中', 'error')
        return redirect(url_for('public.profile_security'))

    cards_count = db.session.execute(
        db.select(db.func.count()).select_from(Card).where(
            Card.user_id == current_user.id, Card.deleted_at.is_(None)
        )
    ).scalar() or 0

    comments_count = db.session.execute(
        db.select(db.func.count()).select_from(Comment).where(
            Comment.user_id == current_user.id, Comment.deleted_at.is_(None)
        )
    ).scalar() or 0

    goods_count = db.session.execute(
        db.select(db.func.count()).select_from(Good).where(Good.uid == current_user.id)
    ).scalar() or 0

    archive = DeletedUser(
        original_id=current_user.id,
        number=current_user.number,
        avatar=current_user.avatar,
        email=current_user.email,
        phone=current_user.phone,
        username=current_user.username,
        roles_id=current_user.roles_id,
        cards_count=cards_count,
        comments_count=comments_count,
        goods_count=goods_count,
        delete_scheduled_at=datetime.now() + timedelta(days=3)
    )
    db.session.add(archive)

    current_user.status = 1
    current_user.username = f'[注销中]{current_user.username}'
    db.session.commit()

    logout_user()
    flash('账号注销申请已提交，3天冷静期内可联系管理员恢复。冷静期后数据将被永久删除。', 'success')
    return redirect(url_for('public.index'))


@public.route('/profile/cards')
@login_required
def profile_cards():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    my_cards_count = db.session.execute(
        db.select(db.func.count()).select_from(Card).where(
            Card.user_id == current_user.id, Card.deleted_at.is_(None)
        )
    ).scalar() or 0

    query = db.select(Card).where(
        Card.user_id == current_user.id, Card.deleted_at.is_(None)
    ).order_by(desc(Card.created_at))

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    cards = pagination.items

    return render_template("public/user/profile_cards.html",
                           my_cards_count=my_cards_count,
                           cards=cards,
                           pagination=pagination)


@public.route('/profile/comments')
@login_required
def profile_comments():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    my_comment_count = db.session.execute(
        db.select(db.func.count()).select_from(Comment).where(
            Comment.user_id == current_user.id, Comment.deleted_at.is_(None)
        )
    ).scalar() or 0

    query = db.select(Comment).where(
        Comment.user_id == current_user.id, Comment.deleted_at.is_(None)
    ).order_by(Comment.created_at.desc())

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    comments = pagination.items

    return render_template("public/user/profile_comments.html",
                           my_comment_count=my_comment_count,
                           comments=comments,
                           pagination=pagination)


@public.route('/good/<int:card_id>', methods=['POST'])
@login_required
def toggle_good(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        return jsonify(success=False, message='卡片不存在'), 404

    existing = db.session.execute(
        db.select(Good).where(Good.aid == 1, Good.pid == card_id, Good.uid == current_user.id)
    ).scalar()

    if existing:
        db.session.delete(existing)
        card.good = max((card.good or 1) - 1, 0)
        db.session.commit()
        return jsonify(success=True, liked=False, count=card.good)
    else:
        new_good = Good(aid=1, pid=card_id, uid=current_user.id, ip=request.remote_addr or '0.0.0.0')
        db.session.add(new_good)
        card.good = (card.good or 0) + 1
        db.session.commit()
        return jsonify(success=True, liked=True, count=card.good)


@public.route('/comment/<int:comment_id>/good', methods=['POST'])
@login_required
def comment_toggle_good(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        return jsonify(success=False, message='评论不存在'), 404

    existing = db.session.execute(
        db.select(Good).where(Good.aid == 2, Good.pid == comment_id, Good.uid == current_user.id)
    ).scalar()

    if existing:
        db.session.delete(existing)
        comment.goods = max((comment.goods or 1) - 1, 0)
        db.session.commit()
        return jsonify(success=True, liked=False, count=comment.goods)
    else:
        new_good = Good(aid=2, pid=comment_id, uid=current_user.id, ip=request.remote_addr or '0.0.0.0')
        db.session.add(new_good)
        comment.goods = (comment.goods or 0) + 1
        db.session.commit()
        return jsonify(success=True, liked=True, count=comment.goods)


@public.route('/ban_records')
def ban_records():
    page = request.args.get('page', 1, type=int)
    query = db.select(BanRecord).where(BanRecord.unbanned_at.is_(None)).order_by(desc(BanRecord.created_at))
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    records = pagination.items
    return render_template("public/ban_records.html", records=records, pagination=pagination)


@public.route('/about')
def about():
    return render_template("public/about.html")


@public.route("/terms")
def terms():
    return render_template("public/terms.html")


@public.route("/privacy")
def privacy():
    return render_template("public/privacy.html")