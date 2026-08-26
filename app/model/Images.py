"""
图片模型模块

对应数据库表 images，记录条目（卡片、评论等）关联的图片资源。
通过 aid+pid 定位图片所属的条目，支持一条内容关联多张图片。
"""
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Images(db.Model):
    """图片模型，记录条目关联的图片"""
    __tablename__ = 'images'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # 应用 ID，标识图片所属的应用模块
    aid = mapped_column(db.Integer, nullable=False, comment='应用ID')
    # 条目 ID，标识图片所属的具体条目
    pid = mapped_column(db.Integer, nullable=False, comment='条目ID')
    # 上传用户 ID，外键关联 users.id
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False)
    # 图片 URL 地址
    url = mapped_column(db.String(256), nullable=False)

    # 创建时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    # 更新时间
    updated_at = mapped_column(db.DateTime, nullable=True, onupdate=datetime.now)
    # 软删除时间，非空表示该图片已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    # 关系：图片 -> 用户（多对一），反向 User.images
    user = relationship('User', backref='images')