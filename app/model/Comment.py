from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Comment(db.Model):
    """评论模型，用户对卡片的评论"""
    __tablename__ = 'comment'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 评论内容
    content = mapped_column(db.String(200), nullable=False)

    # 外键
    user_id = mapped_column(db.Integer, ForeignKey('user.id'), nullable=False)
    card_id = mapped_column(db.Integer, ForeignKey('card.id'), nullable=False)

    # 时间字段
    create_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    delete_time = mapped_column(db.DateTime, nullable=True, comment="软删除标记，非空表示已删除")

    # 关系：评论 -> 用户（多对一）
    user = relationship('User', backref='comments')