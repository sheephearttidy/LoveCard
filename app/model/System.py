from sqlalchemy.orm import mapped_column

from model.db import db


class System(db.Model):
    """系统配置模型，存储站点键值对配置"""
    __tablename__ = 'system'

    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name = mapped_column(db.String(255), nullable=True, default='')
    value = mapped_column(db.String(2555), nullable=False, default='')