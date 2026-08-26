"""
标签映射模型模块

对应数据库表 tags_map，记录条目（卡片、评论等）与标签的多对多关系。
通过 aid+pid 定位条目，tag_id 关联到 tags 表，
实现一条内容可以拥有多个标签，一个标签也可以关联多条内容。
"""
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class TagsMap(db.Model):
    """标签映射模型，记录条目与标签的多对多关系"""
    __tablename__ = 'tags_map'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # 应用 ID，标识映射所属的应用模块
    aid = mapped_column(db.Integer, nullable=False)
    # 条目 ID，标识被打标签的具体条目
    pid = mapped_column(db.Integer, nullable=False)
    # 标签 ID，外键关联 tags.id
    tag_id = mapped_column(db.Integer, ForeignKey('tags.id'), nullable=False)

    # 创建时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    # 软删除时间，非空表示该映射已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    # 关系：映射 -> 标签（多对一），反向 Tags.tag_maps
    tag = relationship('Tags', backref='tag_maps')