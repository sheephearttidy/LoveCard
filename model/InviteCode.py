from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class InviteCode(db.Model):
    __tablename__ = 'invite_codes'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    code = mapped_column(db.String(32), nullable=False, unique=True)
    created_by = mapped_column(db.Integer, nullable=False)
    max_uses = mapped_column(db.Integer, nullable=False, default=0)
    used_count = mapped_column(db.Integer, nullable=False, default=0)
    expires_at = mapped_column(db.DateTime, nullable=True)
    status = mapped_column(db.Integer, nullable=False, default=0)
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def is_valid(self):
        if self.status != 0:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < datetime.now():
            return False
        return True