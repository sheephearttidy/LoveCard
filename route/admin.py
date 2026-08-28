from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort, session
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import joinedload

from model.AuditLog import AuditLog
from model.BanRecord import BanRecord
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.Images import Images
from model.InviteCode import InviteCode
from model.Notification import Notification
from model.RateLimitAttempt import RateLimitAttempt
from model.Tags import Tags
from model.TagsMap import TagsMap
from model.User import User
from model.db import db
from utils.audit import log_action
from utils.notification import notify_card_status, notify_comment_status, push_notification
from utils.system import ensure_default_configs, set_config, get_site_config, SITE_CONFIG_LABELS, SITE_CONFIG_GROUPS, \
    SITE_CONFIG_HINTS, AVAILABLE_THEMES
from utils.theme import clear_template_cache

admin = Blueprint('admin', __name__, url_prefix='/admin')


def _escape_like(value):
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def super_admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_super_admin:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


@admin.route('/')
@admin_required
def dashboard():
    cards_total = db.session.execute(db.select(func.count()).select_from(Card).where(Card.deleted_at.is_(None))).scalar() or 0
    cards_pending = db.session.execute(db.select(func.count()).select_from(Card).where(Card.status == 0, Card.deleted_at.is_(None))).scalar() or 0
    cards_approved = db.session.execute(db.select(func.count()).select_from(Card).where(Card.status == 1, Card.deleted_at.is_(None))).scalar() or 0
    cards_banned = db.session.execute(db.select(func.count()).select_from(Card).where(Card.status == 3, Card.deleted_at.is_(None))).scalar() or 0
    users_total = db.session.execute(db.select(func.count()).select_from(User)).scalar() or 0
    users_pending = db.session.execute(db.select(func.count()).select_from(User).where(User.status == 2)).scalar() or 0
    comments_total = db.session.execute(db.select(func.count()).select_from(Comment).where(Comment.deleted_at.is_(None))).scalar() or 0
    comments_pending = db.session.execute(db.select(func.count()).select_from(Comment).where(Comment.status == 0, Comment.deleted_at.is_(None))).scalar() or 0
    goods_total = db.session.execute(db.select(func.count()).select_from(Good)).scalar() or 0

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cards_today = db.session.execute(
        db.select(func.count()).select_from(Card).where(Card.created_at >= today, Card.deleted_at.is_(None))
    ).scalar() or 0
    users_today = db.session.execute(
        db.select(func.count()).select_from(User).where(User.created_at >= today)
    ).scalar() or 0
    comments_today = db.session.execute(
        db.select(func.count()).select_from(Comment).where(Comment.created_at >= today, Comment.deleted_at.is_(None))
    ).scalar() or 0

    recent_cards = db.session.execute(
        db.select(Card).where(Card.deleted_at.is_(None)).order_by(desc(Card.created_at)).limit(5)
    ).scalars().all()

    recent_users = db.session.execute(
        db.select(User).order_by(desc(User.created_at)).limit(5)
    ).scalars().all()

    return render_template("admin/dashboard.html",
                           cards_total=cards_total, cards_pending=cards_pending,
                           cards_approved=cards_approved, cards_banned=cards_banned,
                           users_total=users_total, users_pending=users_pending,
                           comments_total=comments_total, comments_pending=comments_pending,
                           goods_total=goods_total,
                           cards_today=cards_today, users_today=users_today,
                           comments_today=comments_today,
                           recent_cards=recent_cards, recent_users=recent_users)


@admin.route('/cards')
@admin_required
def cards_list():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', type=int)
    search = request.args.get('search', '').strip()

    query = db.select(Card).where(Card.deleted_at.is_(None))
    if status_filter is not None:
        query = query.where(Card.status == status_filter)
    if search:
        escaped = _escape_like(search)
        conditions = [Card.content.ilike(f'%{escaped}%')]
        if search.isdigit():
            conditions.append(Card.id == int(search))
        author_subq = db.select(User.id).where(or_(User.username.ilike(f'%{escaped}%'), User.nickname.ilike(f'%{escaped}%')))
        conditions.append(Card.user_id.in_(author_subq))
        query = query.where(or_(*conditions))
    query = query.order_by(desc(Card.created_at))

    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    cards = pagination.items

    return render_template("admin/cards.html", cards=cards, pagination=pagination,
                           status_filter=status_filter, search=search)


