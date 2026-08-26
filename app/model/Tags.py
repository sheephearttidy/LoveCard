from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Tags(db.Model):
    """标签模型，管理内容标签"""
    __tablename__ = 'tags'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    aid = mapped_column(db.Integer, nullable=False)
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    name = mapped_column(db.String(255), nullable=True, default='')
    status = mapped_column(db.Integer, nullable=False, default=0)

    created_at = mapped_column(db.DateTime, nullable=True, default=datetime.now)
    updated_at = mapped_column(db.DateTime, nullable=True, onupdate=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    user = relationship('User', backref='tags')