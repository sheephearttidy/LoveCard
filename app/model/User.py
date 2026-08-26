"""
用户模型模块

对应数据库表 users，存储用户基本信息、认证凭据和角色配置。
继承 Flask-Login 的 UserMixin 以支持用户会话管理。
"""
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.orm import mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from model.db import db


class User(db.Model, UserMixin):
    """用户模型，继承 UserMixin 以支持 Flask-Login"""
    __tablename__ = 'users'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # 用户编号，系统分配的唯一标识（如 1000000000）
    number = mapped_column(db.String(32), nullable=False)
    # 头像 URL
    avatar = mapped_column(db.String(255), nullable=False, default='')
    # 邮箱地址，用于登录和通知
    email = mapped_column(db.String(320), nullable=False)
    # 手机号码
    phone = mapped_column(db.String(20), nullable=False, default='')
    # 用户名，显示名称
    username = mapped_column(db.String(255), nullable=False)
    # 密码哈希值，使用 bcrypt 加密存储
    password = mapped_column(db.String(255), nullable=False)
    # 账号状态：0=正常，其他值=禁用等
    status = mapped_column(db.Integer, nullable=False, default=0)
    # 角色 ID 列表，JSON 格式存储，如 [0, 1, 2] 表示拥有多个角色
    roles_id = mapped_column(db.JSON, nullable=True)

    # 创建时间，记录首次插入时间
    created_at = mapped_column(db.DateTime, nullable=False, default=datetime.now)
    # 更新时间，记录每次修改时间
    updated_at = mapped_column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    # 软删除时间，非空表示该用户已被删除
    deleted_at = mapped_column(db.DateTime, nullable=True)

    @property
    def is_active(self):
        """覆盖 UserMixin 的 is_active，根据 status 判断账号是否可用"""
        return self.status == 0

    def set_password(self, raw_password):
        """将明文密码哈希后存储，不应直接保存明文密码"""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """验证用户输入的密码是否与存储的哈希匹配"""
        return check_password_hash(self.password, raw_password)