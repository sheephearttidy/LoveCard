"""
系统配置模型模块

对应数据库表 system，以键值对形式存储站点全局配置。
如站点名称、URL、ICP 备案号、SMTP 配置等均在此表中。
通过 name 查询对应的 value 即可获取配置项。
"""
from sqlalchemy.orm import mapped_column

from model.db import db


class System(db.Model):
    """系统配置模型，存储站点键值对配置"""
    __tablename__ = 'system'

    # 主键，自增
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # 配置项名称，如 siteUrl、siteName、smtpSecure 等
    name = mapped_column(db.String(255), nullable=True, default='')
    # 配置项值，支持较长的配置内容（如页脚 HTML）
    value = mapped_column(db.String(2555), nullable=False, default='')