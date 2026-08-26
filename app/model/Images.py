from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Images(db.Model):
    """图片模型，记录条目关联的图片"""
    __tablename__ = 'images'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    aid = mapped_column(db.Integer, nullable=False, comment='应用ID')
    pid = mapped_column(db.Integer, nullable=False, comment='条目ID')
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False)
    url = mapped_column(db.String(256), nullable=False)

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = mapped_column(db.DateTime, nullable=True, onupdate=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    user = relationship('User', backref='images')