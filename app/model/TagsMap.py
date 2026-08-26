from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class TagsMap(db.Model):
    """标签映射模型，记录条目与标签的多对多关系"""
    __tablename__ = 'tags_map'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    aid = mapped_column(db.Integer, nullable=False)
    pid = mapped_column(db.Integer, nullable=False)
    tag_id = mapped_column(db.Integer, ForeignKey('tags.id'), nullable=False)

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    tag = relationship('Tags', backref='tag_maps')