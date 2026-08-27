"""
点赞模型模块

对应数据库表 good，记录用户对条目（卡片、评论等）的点赞行为。
每条记录代表一次点赞，通过 aid+pid+uid 组合可判断用户是否已点赞。
"""
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapped_column

from model.db import db


class Good(db.Model):
    """点赞模型，记录用户对条目的点赞"""
    __tablename__ = 'good'
    __table_args__ = (
        UniqueConstraint('aid', 'pid', 'uid', name='uq_good_aid_pid_uid'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'},
    )

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # 应用 ID，标识点赞所属的应用模块
    aid = mapped_column(db.Integer, nullable=False, comment='应用ID')
    # 条目 ID，标识被点赞的具体条目
    pid = mapped_column(db.Integer, nullable=False, comment='条目ID')
    # 点赞用户 ID
    uid = mapped_column(db.Integer, nullable=False)
    # 点赞者 IP 地址，用于未登录用户的点赞限制
    ip = mapped_column(db.String(32), nullable=False, comment='发布IP')

    # 点赞时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, comment='发布时间')