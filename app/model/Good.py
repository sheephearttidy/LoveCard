from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class Good(db.Model):
    """点赞模型，记录用户对条目的点赞"""
    __tablename__ = 'good'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    aid = mapped_column(db.Integer, nullable=False, comment='应用ID')
    pid = mapped_column(db.Integer, nullable=False, comment='条目ID')
    uid = mapped_column(db.Integer, nullable=False)
    ip = mapped_column(db.String(32), nullable=False, comment='发布IP')

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, comment='发布时间')