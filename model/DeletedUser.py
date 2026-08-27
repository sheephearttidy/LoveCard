"""
已删除用户归档模型

用于存储用户注销账号后的备份数据，配合3天冷静期机制。
冷静期过后可由超级管理员手动清理或系统自动清理。
"""
from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class DeletedUser(db.Model):
    __tablename__ = 'deleted_users'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    original_id = mapped_column(db.Integer, nullable=False)
    number = mapped_column(db.String(32), nullable=False, default='')
    avatar = mapped_column(db.String(255), nullable=False, default='')
    email = mapped_column(db.String(320), nullable=False, default='')
    phone = mapped_column(db.String(20), nullable=False, default='')
    username = mapped_column(db.String(255), nullable=False, default='')
    nickname = mapped_column(db.String(255), nullable=False, default='')
    roles_id = mapped_column(db.JSON, nullable=False, default=list)

    cards_count = mapped_column(db.Integer, nullable=False, default=0)
    comments_count = mapped_column(db.Integer, nullable=False, default=0)
    goods_count = mapped_column(db.Integer, nullable=False, default=0)

    delete_scheduled_at = mapped_column(db.DateTime, nullable=False)
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def is_cooling_off(self):
        return datetime.now() < self.delete_scheduled_at

    @property
    def remaining_hours(self):
        delta = self.delete_scheduled_at - datetime.now()
        if delta.total_seconds() <= 0:
            return 0
        return int(delta.total_seconds() / 3600)

    @property
    def display_name(self):
        return self.nickname if self.nickname else self.username