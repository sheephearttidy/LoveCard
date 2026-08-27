from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class RateLimitAttempt(db.Model):
    __tablename__ = 'rate_limit_attempts'
    __table_args__ = (
        db.Index('ix_rate_limit_attempts_ip_created', 'ip', 'created_at'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'},
    )

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    ip = mapped_column(db.String(39), nullable=False, index=True)
    action = mapped_column(db.String(50), nullable=False, default='login')
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)