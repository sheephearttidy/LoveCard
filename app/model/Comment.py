from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

from model.db import db


class Comment(db.Model):
    __tablename__ = 'comment'
    id = mapped_column(db.Integer, primary_key=True)  # 评论ID，主键
    content = mapped_column(db.String(200))  # 评论内容
    '''外键'''
    user_id = mapped_column(db.Integer, ForeignKey('user.id'))  # 评论者ID，外键关联用户表
    card_id = mapped_column(db.Integer, ForeignKey('card.id'))  # 所属卡片ID，外键关联卡片表

    server_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 服务器记录时间
    comment_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 评论发布时间
