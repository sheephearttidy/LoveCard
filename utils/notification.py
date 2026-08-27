from model.Notification import Notification
from model.User import User
from model.db import db


def push_notification(user_id, ntype, title, content='', data=None):
    n = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        content=content,
        data=data,
    )
    db.session.add(n)
    return n


def notify_admins(ntype, title, content='', data=None):
    users = db.session.execute(
        db.select(User).where(User.deleted_at.is_(None), User.status == 0)
    ).scalars().all()
    for u in users:
        if u.is_admin:
            push_notification(u.id, ntype, title, content, data)


def notify_card_status(card, action_by_id):
    if not card or not card.author:
        return
    if card.author.id == action_by_id:
        return
    status_map = {
        1: ('card_approved', '卡片审核通过', f'你的卡片「{card.content[:30]}」已通过审核'),
        2: ('card_rejected', '卡片审核拒绝', f'你的卡片「{card.content[:30]}」未通过审核'),
        3: ('card_banned', '卡片已被封禁', f'你的卡片「{card.content[:30]}」已被封禁'),
    }
    info = status_map.get(card.status)
    if info:
        push_notification(card.author.id, info[0], info[1], info[2], {'card_id': card.id})


def notify_comment_status(comment, action_by_id):
    if not comment or not comment.user:
        return
    if comment.user.id == action_by_id:
        return
    status_map = {
        1: ('comment_approved', '评论审核通过', '你的一条评论已通过审核'),
        2: ('comment_rejected', '评论审核拒绝', '你的一条评论未通过审核'),
        3: ('comment_banned', '评论已被封禁', '你的一条评论已被封禁'),
    }
    info = status_map.get(comment.status)
    if info:
        push_notification(comment.user.id, info[0], info[1], info[2], {'comment_id': comment.id})


def notify_new_comment(card, comment_user_id):
    if not card or not card.author:
        return
    if card.author.id == comment_user_id:
        return
    push_notification(
        card.author.id, 'new_comment', '收到新评论',
        f'你的卡片收到了一条新评论',
        {'card_id': card.id}
    )


def get_unread_count(user_id):
    from sqlalchemy import func
    return db.session.execute(
        db.select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == 0
        )
    ).scalar() or 0