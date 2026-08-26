"""
评论模型模块

对应数据库表 comments，存储用户对卡片等内容的评论。
支持嵌套评论（通过 parent_id 实现树形结构）和多应用评论（通过 aid 区分）。
"""
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Comment(db.Model):
    """评论模型，用户对卡片等内容的评论"""
    __tablename__ = 'comments'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 应用 ID，标识评论所属的应用模块
    aid = mapped_column(db.Integer, nullable=False, default=0)
    # 条目 ID，标识评论所属的具体条目（如卡片 ID）
    pid = mapped_column(db.Integer, nullable=False, default=0)
    # 父评论 ID，0 或 NULL 表示顶级评论，非零表示回复某条评论（嵌套评论）
    parent_id = mapped_column(db.Integer, nullable=True, default=0)
    # 是否置顶：0=否，1=是
    is_top = mapped_column(db.Integer, nullable=False, default=0)
    # 审核状态：0=待审核，1=已通过
    status = mapped_column(db.Integer, nullable=False, default=0)
    # 评论者用户 ID，外键关联 users.id
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, default=0)
    # 评论扩展数据，JSON 格式，存储附加信息（如表情、附件等）
    data = mapped_column(db.JSON, nullable=True)
    # 评论正文内容
    content = mapped_column(db.Text, nullable=True)
    # 点赞数，冗余计数
    goods = mapped_column(db.Integer, nullable=False, default=0)
    # 评论者 IP 地址
    post_ip = mapped_column(db.String(39), nullable=True)

    # 创建时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    # 更新时间
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    # 软删除时间，非空表示该评论已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    # 关系：评论 -> 用户（多对一），反向 User.comments
    user = relationship('User', backref='comments')