from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

from model.db import db


class Card(db.Model):
    __tablename__ = 'card'
    id = mapped_column(db.Integer, primary_key=True)  # 卡片ID，主键
    title = mapped_column(db.String(50), nullable=False)  # 卡片标题，不可为空
    content = mapped_column(db.String(200), nullable=False)  # 卡片内容，不可为空
    author_id = mapped_column(db.Integer, ForeignKey('user.id'))  # 作者ID，外键关联用户表
    '''溯源时间'''
    server_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 服务器记录时间
    create_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 创建时间
    delete_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 删除时间（软删除标记）
    '''点赞数'''
    like_count = mapped_column(db.Integer, nullable=False, default=0)  # 点赞数，默认0
    commnet_count = mapped_column(db.Integer, nullable=False, default=0)  # 评论数，默认0
    coument_id = mapped_column(db.Integer, nullable=False, default=0)  # 评论关联ID，默认0
    '''管理'''
    statue = mapped_column(db.Boolean, nullable=False, default=False)  # 审核状态，默认未通过
    is_top = mapped_column(db.Boolean, nullable=False, default=False)  # 是否置顶，默认否
