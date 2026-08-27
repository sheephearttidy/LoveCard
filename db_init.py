"""
数据库初始化脚本

提供数据库创建、迁移和种子数据初始化功能。
使用方式：
    python db_init.py create     - 创建所有表（开发用，不会删除已有表）
    python db_init.py drop       - 删除所有表（危险！会丢失所有数据）
    python db_init.py recreate   - 删除并重建所有表（危险！会丢失所有数据）
    python db_init.py seed       - 初始化种子数据（管理员账号、默认配置）
    python db_init.py reset      - 完整重置：删表 + 建表 + 种子数据
"""
import sys

from werkzeug.security import generate_password_hash

from app import app
from model import db, User
from model.Card import Card
from model.Comment import Comment
from model.Good import Good
from model.Images import Images
from model.Tags import Tags
from model.TagsMap import TagsMap
from model.System import System
from model.DeletedUser import DeletedUser
from model.BanRecord import BanRecord
from utils.system import ensure_default_configs, SITE_CONFIG_DEFAULTS

ALL_MODELS = [User, Card, Comment, Good, Images, Tags, TagsMap, System, DeletedUser, BanRecord]


def create_tables():
    """创建所有数据库表（如果不存在）"""
    with app.app_context():
        db.create_all()
        print("数据库表创建完成")
        _print_tables()


def drop_tables():
    """删除所有数据库表"""
    with app.app_context():
        db.drop_all()
        print("数据库表已全部删除")


def seed_data():
    """初始化种子数据：管理员账号 + 默认站点配置"""
    with app.app_context():
        _seed_admin()
        _seed_configs()
        db.session.commit()
        print("种子数据初始化完成")


def _seed_admin():
    existing = db.session.execute(
        db.select(User).where(User.username == 'admin')
    ).scalar_one_or_none()

    if existing:
        print(f"  管理员账号已存在 (ID: {existing.id})，跳过")
    else:
        admin_user = User(
            number='1000000000',
            avatar='',
            email='admin@lovecard.com',
            phone='',
            username='admin',
            password=generate_password_hash('admin'),
            status=0,
            roles_id=[0]
        )
        db.session.add(admin_user)
        db.session.flush()
        if admin_user.number == '1000000000':
            admin_user.number = str(1000000000 + admin_user.id)
        print("  管理员账号创建成功 (用户名: admin, 密码: admin, 角色: 超级管理员)")


def _seed_configs():
    ensure_default_configs()
    print(f"  默认站点配置已确保存在 ({len(SITE_CONFIG_DEFAULTS)} 项)")


def _print_tables():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if tables:
        print(f"  当前共 {len(tables)} 张表: {', '.join(sorted(tables))}")
    else:
        print("  (无表)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    commands = {
        'create': lambda: create_tables(),
        'drop': lambda: drop_tables(),
        'recreate': lambda: (drop_tables(), create_tables()),
        'seed': lambda: seed_data(),
        'reset': lambda: (drop_tables(), create_tables(), seed_data()),
    }

    if command not in commands:
        print(f"未知命令: {command}")
        print(__doc__)
        return

    print(f"执行: {command}")
    commands[command]()
    print("完成")


if __name__ == '__main__':
    main()