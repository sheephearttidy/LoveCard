from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Comment(db.Model):
    """评论模型，用户对卡片等内容的评论"""
    __tablename__ = 'comments'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    aid = mapped_column(db.Integer, nullable=False, default=0)
    pid = mapped_column(db.Integer, nullable=False, default=0)
    parent_id = mapped_column(db.Integer, nullable=True, default=0)
    is_top = mapped_column(db.Integer, nullable=False, default=0)
    status = mapped_column(db.Integer, nullable=False, default=0)
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    data = mapped_column(db.JSON, nullable=True)
    content = mapped_column(db.Text, nullable=True)
    goods = mapped_column(db.Integer, nullable=False, default=0)
    post_ip = mapped_column(db.String(39), nullable=True)

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    user = relationship('User', backref='comments')