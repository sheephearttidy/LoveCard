from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship

from model.db import db


class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, ForeignKey('users.id'), nullable=False, index=True)
    type = mapped_column(db.String(50), nullable=False, default='system')
    title = mapped_column(db.String(255), nullable=False, default='')
    content = mapped_column(db.String(1000), nullable=False, default='')
    data = mapped_column(db.JSON, nullable=True)
    is_read = mapped_column(db.Integer, nullable=False, default=0)
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)

    user = relationship('User', backref='notifications')