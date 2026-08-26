from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Card(db.Model):
    """卡片模型，用户发布的卡片内容"""
    __tablename__ = 'card'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 卡片内容
    title = mapped_column(db.String(50), nullable=False)
    content = mapped_column(db.String(200), nullable=False)
    author_id = mapped_column(db.Integer, ForeignKey('user.id'), nullable=False)

    # 统计数据
    like_count = mapped_column(db.Integer, nullable=False, default=0)
    comment_count = mapped_column(db.Integer, nullable=False, default=0)

    # 管理字段
    status = mapped_column(db.Boolean, nullable=False, default=False, comment="审核状态，False=未通过，True=已通过")
    is_top = mapped_column(db.Boolean, nullable=False, default=False, comment="是否置顶")

    # 时间字段
    create_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    update_time = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    delete_time = mapped_column(db.DateTime, nullable=True, comment="软删除标记，非空表示已删除")

    # 关系：卡片 -> 作者（多对一）
    author = relationship('User', backref='cards')
    # 关系：卡片 -> 评论（一对多）
    comments = relationship('Comment', backref='card', order_by='Comment.create_time.desc()')