@admin.route('/cards/<int:card_id>/detail')
@admin_required
def card_detail(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        abort(404)

    images = db.session.execute(
        db.select(Images).where(
            Images.aid == 1,
            Images.pid == card_id,
            Images.deleted_at.is_(None)
        )
    ).scalars().all()

    comments = db.session.execute(
        db.select(Comment).where(
            Comment.pid == card_id,
            Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at.desc())
    ).scalars().all()

    tags = []
    if card.tags:
        tags = db.session.execute(
            db.select(Tags).where(Tags.id.in_(card.tags), Tags.deleted_at.is_(None))
        ).scalars().all()

    return render_template("admin/card_detail.html", card=card, images=images,
                           comments=comments, tags=tags)


@admin.route('/cards/<int:card_id>/approve', methods=['POST'])
@admin_required
def card_approve(card_id):
    card = db.session.get(Card, card_id)
    if card:
        card.status = 1
        card.updated_at = datetime.now()
        log_action('card_approve', 'card', card_id, f'卡片 #{card_id} 审核通过')
        notify_card_status(card, current_user.id)
        db.session.commit()
        flash('卡片已审核通过', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/reject', methods=['POST'])
@admin_required
def card_reject(card_id):
    card = db.session.get(Card, card_id)
    if card:
        card.status = 2
        card.updated_at = datetime.now()
        log_action('card_reject', 'card', card_id, f'卡片 #{card_id} 审核拒绝')
        notify_card_status(card, current_user.id)
        db.session.commit()
        flash('卡片已拒绝', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/ban', methods=['POST'])
@admin_required
def card_ban(card_id):
    card = db.session.get(Card, card_id)
    if card:
        reason = request.form.get('ban_reason', '').strip()
        card.status = 3
        card.updated_at = datetime.now()
        if reason:
            card.data = card.data or {}
            card.data['ban_reason'] = reason
        log_action('card_ban', 'card', card_id, f'卡片 #{card_id} 已封禁{("，原因: " + reason) if reason else ""}')
        notify_card_status(card, current_user.id)
        db.session.commit()
        flash('卡片已封禁', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/unban', methods=['POST'])
@admin_required
def card_unban(card_id):
    card = db.session.get(Card, card_id)
    if card:
        card.status = 1
        card.updated_at = datetime.now()
        log_action('card_unban', 'card', card_id, f'卡片 #{card_id} 已解封')
        notify_card_status(card, current_user.id)
        db.session.commit()
        flash('卡片已解封', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/toggle_top', methods=['POST'])
@admin_required
def card_toggle_top(card_id):
    card = db.session.get(Card, card_id)
    if card:
        card.is_top = 0 if card.is_top else 1
        card.updated_at = datetime.now()
        log_action('card_toggle_top', 'card', card_id, f'卡片 #{card_id} 置顶状态: {card.is_top}')
        db.session.commit()
        flash('置顶状态已更新', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/delete', methods=['POST'])
@admin_required
def card_delete(card_id):
    card = db.session.get(Card, card_id)
    if card:
        now = datetime.now()
        card.deleted_at = now
        related_comments = db.session.execute(
            db.select(Comment).where(Comment.pid == card_id, Comment.deleted_at.is_(None))
        ).scalars().all()
        for c in related_comments:
            c.deleted_at = now
        log_action('card_delete', 'card', card_id, f'卡片 #{card_id} 已删除')
        db.session.commit()
        flash('卡片已删除', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/batch', methods=['POST'])
@admin_required
def cards_batch():
    action = request.form.get('batch_action', '').strip()
    card_ids = request.form.getlist('card_ids', type=int)

    if not card_ids or not action:
        flash('请选择卡片和操作', 'error')
        return redirect(url_for('admin.cards_list'))

    count = 0
    now = datetime.now()
    for cid in card_ids:
        card = db.session.get(Card, cid)
        if not card or card.deleted_at is not None:
            continue
        if action == 'approve':
            card.status = 1
        elif action == 'reject':
            card.status = 2
        elif action == 'ban':
            card.status = 3
        elif action == 'delete':
            card.deleted_at = now
            related_comments = db.session.execute(
                db.select(Comment).where(Comment.pid == cid, Comment.deleted_at.is_(None))
            ).scalars().all()
            for c in related_comments:
                c.deleted_at = now
        else:
            continue
        card.updated_at = now
        count += 1

    db.session.commit()
    action_names = {'approve': '通过', 'reject': '拒绝', 'ban': '封禁', 'delete': '删除'}
    log_action('cards_batch', 'card', 0, f'批量{action_names.get(action, "操作")} {count} 条卡片')
    flash(f'已{action_names.get(action, "操作")} {count} 条卡片', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/ban_user/<int:user_id>', methods=['POST'])
@admin_required
def cards_ban_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('admin.cards_list'))

    if user.id == current_user.id:
        flash('不能封禁自己的卡片', 'error')
        return redirect(url_for('admin.cards_list'))

    if user.is_super_admin and not current_user.is_super_admin:
        flash('无权封禁超级管理员的卡片', 'error')
        return redirect(url_for('admin.cards_list'))

    count = db.session.execute(
        db.update(Card).where(
            Card.user_id == user_id,
            Card.deleted_at.is_(None),
            Card.status == 1
        ).values(status=3, updated_at=datetime.now())
    ).rowcount
    log_action('cards_ban_user', 'user', user_id, f'封禁用户 {user.display_name} 的 {count} 条卡片')
    db.session.commit()
    flash(f'已封禁用户 {user.display_name} 的 {count} 条已通过卡片', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/users')
@admin_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', type=int)
    role_filter = request.args.get('role', type=int)

    query = db.select(User)
    if status_filter is not None:
        query = query.where(User.status == status_filter)
    if role_filter is not None:
        query = query.where(User.roles_id.contains([role_filter]))
    if search:
        escaped = _escape_like(search)
        query = query.where(
            or_(
                User.username.ilike(f'%{escaped}%'),
                User.nickname.ilike(f'%{escaped}%'),
                User.email.ilike(f'%{escaped}%'),
                User.number.ilike(f'%{escaped}%'),
                User.phone.ilike(f'%{escaped}%')
            )
        )
    query = query.order_by(desc(User.created_at))

    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    users = pagination.items
    return render_template("admin/users.html", users=users, pagination=pagination, search=search,
                           status_filter=status_filter, role_filter=role_filter)


@admin.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def user_toggle_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('不能修改自己的状态', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.is_super_admin and not current_user.is_super_admin:
        flash('无权修改超级管理员状态', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    user.status = 1 if user.status == 0 else 0
    user.updated_at = datetime.now()
    action_text = '封禁' if user.status == 1 else '解封'
    log_action('user_toggle_status', 'user', user.id, f'{action_text}用户 {user.display_name}')
    db.session.commit()
    flash('用户状态已更新', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin.route('/users/<int:user_id>/ban', methods=['POST'])
@admin_required
def user_ban(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('不能封禁自己', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.is_super_admin and not current_user.is_super_admin:
        flash('无权封禁超级管理员', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    reason = request.form.get('ban_reason', '').strip()
    if not reason:
        flash('请填写封禁原因', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    tags_str = request.form.get('ban_tags', '').strip()
    tags_list = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

    user.status = 1
    user.updated_at = datetime.now()

    record = BanRecord(
        user_id=user.id,
        username=user.display_name,
        reason=reason,
        tags=tags_list,
        banned_by=current_user.id,
        banned_by_name=current_user.display_name
    )
    db.session.add(record)
    log_action('user_ban', 'user', user.id, f'封禁用户 {user.display_name}，原因: {reason}')
    db.session.commit()
    flash(f'用户 {user.display_name} 已封禁', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin.route('/users/<int:user_id>/unban', methods=['POST'])
@admin_required
def user_unban(user_id):
    user = db.session.get(User, user_id)
    if not user or user.id == current_user.id:
        flash('不能修改自己的状态', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    user.status = 0
    user.updated_at = datetime.now()

    active_ban = db.session.execute(
        db.select(BanRecord).where(
            BanRecord.user_id == user.id,
            BanRecord.unbanned_at.is_(None)
        ).order_by(desc(BanRecord.created_at))
    ).scalar()
    if active_ban:
        active_ban.unbanned_at = datetime.now()

    log_action('user_unban', 'user', user.id, f'解封用户 {user.display_name}')
    db.session.commit()
    flash(f'用户 {user.display_name} 已解封', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('不能删除自己', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    if user.is_super_admin and not current_user.is_super_admin:
        flash('无权删除超级管理员', 'error')
        return redirect(request.referrer or url_for('admin.users_list'))

    now = datetime.now()

    related_cards = db.session.execute(
        db.select(Card).where(Card.user_id == user_id, Card.deleted_at.is_(None))
    ).scalars().all()
    for c in related_cards:
        c.deleted_at = now

    related_comments = db.session.execute(
        db.select(Comment).where(Comment.user_id == user_id, Comment.deleted_at.is_(None))
    ).scalars().all()
    for c in related_comments:
        c.deleted_at = now

    related_goods = db.session.execute(
        db.select(Good).where(Good.uid == user_id)
    ).scalars().all()
    for g in related_goods:
        db.session.delete(g)

    user.deleted_at = now
    log_action('user_delete', 'user', user.id, f'删除用户 {user.display_name}')
    db.session.commit()
    flash('用户已删除', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin.route('/comments')
@admin_required
def comments_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', type=int)

    query = db.select(Comment).where(Comment.deleted_at.is_(None))
    if status_filter is not None:
        query = query.where(Comment.status == status_filter)
    if search:
        escaped = _escape_like(search)
        conditions = [Comment.content.ilike(f'%{escaped}%')]
        if search.isdigit():
            conditions.append(Comment.id == int(search))
        author_subq = db.select(User.id).where(or_(User.username.ilike(f'%{escaped}%'), User.nickname.ilike(f'%{escaped}%')))
        conditions.append(Comment.user_id.in_(author_subq))
        query = query.where(or_(*conditions))
    query = query.order_by(desc(Comment.created_at))

    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    comments = pagination.items
    return render_template("admin/comments.html", comments=comments, pagination=pagination, search=search, status_filter=status_filter)


@admin.route('/comments/<int:comment_id>/approve', methods=['POST'])
@admin_required
def comment_approve(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        flash('评论不存在', 'error')
        return redirect(request.referrer or url_for('admin.comments_list'))
    comment.status = 1
    comment.updated_at = datetime.now()
    if comment.pid:
        card = db.session.get(Card, comment.pid)
        if card:
            card.comments = (card.comments or 0) + 1
    log_action('comment_approve', 'comment', comment_id, f'评论 #{comment_id} 审核通过')
    notify_comment_status(comment, current_user.id)
    db.session.commit()
    flash('评论已通过', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/comments/<int:comment_id>/reject', methods=['POST'])
@admin_required
def comment_reject(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        flash('评论不存在', 'error')
        return redirect(request.referrer or url_for('admin.comments_list'))
    comment.status = 2
    comment.updated_at = datetime.now()
    log_action('comment_reject', 'comment', comment_id, f'评论 #{comment_id} 审核拒绝')
    notify_comment_status(comment, current_user.id)
    db.session.commit()
    flash('评论已拒绝', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/comments/<int:comment_id>/ban', methods=['POST'])
@admin_required
def comment_ban(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        flash('评论不存在', 'error')
        return redirect(request.referrer or url_for('admin.comments_list'))
    was_approved = comment.status == 1
    comment.status = 3
    comment.updated_at = datetime.now()
    if was_approved and comment.pid:
        card = db.session.get(Card, comment.pid)
        if card and card.comments > 0:
            card.comments -= 1
    log_action('comment_ban', 'comment', comment_id, f'评论 #{comment_id} 已封禁')
    notify_comment_status(comment, current_user.id)
    db.session.commit()
    flash('评论已封禁', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/comments/<int:comment_id>/unban', methods=['POST'])
@admin_required
def comment_unban(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment or comment.deleted_at is not None:
        flash('评论不存在', 'error')
        return redirect(request.referrer or url_for('admin.comments_list'))
    comment.status = 1
    comment.updated_at = datetime.now()
    if comment.pid:
        card = db.session.get(Card, comment.pid)
        if card:
            card.comments = (card.comments or 0) + 1
    log_action('comment_unban', 'comment', comment_id, f'评论 #{comment_id} 已解封')
    notify_comment_status(comment, current_user.id)
    db.session.commit()
    flash('评论已解封', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/comments/batch', methods=['POST'])
@admin_required
def comments_batch():
    action = request.form.get('batch_action', '').strip()
    comment_ids = request.form.getlist('comment_ids', type=int)

    if not comment_ids or not action:
        flash('请选择评论和操作', 'error')
        return redirect(url_for('admin.comments_list'))

    count = 0
    now = datetime.now()
    for cid in comment_ids:
        comment = db.session.get(Comment, cid)
        if not comment or comment.deleted_at is not None:
            continue
        if action == 'approve':
            if comment.status != 1:
                comment.status = 1
                if comment.pid:
                    card = db.session.get(Card, comment.pid)
                    if card:
                        card.comments = (card.comments or 0) + 1
        elif action == 'reject':
            comment.status = 2
        elif action == 'ban':
            was_approved = comment.status == 1
            comment.status = 3
            if was_approved and comment.pid:
                card = db.session.get(Card, comment.pid)
                if card and card.comments > 0:
                    card.comments -= 1
        elif action == 'delete':
            comment.deleted_at = now
            if comment.pid:
                card = db.session.get(Card, comment.pid)
                if card and card.comments > 0:
                    card.comments -= 1
        else:
            continue
        comment.updated_at = now
        count += 1

    db.session.commit()
    action_names = {'approve': '通过', 'reject': '拒绝', 'ban': '封禁', 'delete': '删除'}
    log_action('comments_batch', 'comment', 0, f'批量{action_names.get(action, "操作")} {count} 条评论')
    flash(f'已{action_names.get(action, "操作")} {count} 条评论', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/comments/<int:comment_id>/delete', methods=['POST'])
@admin_required
def comment_delete(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment:
        comment.deleted_at = datetime.now()
        if comment.pid:
            card = db.session.get(Card, comment.pid)
            if card and card.comments > 0:
                card.comments -= 1
        log_action('comment_delete', 'comment', comment_id, f'评论 #{comment_id} 已删除')
        db.session.commit()
        flash('评论已删除', 'success')
    return redirect(request.referrer or url_for('admin.comments_list'))


@admin.route('/tags', methods=['GET', 'POST'])
@admin_required
def tags_list():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            new_tag = Tags(aid=1, user_id=current_user.id, name=name, status=0)
            db.session.add(new_tag)
            db.session.flush()
            log_action('tag_create', 'tag', new_tag.id, f'创建标签 {name}')
            db.session.commit()
            flash('标签已创建', 'success')
        else:
            flash('标签名称不能为空', 'error')
        return redirect(url_for('admin.tags_list'))

    tags = db.session.execute(
        db.select(Tags).where(Tags.deleted_at.is_(None)).order_by(Tags.id)
    ).scalars().all()
    return render_template("admin/tags.html", tags=tags)


@admin.route('/tags/<int:tag_id>/delete', methods=['POST'])
@admin_required
def tag_delete(tag_id):
    tag = db.session.get(Tags, tag_id)
    if tag:
        tag.deleted_at = datetime.now()
        db.session.execute(
            db.update(TagsMap).where(TagsMap.tag_id == tag_id).values(deleted_at=datetime.now())
        )
        log_action('tag_delete', 'tag', tag_id, f'删除标签 {tag.name}')
        db.session.commit()
        flash('标签已删除', 'success')
    return redirect(request.referrer or url_for('admin.tags_list'))


@admin.route('/tags/<int:tag_id>/toggle_status', methods=['POST'])
@admin_required
def tag_toggle_status(tag_id):
    tag = db.session.get(Tags, tag_id)
    if tag:
        tag.status = 1 if tag.status == 0 else 0
        log_action('tag_toggle_status', 'tag', tag_id, f'标签 {tag.name} 状态切换为 {"禁用" if tag.status == 1 else "启用"}')
        db.session.commit()
        flash('标签状态已更新', 'success')
    return redirect(request.referrer or url_for('admin.tags_list'))


@admin.route('/settings')
@admin.route('/settings/<group>')
@super_admin_required
def settings(group=None):
    ensure_default_configs()

    group_dict = {g['key']: g for g in SITE_CONFIG_GROUPS}
    if group and group not in group_dict:
        abort(404)

    if request.method == 'GET' and request.args.get('save') == '1':
        flash('配置已保存', 'success')

    config_dict = get_site_config()
    active_group = group_dict.get(group) if group else group_dict.get('basic')

    return render_template("admin/settings.html",
                           config_dict=config_dict,
                           config_labels=SITE_CONFIG_LABELS,
                           config_groups=SITE_CONFIG_GROUPS,
                           config_hints=SITE_CONFIG_HINTS,
                           active_group=active_group,
                           current_group=group or 'basic',
                           available_themes=AVAILABLE_THEMES)


@admin.route('/settings/save', methods=['POST'])
@super_admin_required
def settings_save():
    group = request.form.get('_group', 'basic')
    try:
        for key in request.form:
            if key.startswith('_'):
                continue
            value = request.form.get(key)
            set_config(key, value)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('保存设置失败，请重试', 'error')
        return redirect(url_for('admin.settings', group=group))
    if group == 'appearance':
        clear_template_cache()
    return redirect(url_for('admin.settings', group=group, save='1'))


@admin.route('/users/<int:user_id>/set_role', methods=['POST'])
@super_admin_required
def user_set_role(user_id):
    user = db.session.get(User, user_id)
    if not user or user.deleted_at is not None:
        flash('用户不存在', 'error')
        return redirect(url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('不能修改自己的角色', 'error')
        return redirect(url_for('admin.users_list'))

    role = request.form.get('role', '').strip()
    role_map = {
        'super_admin': [0],
        'admin': [1],
        'user': [2],
    }

    if role not in role_map:
        flash('无效的角色', 'error')
        return redirect(url_for('admin.users_list'))

    user.roles_id = role_map[role]
    user.updated_at = datetime.now()
    role_names = {'super_admin': '超级管理员', 'admin': '管理员', 'user': '普通用户'}
    log_action('user_set_role', 'user', user.id, f'用户 {user.display_name} 角色设为 {role_names[role]}')
    db.session.commit()
    flash(f'已将 {user.display_name} 的角色设置为 {role_names[role]}', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin.route('/deleted_users')
@super_admin_required
def deleted_users_list():
    page = request.args.get('page', 1, type=int)

    query = db.select(DeletedUser).order_by(desc(DeletedUser.created_at))
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    deleted_users = pagination.items
    return render_template("admin/deleted_users.html", deleted_users=deleted_users, pagination=pagination)


@admin.route('/deleted_users/<int:archive_id>/restore', methods=['POST'])
@super_admin_required
def deleted_user_restore(archive_id):
    archive = db.session.get(DeletedUser, archive_id)
    if not archive:
        flash('归档记录不存在', 'error')
        return redirect(url_for('admin.deleted_users_list'))

    user = db.session.get(User, archive.original_id)
    if not user:
        flash('原用户记录不存在', 'error')
        return redirect(url_for('admin.deleted_users_list'))

    if user.deleted_at is not None:
        user.deleted_at = None

    user.status = 0
    user.roles_id = archive.roles_id
    if user.username.startswith('[注销中]'):
        user.username = user.username[5:]
    if user.nickname.startswith('[注销中]'):
        user.nickname = user.nickname[5:]
    user.updated_at = datetime.now()

    db.session.delete(archive)
    log_action('user_restore', 'user', user.id, f'恢复用户 {user.display_name}')
    db.session.commit()
    flash(f'用户 {user.display_name} 已恢复（其发布的内容需在卡片/评论管理中单独恢复）', 'success')
    return redirect(url_for('admin.deleted_users_list'))


@admin.route('/deleted_users/<int:archive_id>/purge', methods=['POST'])
@super_admin_required
def deleted_user_purge(archive_id):
    archive = db.session.get(DeletedUser, archive_id)
    if not archive:
        flash('归档记录不存在', 'error')
        return redirect(url_for('admin.deleted_users_list'))

    user = db.session.get(User, archive.original_id)

    now = datetime.now()
    if user:
        related_cards = db.session.execute(
            db.select(Card).where(Card.user_id == user.id, Card.deleted_at.is_(None))
        ).scalars().all()
        for c in related_cards:
            c.deleted_at = now

        related_comments = db.session.execute(
            db.select(Comment).where(Comment.user_id == user.id, Comment.deleted_at.is_(None))
        ).scalars().all()
        for c in related_comments:
            c.deleted_at = now

        user.deleted_at = now
        user.status = 1

    db.session.delete(archive)
    log_action('user_purge', 'user', archive.original_id, f'永久删除用户数据（归档 #{archive_id}）')
    db.session.commit()
    flash('用户数据已永久删除', 'success')
    return redirect(url_for('admin.deleted_users_list'))


@admin.route('/ban_records')
@admin_required
def ban_records_list():
    page = request.args.get('page', 1, type=int)

    query = db.select(BanRecord).order_by(desc(BanRecord.created_at))
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    records = pagination.items
    return render_template("admin/ban_records.html", records=records, pagination=pagination)


@admin.route('/comment/<int:comment_id>/toggle_good', methods=['POST'])
@admin_required
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


@admin.route('/pending_users')
@admin_required
def pending_users_list():
    page = request.args.get('page', 1, type=int)
    query = db.select(User).where(User.status == 2).order_by(desc(User.created_at))
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    users = pagination.items
    return render_template("admin/pending_users.html", users=users, pagination=pagination)


@admin.route('/pending_users/<int:user_id>/approve', methods=['POST'])
@admin_required
def pending_user_approve(user_id):
    user = db.session.get(User, user_id)
    if not user or user.status != 2:
        flash('用户不存在或不在审核状态', 'error')
        return redirect(request.referrer or url_for('admin.pending_users_list'))
    user.status = 0
    user.updated_at = datetime.now()
    log_action('user_approve', 'user', user.id, f'审核通过用户 {user.display_name}')
    db.session.commit()
    flash(f'用户 {user.display_name} 已审核通过', 'success')
    return redirect(request.referrer or url_for('admin.pending_users_list'))


@admin.route('/pending_users/<int:user_id>/reject', methods=['POST'])
@admin_required
def pending_user_reject(user_id):
    user = db.session.get(User, user_id)
    if not user or user.status != 2:
        flash('用户不存在或不在审核状态', 'error')
        return redirect(request.referrer or url_for('admin.pending_users_list'))
    user.status = 1
    user.updated_at = datetime.now()
    log_action('user_reject', 'user', user.id, f'拒绝用户 {user.display_name} 注册')
    db.session.commit()
    flash(f'用户 {user.display_name} 已拒绝', 'success')
    return redirect(request.referrer or url_for('admin.pending_users_list'))


@admin.route('/pending_users/batch', methods=['POST'])
@admin_required
def pending_users_batch():
    action = request.form.get('batch_action', '').strip()
    user_ids = request.form.getlist('user_ids', type=int)

    if not user_ids or not action:
        flash('请选择用户和操作', 'error')
        return redirect(url_for('admin.pending_users_list'))

    count = 0
    now = datetime.now()
    for uid in user_ids:
        user = db.session.get(User, uid)
        if not user or user.status != 2:
            continue
        if action == 'approve':
            user.status = 0
        elif action == 'reject':
            user.status = 1
        else:
            continue
        user.updated_at = now
        count += 1

    db.session.commit()
    action_names = {'approve': '通过', 'reject': '拒绝'}
    log_action('users_batch_review', 'user', 0, f'批量{action_names.get(action, "操作")} {count} 个用户')
    flash(f'已{action_names.get(action, "操作")} {count} 个用户', 'success')
    return redirect(request.referrer or url_for('admin.pending_users_list'))


@admin.route('/invite_codes')
@super_admin_required
def invite_codes_list():
    from sqlalchemy import or_, func as sa_func
    page = request.args.get('page', 1, type=int)
    code_filter = request.args.get('filter', 'all')

    valid_cond = (InviteCode.status == 0) & (
        or_(InviteCode.max_uses == 0, InviteCode.used_count < InviteCode.max_uses)
    ) & (or_(InviteCode.expires_at.is_(None), InviteCode.expires_at > datetime.now()))

    query = db.select(InviteCode).order_by(desc(InviteCode.created_at))
    if code_filter == 'unused':
        query = query.where(valid_cond)
    elif code_filter == 'used':
        query = query.where(~valid_cond)

    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    codes = pagination.items

    total_all = db.session.execute(db.select(sa_func.count(InviteCode.id))).scalar()
    total_unused = db.session.execute(db.select(sa_func.count(InviteCode.id)).where(valid_cond)).scalar()
    total_used = (total_all or 0) - (total_unused or 0)

    generated_codes = session.pop('generated_invite_codes', None)

    return render_template("admin/invite_codes.html", codes=codes, pagination=pagination, code_filter=code_filter, total_all=total_all, total_unused=total_unused, total_used=total_used, generated_codes=generated_codes)


@admin.route('/invite_codes/generate', methods=['POST'])
@super_admin_required
def invite_codes_generate():
    import secrets
    from datetime import timedelta
    from sqlalchemy.exc import IntegrityError

    count = request.form.get('count', 1, type=int)
    max_uses = request.form.get('max_uses', 0, type=int)
    days = request.form.get('expires_days', 0, type=int)

    count = min(max(count, 1), 50)
    generated_codes = []

    for _ in range(count):
        for _attempt in range(5):
            code = secrets.token_urlsafe(12).replace('-', '').replace('_', '').upper()[:10]
            expires_at = None
            if days > 0:
                expires_at = datetime.now() + timedelta(days=days)
            new_code = InviteCode(
                code=code,
                created_by=current_user.id,
                max_uses=max_uses,
                expires_at=expires_at,
            )
            db.session.add(new_code)
            try:
                db.session.flush()
                generated_codes.append(code)
                break
            except IntegrityError:
                db.session.rollback()

    db.session.commit()
    session['generated_invite_codes'] = generated_codes
    log_action('invite_codes_generate', 'invite_code', 0, f'生成 {len(generated_codes)} 个邀请码')
    flash(f'已生成 {len(generated_codes)} 个邀请码', 'success')
    return redirect(url_for('admin.invite_codes_list'))


@admin.route('/invite_codes/<int:code_id>/toggle_status', methods=['POST'])
@super_admin_required
def invite_code_toggle_status(code_id):
    code = db.session.get(InviteCode, code_id)
    if code:
        code.status = 1 if code.status == 0 else 0
        log_action('invite_code_toggle', 'invite_code', code_id, f'邀请码 {code.code} 状态切换')
        db.session.commit()
        flash('邀请码状态已更新', 'success')
    return redirect(request.referrer or url_for('admin.invite_codes_list'))


@admin.route('/invite_codes/<int:code_id>/delete', methods=['POST'])
@super_admin_required
def invite_code_delete(code_id):
    code = db.session.get(InviteCode, code_id)
    if code:
        db.session.delete(code)
        log_action('invite_code_delete', 'invite_code', code_id, f'删除邀请码 {code.code}')
        db.session.commit()
        flash('邀请码已删除', 'success')
    return redirect(request.referrer or url_for('admin.invite_codes_list'))


@admin.route('/invite_codes/export')
@super_admin_required
def invite_codes_export():
    import csv
    from io import StringIO
    from flask import Response as FlaskResponse

    codes = db.session.execute(
        db.select(InviteCode).order_by(desc(InviteCode.created_at))
    ).scalars().all()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['邀请码', '使用次数', '最大使用次数', '有效期', '状态', '创建时间'])
    for c in codes:
        status_text = '有效' if c.is_valid else ('已禁用' if c.status != 0 else ('已用完' if c.max_uses > 0 and c.used_count >= c.max_uses else '已过期'))
        expires_text = c.expires_at.strftime('%Y-%m-%d %H:%M') if c.expires_at else '永久'
        writer.writerow([c.code, c.used_count, c.max_uses if c.max_uses > 0 else '不限', expires_text, status_text, c.created_at.strftime('%Y-%m-%d %H:%M')])

    output = si.getvalue()
    si.close()

    return FlaskResponse(
        output,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=invite_codes.csv'}
    )


@admin.route('/audit_logs')
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    search = request.args.get('search', '').strip()

    query = db.select(AuditLog).order_by(desc(AuditLog.created_at))
    if action_filter:
        query = query.where(AuditLog.action == action_filter)
    if search:
        escaped = search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.where(
            or_(
                AuditLog.username.ilike(f'%{escaped}%'),
                AuditLog.detail.ilike(f'%{escaped}%'),
            )
        )

    pagination = db.paginate(query, page=page, per_page=30, error_out=False)
    logs = pagination.items

    action_types = db.session.execute(
        db.select(AuditLog.action).distinct()
    ).scalars().all()

    return render_template("admin/audit_logs.html", logs=logs, pagination=pagination,
                           action_filter=action_filter, search=search,
                           action_types=action_types)


@admin.route('/images')
@admin_required
def images_list():
    page = request.args.get('page', 1, type=int)
    aid_filter = request.args.get('aid', type=int)
    orphan_only = request.args.get('orphan', '0') == '1'

    query = db.select(Images).where(Images.deleted_at.is_(None))
    if aid_filter is not None:
        query = query.where(Images.aid == aid_filter)
    if orphan_only:
        card_ids_subq = db.select(Card.id).where(Card.deleted_at.is_(None))
        comment_ids_subq = db.select(Comment.id).where(Comment.deleted_at.is_(None))
        query = query.where(
            or_(
                (Images.aid == 1) & (Images.pid.notin_(card_ids_subq)),
                (Images.aid == 2) & (Images.pid.notin_(comment_ids_subq)),
                Images.aid.notin_([1, 2]),
            )
        )
    query = query.order_by(desc(Images.created_at))

    pagination = db.paginate(query, page=page, per_page=30, error_out=False)
    images = pagination.items

    total = db.session.execute(
        db.select(func.count()).select_from(Images).where(Images.deleted_at.is_(None))
    ).scalar() or 0

    orphan_count = db.session.execute(
        db.select(func.count()).select_from(Images).where(
            Images.deleted_at.is_(None),
            or_(
                (Images.aid == 1) & (Images.pid.notin_(db.select(Card.id).where(Card.deleted_at.is_(None)))),
                (Images.aid == 2) & (Images.pid.notin_(db.select(Comment.id).where(Comment.deleted_at.is_(None)))),
                Images.aid.notin_([1, 2]),
            )
        )
    ).scalar() or 0

    return render_template("admin/images.html", images=images, pagination=pagination,
                           aid_filter=aid_filter, orphan_only=orphan_only,
                           total=total, orphan_count=orphan_count)


@admin.route('/images/<int:image_id>/delete', methods=['POST'])
@admin_required
def image_delete(image_id):
    img = db.session.get(Images, image_id)
    if img:
        img.deleted_at = datetime.now()
        log_action('image_delete', 'image', image_id, f'删除图片 {img.url[:50]}')
        db.session.commit()
        flash('图片已删除', 'success')
    return redirect(request.referrer or url_for('admin.images_list'))


@admin.route('/images/clean_orphan', methods=['POST'])
@admin_required
def images_clean_orphan():
    card_ids_subq = db.select(Card.id).where(Card.deleted_at.is_(None))
    comment_ids_subq = db.select(Comment.id).where(Comment.deleted_at.is_(None))

    orphans = db.session.execute(
        db.select(Images).where(
            Images.deleted_at.is_(None),
            or_(
                (Images.aid == 1) & (Images.pid.notin_(card_ids_subq)),
                (Images.aid == 2) & (Images.pid.notin_(comment_ids_subq)),
                Images.aid.notin_([1, 2]),
            )
        )
    ).scalars().all()

    now = datetime.now()
    for img in orphans:
        img.deleted_at = now

    log_action('images_clean_orphan', 'image', 0, f'清理 {len(orphans)} 张孤立图片')
    db.session.commit()
    flash(f'已清理 {len(orphans)} 张孤立图片', 'success')
    return redirect(url_for('admin.images_list'))


@admin.route('/notifications')
@admin_required
def notifications_list():
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '').strip()
    user_search = request.args.get('user_search', '').strip()
    read_filter = request.args.get('read', '').strip()

    query = db.select(Notification).order_by(desc(Notification.created_at))
    if type_filter:
        query = query.where(Notification.type == type_filter)
    if user_search:
        escaped = _escape_like(user_search)
        user_subq = db.select(User.id).where(
            or_(User.username.ilike(f'%{escaped}%'), User.nickname.ilike(f'%{escaped}%'))
        )
        query = query.where(Notification.user_id.in_(user_subq))
    if read_filter == 'unread':
        query = query.where(Notification.is_read == 0)
    elif read_filter == 'read':
        query = query.where(Notification.is_read == 1)

    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    notifications = pagination.items

    type_list = db.session.execute(
        db.select(Notification.type).distinct()
    ).scalars().all()

    total = db.session.execute(
        db.select(func.count()).select_from(Notification)
    ).scalar() or 0
    unread = db.session.execute(
        db.select(func.count()).select_from(Notification).where(Notification.is_read == 0)
    ).scalar() or 0

    return render_template("admin/notifications.html", notifications=notifications,
                           pagination=pagination, type_filter=type_filter,
                           user_search=user_search, type_list=type_list,
                           read_filter=read_filter, total=total, unread=unread)


@admin.route('/notifications/send', methods=['GET', 'POST'])
@admin_required
def notification_send():
    if request.method == 'POST':
        target = request.form.get('target', 'all').strip()
        user_id_val = request.form.get('user_id', type=int)
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        ntype = request.form.get('type', 'system').strip()

        if not title:
            flash('通知标题不能为空', 'error')
            return redirect(url_for('admin.notification_send'))

        if target == 'single' and not user_id_val:
            flash('请指定用户ID', 'error')
            return redirect(url_for('admin.notification_send'))

        count = 0
        if target == 'all':
            users = db.session.execute(
                db.select(User).where(User.deleted_at.is_(None), User.status == 0)
            ).scalars().all()
            for u in users:
                push_notification(u.id, ntype, title, content)
                count += 1
        elif target == 'single':
            user = db.session.get(User, user_id_val)
            if user:
                push_notification(user.id, ntype, title, content)
                count = 1
            else:
                flash('用户不存在', 'error')
                return redirect(url_for('admin.notification_send'))

        log_action('notification_send', 'notification', 0, f'发送通知「{title}」给 {count} 人')
        db.session.commit()
        flash(f'通知已发送给 {count} 人', 'success')
        return redirect(url_for('admin.notifications_list'))

    return render_template("admin/notification_send.html")


@admin.route('/notifications/<int:nid>/delete', methods=['POST'])
@admin_required
def notification_delete(nid):
    n = db.session.get(Notification, nid)
    if n:
        db.session.delete(n)
        log_action('notification_delete', 'notification', nid, f'删除通知 #{nid}')
        db.session.commit()
        flash('通知已删除', 'success')
    return redirect(request.referrer or url_for('admin.notifications_list'))


@admin.route('/notifications/batch_delete', methods=['POST'])
@admin_required
def notifications_batch_delete():
    ids = request.form.getlist('notification_ids', type=int)
    if not ids:
        flash('请选择通知', 'error')
        return redirect(url_for('admin.notifications_list'))

    count = 0
    for nid in ids:
        n = db.session.get(Notification, nid)
        if n:
            db.session.delete(n)
            count += 1

    log_action('notifications_batch_delete', 'notification', 0, f'批量删除 {count} 条通知')
    db.session.commit()
    flash(f'已删除 {count} 条通知', 'success')
    return redirect(url_for('admin.notifications_list'))


@admin.route('/cards/<int:card_id>/edit', methods=['GET', 'POST'])
@admin_required
def card_edit(card_id):
    card = db.session.get(Card, card_id)
    if not card or card.deleted_at is not None:
        abort(404)

    if request.method == 'POST':
        new_content = request.form.get('content', '').strip()
        new_cover = request.form.get('cover', '').strip()
        new_tags_str = request.form.get('tags', '').strip()

        if new_content:
            card.content = new_content
        if new_cover is not None:
            card.cover = new_cover

        new_target = request.form.get('target', '').strip()
        if card.data is None:
            card.data = {}
        if new_target:
            card.data['target'] = new_target
        elif 'target' in card.data:
            del card.data['target']

        if new_tags_str:
            tag_names = [t.strip() for t in new_tags_str.split(',') if t.strip()]
            tag_ids = []
            for tname in tag_names:
                existing = db.session.execute(
                    db.select(Tags).where(Tags.name == tname, Tags.aid == 1, Tags.deleted_at.is_(None))
                ).scalar()
                if existing:
                    tag_ids.append(existing.id)
                else:
                    new_tag = Tags(aid=1, user_id=current_user.id, name=tname, status=0)
                    db.session.add(new_tag)
                    db.session.flush()
                    tag_ids.append(new_tag.id)
            card.tags = tag_ids
        else:
            card.tags = None

        card.updated_at = datetime.now()
        log_action('card_edit', 'card', card_id, f'编辑卡片 #{card_id}')
        db.session.commit()
        flash('卡片已更新', 'success')
        return redirect(url_for('admin.card_detail', card_id=card_id))

    all_tags = db.session.execute(
        db.select(Tags).where(Tags.aid == 1, Tags.deleted_at.is_(None)).order_by(Tags.name)
    ).scalars().all()

    card_tag_names = []
    if card.tags:
        card_tags = db.session.execute(
            db.select(Tags).where(Tags.id.in_(card.tags), Tags.deleted_at.is_(None))
        ).scalars().all()
        card_tag_names = [t.name for t in card_tags]

    return render_template("admin/card_edit.html", card=card, all_tags=all_tags, card_tag_names=card_tag_names)


@admin.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    user_cards_count = db.session.execute(
        db.select(func.count()).select_from(Card).where(
            Card.user_id == user_id, Card.deleted_at.is_(None)
        )
    ).scalar() or 0

    user_comments_count = db.session.execute(
        db.select(func.count()).select_from(Comment).where(
            Comment.user_id == user_id, Comment.deleted_at.is_(None)
        )
    ).scalar() or 0

    user_goods_count = db.session.execute(
        db.select(func.count()).select_from(Good).where(Good.uid == user_id)
    ).scalar() or 0

    user_images_count = db.session.execute(
        db.select(func.count()).select_from(Images).where(
            Images.user_id == user_id, Images.deleted_at.is_(None)
        )
    ).scalar() or 0

    recent_cards = db.session.execute(
        db.select(Card).where(Card.user_id == user_id, Card.deleted_at.is_(None))
        .order_by(desc(Card.created_at)).limit(5)
    ).scalars().all()

    recent_comments = db.session.execute(
        db.select(Comment).where(Comment.user_id == user_id, Comment.deleted_at.is_(None))
        .order_by(desc(Comment.created_at)).limit(5)
    ).scalars().all()

    ban_records = db.session.execute(
        db.select(BanRecord).where(BanRecord.user_id == user_id).order_by(desc(BanRecord.created_at)).limit(5)
    ).scalars().all()

    notifications_count = db.session.execute(
        db.select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    ).scalar() or 0

    return render_template("admin/user_detail.html", user=user,
                           user_cards_count=user_cards_count,
                           user_comments_count=user_comments_count,
                           user_goods_count=user_goods_count,
                           user_images_count=user_images_count,
                           recent_cards=recent_cards,
                           recent_comments=recent_comments,
                           ban_records=ban_records,
                           notifications_count=notifications_count)


@admin.route('/export/<datatype>')
@super_admin_required
def data_export(datatype):
    import csv
    from io import StringIO
    from flask import Response as FlaskResponse

    si = StringIO()
    writer = csv.writer(si)

    if datatype == 'cards':
        writer.writerow(['ID', '内容', '作者ID', '作者', '状态', '置顶', '点赞', '浏览', '评论数', '创建时间'])
        cards = db.session.execute(
            db.select(Card).where(Card.deleted_at.is_(None)).order_by(desc(Card.created_at))
        ).scalars().all()
        for c in cards:
            status_map = {0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已封禁'}
            writer.writerow([c.id, (c.content or '')[:200], c.user_id,
                             c.author.display_name if c.author else '',
                             status_map.get(c.status, str(c.status)),
                             '是' if c.is_top else '否', c.good, c.views, c.comments,
                             c.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        filename = 'cards.csv'
    elif datatype == 'users':
        writer.writerow(['ID', '编号', '用户名', '昵称', '邮箱', '手机', '角色', '状态', '注册时间'])
        users = db.session.execute(db.select(User).order_by(desc(User.created_at))).scalars().all()
        for u in users:
            role = '超管' if u.is_super_admin else ('管理员' if u.is_admin else '用户')
            status_map = {0: '正常', 1: '封禁', 2: '待审核'}
            writer.writerow([u.id, u.number, u.username, u.nickname, u.email, u.phone,
                             role, status_map.get(u.status, str(u.status)),
                             u.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        filename = 'users.csv'
    elif datatype == 'comments':
        writer.writerow(['ID', '内容', '评论者ID', '评论者', '卡片ID', '状态', '点赞', '创建时间'])
        comments = db.session.execute(
            db.select(Comment).where(Comment.deleted_at.is_(None)).order_by(desc(Comment.created_at))
        ).scalars().all()
        for c in comments:
            status_map = {0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已封禁'}
            writer.writerow([c.id, (c.content or '')[:200], c.user_id,
                             c.user.display_name if c.user else '',
                             c.pid, status_map.get(c.status, str(c.status)), c.goods,
                             c.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        filename = 'comments.csv'
    elif datatype == 'audit_logs':
        writer.writerow(['ID', '操作人', '操作', '目标类型', '目标ID', '详情', 'IP', '时间'])
        logs = db.session.execute(
            db.select(AuditLog).order_by(desc(AuditLog.created_at)).limit(5000)
        ).scalars().all()
        for l in logs:
            writer.writerow([l.id, l.username, l.action, l.target_type, l.target_id,
                             l.detail, l.ip, l.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        filename = 'audit_logs.csv'
    else:
        abort(404)

    output = si.getvalue()
    si.close()

    return FlaskResponse(
        output,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin.route('/rate_limits')
@admin_required
def rate_limits_list():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    ip_search = request.args.get('ip', '').strip()

    query = db.select(RateLimitAttempt).order_by(desc(RateLimitAttempt.created_at))
    if action_filter:
        query = query.where(RateLimitAttempt.action == action_filter)
    if ip_search:
        query = query.where(RateLimitAttempt.ip.ilike(f'%{_escape_like(ip_search)}%'))

    pagination = db.paginate(query, page=page, per_page=30, error_out=False)
    records = pagination.items

    action_types = db.session.execute(
        db.select(RateLimitAttempt.action).distinct()
    ).scalars().all()

    total = db.session.execute(
        db.select(func.count()).select_from(RateLimitAttempt)
    ).scalar() or 0

    return render_template("admin/rate_limits.html", records=records, pagination=pagination,
                           action_filter=action_filter, ip_search=ip_search,
                           action_types=action_types, total=total)


@admin.route('/rate_limits/cleanup', methods=['POST'])
@admin_required
def rate_limits_cleanup():
    from datetime import timedelta
    days = request.form.get('days', 30, type=int)
    days = max(1, min(days, 365))
    cutoff = datetime.now() - timedelta(days=days)

    count = db.session.execute(
        db.delete(RateLimitAttempt).where(RateLimitAttempt.created_at < cutoff)
    ).rowcount

    log_action('rate_limits_cleanup', 'system', 0, f'清理 {days} 天前的频率限制记录 {count} 条')
    db.session.commit()
    flash(f'已清理 {count} 条 {days} 天前的记录', 'success')
    return redirect(url_for('admin.rate_limits_list'))


@admin.route('/system_info')
@super_admin_required
def system_info():
    import platform
    import sys

    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'flask_version': '',
        'sqlalchemy_version': '',
    }

    try:
        import flask
        info['flask_version'] = flask.__version__
    except Exception:
        pass
    try:
        import sqlalchemy
        info['sqlalchemy_version'] = sqlalchemy.__version__
    except Exception:
        pass

    db_tables = {}
    for table_name in ['cards', 'users', 'comments', 'images', 'good', 'tags', 'notifications',
                        'audit_logs', 'ban_records', 'invite_codes', 'rate_limit_attempts', 'system']:
        try:
            count = db.session.execute(db.text(f'SELECT COUNT(*) FROM {table_name}')).scalar()
            db_tables[table_name] = count
        except Exception:
            db_tables[table_name] = -1

    return render_template("admin/system_info.html", info=info, db_tables=db_tables)


@admin.route('/tags/merge', methods=['GET', 'POST'])
@super_admin_required
def tags_merge():
    if request.method == 'POST':
        source_id = request.form.get('source_id', type=int)
        target_id = request.form.get('target_id', type=int)

        if not source_id or not target_id:
            flash('请选择源标签和目标标签', 'error')
            return redirect(url_for('admin.tags_merge'))

        if source_id == target_id:
            flash('源标签和目标标签不能相同', 'error')
            return redirect(url_for('admin.tags_merge'))

        source_tag = db.session.get(Tags, source_id)
        target_tag = db.session.get(Tags, target_id)
        if not source_tag or not target_tag:
            flash('标签不存在', 'error')
            return redirect(url_for('admin.tags_merge'))

        affected_cards = 0
        cards = db.session.execute(
            db.select(Card).where(Card.deleted_at.is_(None))
        ).scalars().all()
        for card in cards:
            if card.tags and source_id in card.tags:
                card.tags = [target_id if t == source_id else t for t in card.tags]
                if target_id not in card.tags:
                    card.tags.append(target_id)
                affected_cards += 1

        source_tag.deleted_at = datetime.now()
        log_action('tags_merge', 'tag', source_id,
                   f'合并标签「{source_tag.name}」→「{target_tag.name}」，影响 {affected_cards} 张卡片')
        db.session.commit()
        flash(f'标签「{source_tag.name}」已合并到「{target_tag.name}」，影响 {affected_cards} 张卡片', 'success')
        return redirect(url_for('admin.tags_list'))

    tags = db.session.execute(
        db.select(Tags).where(Tags.aid == 1, Tags.deleted_at.is_(None)).order_by(Tags.name)
    ).scalars().all()

    return render_template("admin/tags_merge.html", tags=tags)