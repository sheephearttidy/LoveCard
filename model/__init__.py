"""
模型包初始化模块

统一导出数据库实例 db 和所有 ORM 模型类，
外部可通过 from model import User, Card 等方式引用。
"""
from model.AuditLog import AuditLog
from model.BanRecord import BanRecord
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.Images import Images
from model.InviteCode import InviteCode
from model.Notification import Notification
from model.System import System
from model.Tags import Tags
from model.TagsMap import TagsMap
from model.User import User
from model.db import db

__all__ = ['db', 'User', 'Card', 'Comment', 'Good', 'Images', 'System', 'Tags', 'TagsMap', 'DeletedUser', 'BanRecord', 'InviteCode', 'Notification', 'AuditLog']