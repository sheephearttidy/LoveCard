from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.orm import mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from model.db import db


class User(db.Model, UserMixin):
    """用户模型，继承 UserMixin 以支持 Flask-Login"""
    __tablename__ = 'users'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    number = mapped_column(db.String(32), nullable=False)
    avatar = mapped_column(db.String(255), nullable=False, default='')
    email = mapped_column(db.String(320), nullable=False)
    phone = mapped_column(db.String(20), nullable=False, default='')
    username = mapped_column(db.String(255), nullable=False)
    password = mapped_column(db.String(255), nullable=False)
    status = mapped_column(db.Integer, nullable=False, default=0)
    roles_id = mapped_column(db.JSON, nullable=True)

    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at = mapped_column(db.DateTime, nullable=True)

    def set_password(self, raw_password):
        """将明文密码哈希后存储"""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """验证用户输入的密码是否与存储的哈希匹配"""
        return check_password_hash(self.password, raw_password)