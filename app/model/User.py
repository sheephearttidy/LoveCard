from datetime import datetime

from sqlalchemy.orm import mapped_column

from model.db import db


class User(db.Model):
    __tablename__ = 'user'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)  # 用户ID，主键自增
    '''用户属性'''
    username = mapped_column(db.String(80), unique=True, nullable=False)  # 用户名，唯一且不可为空
    email = mapped_column(db.String(120), unique=True, nullable=True)  # 邮箱，唯一可为空
    password = mapped_column(db.String(80), unique=True, nullable=False)  # 密码，唯一且不可为空
    '''管理'''
    is_admin = mapped_column(db.Boolean, nullable=False, default=False)  # 是否为管理员，默认否
    is_active = mapped_column(db.Boolean, nullable=False, default=True)  # 账号是否激活，默认是
    '''时间'''
    create_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 创建时间
    server_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 服务器记录时间
    update_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 更新时间
    delete_time = mapped_column(db.DateTime, nullable=False, default=datetime.now)  # 删除时间（软删除标记）
