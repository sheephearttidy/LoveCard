from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_

from model.BanRecord import BanRecord
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.Images import Images
from model.Tags import Tags
from model.TagsMap import TagsMap
from model.User import User
from model.db import db
from utils.system import ensure_default_configs, set_config, get_site_config, SITE_CONFIG_LABELS, SITE_CONFIG_GROUPS, \
    SITE_CONFIG_HINTS

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
    comments_total = db.session.execute(db.select(func.count()).select_from(Comment).where(Comment.deleted_at.is_(None))).scalar() or 0
    goods_total = db.session.execute(db.select(func.count()).select_from(Good)).scalar() or 0

    recent_cards = db.session.execute(
        db.select(Card).where(Card.deleted_at.is_(None)).order_by(desc(Card.created_at)).limit(5)
    ).scalars().all()

    recent_users = db.session.execute(
        db.select(User).order_by(desc(User.created_at)).limit(5)
    ).scalars().all()

    return render_template("admin/dashboard.html",
                           cards_total=cards_total, cards_pending=cards_pending,
                           cards_approved=cards_approved, cards_banned=cards_banned,
                           users_total=users_total,
                           comments_total=comments_total, goods_total=goods_total,
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
        author_subq = db.select(User.id).where(User.username.ilike(f'%{escaped}%'))
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
        db.session.commit()
        flash('卡片已拒绝', 'success')
    return redirect(request.referrer or url_for('admin.cards_list'))


@admin.route('/cards/<int:card_id>/ban', methods=['POST'])
@admin_required
def card_ban(card_id):
    card = db.session.get(Card, card_id)
    if card:
        card.status = 3
        card.updated_at = datetime.now()
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

    count = db.session.execute(
        db.update(Card).where(
            Card.user_id == user_id,
            Card.deleted_at.is_(None),
            Card.status == 1
        ).values(status=3, updated_at=datetime.now())
    ).rowcount
    db.session.commit()
    flash(f'已封禁用户 {user.username} 的 {count} 条已通过卡片', 'success')
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
        username=user.username,
        reason=reason,
        tags=tags_list,
        banned_by=current_user.id,
        banned_by_name=current_user.username
    )
    db.session.add(record)
    db.session.commit()
    flash(f'用户 {user.username} 已封禁', 'success')
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

    db.session.commit()
    flash(f'用户 {user.username} 已解封', 'success')
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
        author_subq = db.select(User.id).where(User.username.ilike(f'%{escaped}%'))
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
        db.session.commit()
        flash('标签已删除', 'success')
    return redirect(request.referrer or url_for('admin.tags_list'))


@admin.route('/tags/<int:tag_id>/toggle_status', methods=['POST'])
@admin_required
def tag_toggle_status(tag_id):
    tag = db.session.get(Tags, tag_id)
    if tag:
        tag.status = 1 if tag.status == 0 else 0
        db.session.commit()
        flash('标签状态已更新', 'success')
    return redirect(request.referrer or url_for('admin.tags_list'))


@admin.route('/settings', methods=['GET', 'POST'])
@super_admin_required
def settings():
    ensure_default_configs()

    if request.method == 'POST':
        for key in request.form:
            value = request.form.get(key)
            set_config(key, value)
        db.session.commit()
        flash('配置已保存', 'success')
        return redirect(url_for('admin.settings'))

    config_dict = get_site_config()
    return render_template("admin/settings.html",
                           config_dict=config_dict,
                           config_labels=SITE_CONFIG_LABELS,
                           config_groups=SITE_CONFIG_GROUPS,
                           config_hints=SITE_CONFIG_HINTS)


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
    db.session.commit()

    role_names = {'super_admin': '超级管理员', 'admin': '管理员', 'user': '普通用户'}
    flash(f'已将 {user.username} 的角色设置为 {role_names[role]}', 'success')
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
    user.updated_at = datetime.now()

    db.session.delete(archive)
    db.session.commit()
    flash(f'用户 {user.username} 已恢复（其发布的内容需在卡片/评论管理中单独恢复）', 'success')
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