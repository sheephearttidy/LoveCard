from datetime import datetime, timedelta
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload

from model.BanRecord import BanRecord
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.Images import Images
from model.Notification import Notification
from model.Tags import Tags
from model.User import User
from model.db import db
from utils.system import get_config
from utils.upload import allowed_file, save_upload
from utils.notification import notify_new_comment, notify_admins, get_unread_count
from utils.theme import render_themed

public = Blueprint('public', __name__)

MAX_CONTENT_LENGTH = 2000
MAX_COMMENT_LENGTH = 500


def _escape_like(value):
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _validate_cover_url(url):
    if not url:
        return None
    if url.startswith('/uploads/'):
        return url
    return None


@public.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    tag_id = request.args.get('tag', type=int)
    search = request.args.get('search', '').strip()

    query = db.select(Card).options(joinedload(Card.author)).where(
        Card.status == 1,
        Card.deleted_at.is_(None)
    )

    if tag_id:
        query = query.where(Card.tags.contains(tag_id))

    if search:
        escaped = _escape_like(search)
        conditions = [Card.content.ilike(f'%{escaped}%')]
        author_subq = db.select(User.id).where(or_(User.username.ilike(f'%{escaped}%'), User.nickname.ilike(f'%{escaped}%')))
        conditions.append(Card.user_id.in_(author_subq))
        query = query.where(or_(*conditions))

    query = query.order_by(desc(Card.is_top), Card.created_at.asc())

    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    cards = pagination.items

    tags = db.session.execute(
        db.select(Tags).where(Tags.status == 0, Tags.deleted_at.is_(None))
    ).scalars().all()

    return render_themed("public/index.html", cards=cards, tags=tags, pagination=pagination, current_tag=tag_id, search=search)


@public.route('/card/<int:card_id>')
def card_detail(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        return render_themed("public/404.html"), 404

    if card.status != 1:
        if not current_user.is_authenticated or not current_user.is_admin:
            return render_themed("public/404.html"), 404

    card.views = (card.views or 0) + 1
    db.session.commit()

    comments = db.session.execute(
        db.select(Comment).options(joinedload(Comment.user)).where(
            Comment.aid == 1,
            Comment.pid == card_id,
            Comment.status == 1,
            Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at.desc())
    ).scalars().all()

    if current_user.is_authenticated:
        comment_ids = [c.id for c in comments]
        liked_comment_ids = set()
        if comment_ids:
            liked_rows = db.session.execute(
                db.select(Good.pid).where(
                    Good.aid == 2, Good.pid.in_(comment_ids), Good.uid == current_user.id
                )
            ).scalars().all()
            liked_comment_ids = set(liked_rows)
        for c in comments:
            c.is_liked = c.id in liked_comment_ids

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

    return render_themed("public/card_detail.html", card=card, comments=comments, images=images, is_liked=is_liked)


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

    if len(content) > MAX_COMMENT_LENGTH:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message=f'评论内容不能超过 {MAX_COMMENT_LENGTH} 个字符'), 400
        flash(f'评论内容不能超过 {MAX_COMMENT_LENGTH} 个字符', 'error')
        return redirect(request.referrer or '/')

    card = db.session.get(Card, pid)
    if not card or card.deleted_at is not None:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message='卡片不存在'), 404
        flash('卡片不存在', 'error')
        return redirect('/')

    need_review = get_config('siteCommentNeedReview') != 'false'
    comment_status = 0 if need_review else 1

    new_comment = Comment(
        aid=aid,
        pid=pid,
        user_id=current_user.id,
        content=content,
        status=comment_status,
    )
    db.session.add(new_comment)

    if comment_status == 1:
        card.comments = (card.comments or 0) + 1
        notify_new_comment(card, current_user.id)
    else:
        notify_admins('comment_pending', '新评论待审核', f'用户 {current_user.display_name} 的评论待审核', {'card_id': card.id})
    db.session.commit()

    if comment_status == 0:
        msg = '评论已提交，等待审核通过后将会展示'
    else:
        msg = '评论成功'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True, message=msg)
    flash(msg, 'success')
    return redirect(url_for('public.card_detail', card_id=pid))


@public.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    if get_config('siteAllowPublish') == 'false':
        flash('站点已关闭发布', 'error')
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        is_anonymous = request.form.get('is_anonymous') == '1'

        if not content:
            flash('内容不能为空', 'error')
            return redirect(url_for('public.publish'))

        if len(content) > MAX_CONTENT_LENGTH:
            flash(f'内容不能超过 {MAX_CONTENT_LENGTH} 个字符', 'error')
            return redirect(url_for('public.publish'))

        tag_ids = request.form.getlist('tags', type=int)

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

        if need_review:
            notify_admins('card_pending', '新卡片待审核', f'用户 {current_user.display_name} 发布的卡片待审核', {'card_id': new_card.id})
        db.session.commit()
        if need_review:
            flash('发布成功，等待审核通过后将在首页展示', 'success')
        else:
            flash('发布成功', 'success')
        return redirect(url_for('public.index'))

    tags = db.session.execute(
        db.select(Tags).where(Tags.status == 0, Tags.deleted_at.is_(None))
    ).scalars().all()

    return render_themed("public/publish.html", tags=tags)


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

    return render_themed("public/user/profile.html",
                           my_cards_count=my_cards_count,
                           my_good_count=my_good_count,
                           my_comment_count=my_comment_count,
                           my_cards=my_cards,
                           my_comments=my_comments)


