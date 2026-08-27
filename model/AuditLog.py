from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, nullable=False, default=0)
    username = mapped_column(db.String(255), nullable=False, default='')
    action = mapped_column(db.String(100), nullable=False, default='')
    target_type = mapped_column(db.String(50), nullable=False, default='')
    target_id = mapped_column(db.Integer, nullable=False, default=0)
    detail = mapped_column(db.String(500), nullable=False, default='')
    ip = mapped_column(db.String(39), nullable=False, default='')
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)