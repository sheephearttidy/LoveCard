"""
数据库基础配置模块

定义 SQLAlchemy 的 DeclarativeBase 基类和命名约定，
所有 ORM 模型均继承自 DataBase，通过 db 实例操作数据库。
"""
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData


class DataBase(DeclarativeBase):
    """ORM 声明式基类，统一约束索引/外键/主键的命名规范"""
    meta = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",          # 普通索引前缀
        "uq": "uq_%(table_name)s_%(column_0_name)s",  # 唯一约束前缀
        "ck": "ck_%(table_name)s_%(column_0_name)s",  # 检查约束前缀
        "fk": "fk_%(table_name)s_%(column_0_name)s",  # 外键约束前缀
        "pk": "pk_%(table_name)s"               # 主键约束前缀
    })


# Flask-SQLAlchemy 实例，使用自定义基类
db = SQLAlchemy(model_class=DataBase)