@public.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        has_error = False

        if len(nickname) > 30:
            flash('昵称长度不能超过 30 个字符', 'error')
            has_error = True
        else:
            current_user.nickname = nickname

        if email and email != current_user.email:
            existing = db.session.execute(
                db.select(User).where(User.email == email, User.id != current_user.id)
            ).scalar()
            if existing:
                flash('邮箱已被注册', 'error')
                has_error = True
            else:
                current_user.email = email

        current_user.phone = phone

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
            avatar_url = save_upload(avatar_file, sub_dir='avatars')
            current_user.avatar = avatar_url

        db.session.commit()
        if not has_error:
            flash('个人信息已更新', 'success')
        return redirect(url_for('public.profile_edit'))

    return render_themed("public/user/profile_edit.html")


@public.route('/profile/security')
@login_required
def profile_security():
    return render_themed("public/user/profile_security.html")


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
        nickname=current_user.nickname,
        roles_id=current_user.roles_id,
        cards_count=cards_count,
        comments_count=comments_count,
        goods_count=goods_count,
        delete_scheduled_at=datetime.now() + timedelta(days=3)
    )
    db.session.add(archive)

    now = datetime.now()
    my_cards = db.session.execute(
        db.select(Card).where(Card.user_id == current_user.id, Card.deleted_at.is_(None))
    ).scalars().all()
    for c in my_cards:
        c.deleted_at = now

    my_comments = db.session.execute(
        db.select(Comment).where(Comment.user_id == current_user.id, Comment.deleted_at.is_(None))
    ).scalars().all()
    for c in my_comments:
        c.deleted_at = now

    current_user.status = 1
    current_user.username = f'[注销中]{current_user.username}'
    current_user.nickname = f'[注销中]{current_user.nickname}'
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

    return render_themed("public/user/profile_cards.html",
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

    return render_themed("public/user/profile_comments.html",
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
    return render_themed("public/ban_records.html", records=records, pagination=pagination)


@public.route('/profile/cards/<int:card_id>/delete', methods=['POST'])
@login_required
def profile_card_delete(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        flash('卡片不存在', 'error')
        return redirect(url_for('public.profile_cards'))

    if card.user_id != current_user.id:
        flash('无权删除此卡片', 'error')
        return redirect(url_for('public.profile_cards'))

    now = datetime.now()
    card.deleted_at = now

    related_comments = db.session.execute(
        db.select(Comment).where(Comment.pid == card_id, Comment.deleted_at.is_(None))
    ).scalars().all()
    for c in related_comments:
        c.deleted_at = now

    db.session.commit()
    flash('卡片已删除', 'success')
    return redirect(url_for('public.profile_cards'))


@public.route('/profile/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def profile_comment_delete(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        flash('评论不存在', 'error')
        return redirect(url_for('public.profile_comments'))

    if comment.user_id != current_user.id:
        flash('无权删除此评论', 'error')
        return redirect(url_for('public.profile_comments'))

    comment.deleted_at = datetime.now()

    if comment.pid:
        card = db.session.get(Card, comment.pid)
        if card and card.comments > 0:
            card.comments -= 1

    db.session.commit()
    flash('评论已删除', 'success')
    return redirect(url_for('public.profile_comments'))


@public.route('/about')
def about():
    return render_themed("public/about.html")


@public.route("/terms")
def terms():
    return render_themed("public/terms.html")


@public.route("/privacy")
def privacy():
    return render_themed("public/privacy.html")


@public.route("/api_docs")
def api_docs():
    return render_themed("public/api_docs.html")


@public.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    query = db.select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at))
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    items = pagination.items
    return render_themed("public/notifications.html", notifications=items, pagination=pagination)


@public.route('/notifications/read/<int:nid>', methods=['POST'])
@login_required
def notification_read(nid):
    n = db.session.get(Notification, nid)
    if n and n.user_id == current_user.id:
        n.is_read = 1
        db.session.commit()
    return jsonify(success=True)


@public.route('/notifications/read_all', methods=['POST'])
@login_required
def notification_read_all():
    db.session.execute(
        db.update(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == 0
        ).values(is_read=1)
    )
    db.session.commit()
    return jsonify(success=True)


@public.route('/notifications/count')
@login_required
def notification_count():
    count = get_unread_count(current_user.id)
    return jsonify(count=count)