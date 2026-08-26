"""
标签模型模块

对应数据库表 tags，管理内容分类标签。
每个标签属于一个应用模块（aid）并由用户创建，
通过 tags_map 表与具体条目建立多对多关系。
"""
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Tags(db.Model):
    """标签模型，管理内容标签"""
    __tablename__ = 'tags'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # 应用 ID，标识标签所属的应用模块
    aid = mapped_column(db.Integer, nullable=False)
    # 创建者用户 ID，外键关联 users.id
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    # 标签名称，如 "技术"、"生活" 等
    name = mapped_column(db.String(255), nullable=True, default='')
    # 标签状态：0=启用，1=禁用
    status = mapped_column(db.Integer, nullable=False, default=0)

    # 创建时间
    created_at = mapped_column(db.DateTime, nullable=True, default=datetime.now)
    # 更新时间
    updated_at = mapped_column(db.DateTime, nullable=True, onupdate=datetime.now)
    # 软删除时间，非空表示该标签已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    # 关系：标签 -> 用户（多对一），反向 User.tags
    user = relationship('User', backref='tags')