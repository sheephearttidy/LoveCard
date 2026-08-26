from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class BanRecord(db.Model):
    __tablename__ = 'ban_records'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, nullable=False)
    username = mapped_column(db.String(255), nullable=False, default='')
    reason = mapped_column(db.String(500), nullable=False, default='')
    tags = mapped_column(db.JSON, nullable=False, default=list)
    banned_by = mapped_column(db.Integer, nullable=False)
    banned_by_name = mapped_column(db.String(255), nullable=False, default='')
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    unbanned_at = mapped_column(db.DateTime, nullable=True)