"""
卡片模型模块

对应数据库表 cards，存储用户发布的卡片/内容主体。
卡片是系统的核心内容单元，包含富文本、标签、封面图及统计数据。
"""
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Card(db.Model):
    """卡片模型，用户发布的卡片内容"""
    __tablename__ = 'cards'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 是否置顶：0=否，1=是
    is_top = mapped_column(db.Integer, nullable=False, default=0)
    # 审核状态：0=待审核，1=已通过，其他值=拒绝等
    status = mapped_column(db.Integer, nullable=False, default=0)
    # 发布用户 ID，外键关联 users.id
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    # 卡片扩展数据，JSON 格式，存储卡片类型特有的配置信息
    data = mapped_column(db.JSON, nullable=True)
    # 封面图 URL，最大长度 2083 符合 URL 规范上限
    cover = mapped_column(db.String(2083), nullable=True)
    # 卡片正文内容
    content = mapped_column(db.Text, nullable=True)
    # 标签 ID 列表，JSON 格式冗余存储，便于快速查询
    tags = mapped_column(db.JSON, nullable=True)
    # 点赞数，冗余计数，与 good 表数据对应
    good = mapped_column(db.Integer, nullable=False, default=0)
    # 浏览数，每次访问 +1
    views = mapped_column(db.Integer, nullable=False, default=0)
    # 评论数，冗余计数，与 comments 表数据对应
    comments = mapped_column(db.Integer, nullable=False, default=0)
    # 发布者 IP 地址，支持 IPv4（15位）和 IPv6（39位）
    post_ip = mapped_column(db.String(39), nullable=True)

    # 创建时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    # 更新时间
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    # 软删除时间，非空表示该卡片已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    # 关系：卡片 -> 作者（多对一），反向 User.cards
    author = relationship('User', backref='cards')