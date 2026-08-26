from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Card(db.Model):
    """卡片模型，用户发布的卡片内容"""
    __tablename__ = 'cards'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    is_top = mapped_column(db.Integer, nullable=False, default=0)
    status = mapped_column(db.Integer, nullable=False, default=0)
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    data = mapped_column(db.JSON, nullable=True)
    cover = mapped_column(db.String(2083), nullable=True)
    content = mapped_column(db.Text, nullable=True)
    tags = mapped_column(db.JSON, nullable=True)
    good = mapped_column(db.Integer, nullable=False, default=0)
    views = mapped_column(db.Integer, nullable=False, default=0)
    comments = mapped_column(db.Integer, nullable=False, default=0)
    post_ip = mapped_column(db.String(39), nullable=True)

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    author = relationship('User', backref='cards')