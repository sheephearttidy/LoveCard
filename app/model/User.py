from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.orm import mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from model.db import db


class User(db.Model, UserMixin):
    """用户模型，继承 UserMixin 以支持 Flask-Login"""
    __tablename__ = 'user'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 用户属性
    username = mapped_column(db.String(80), unique=True, nullable=False)
    email = mapped_column(db.String(120), unique=True, nullable=True)
    password_hash = mapped_column(db.String(255), nullable=False)

    # 管理字段
    is_admin = mapped_column(db.Boolean, nullable=False, default=False)
    is_active = mapped_column(db.Boolean, nullable=False, default=True)

    # 时间字段
    create_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    end_login_time = mapped_column(db.DateTime, nullable=True)

    def set_password(self, password):
        """将明文密码哈希后存储，不应直接保存明文密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证用户输入的密码是否与存储的哈希匹配"""
        return check_password_hash(self.password_hash, password)