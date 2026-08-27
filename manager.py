"""
LoveCards 管理脚本

提供数据库初始化、迁移、种子数据和密钥生成功能。
使用方式：
    python manager.py create       - 创建所有表（开发用，不会删除已有表）
    python manager.py drop         - 删除所有表（危险！会丢失所有数据）
    python manager.py recreate     - 删除并重建所有表（危险！会丢失所有数据）
    python manager.py seed         - 初始化种子数据（管理员账号、默认配置）
    python manager.py reset        - 完整重置：删表 + 建表 + 种子数据
    python manager.py secret_key   - 生成安全的 SECRET_KEY 并写入 .env 文件
"""
import os
import sys
import secrets

from werkzeug.security import generate_password_hash

from app import app
from model import db, User
from model.AuditLog import AuditLog
from model.BanRecord import BanRecord
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.Images import Images
from model.InviteCode import InviteCode
from model.Notification import Notification
from model.RateLimitAttempt import RateLimitAttempt
from model.System import System
from model.Tags import Tags
from model.TagsMap import TagsMap
from utils.system import ensure_default_configs, SITE_CONFIG_DEFAULTS

ALL_MODELS = [User, Card, Comment, Good, Images, Tags, TagsMap, System, DeletedUser, BanRecord, InviteCode, Notification, AuditLog, RateLimitAttempt]


def create_tables():
    """创建所有数据库表（如果不存在）"""
    with app.app_context():
        db.create_all()
        _migrate_add_columns()
        print("数据库表创建完成")
        _print_tables()


def _migrate_add_columns():
    from sqlalchemy import text, inspect
    insp = inspect(db.engine)
    migrations = [
        ('users', 'nickname', "ALTER TABLE users ADD COLUMN nickname VARCHAR(255) NOT NULL DEFAULT '' AFTER username"),
        ('deleted_users', 'nickname', "ALTER TABLE deleted_users ADD COLUMN nickname VARCHAR(255) NOT NULL DEFAULT '' AFTER username"),
        ('users', 'email_verified', "ALTER TABLE users ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0 AFTER status"),
    ]
    for table, column, sql in migrations:
        if table in insp.get_table_names():
            existing_cols = [c['name'] for c in insp.get_columns(table)]
            if column not in existing_cols:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"  迁移: {table}.{column} 列已添加")
                except Exception as e:
                    db.session.rollback()
                    print(f"  迁移失败: {table}.{column}: {e}")


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
            nickname='admin',
            password=generate_password_hash('admin'),
            status=0,
            roles_id=[0],
            email_verified=True
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


def generate_secret_key():
    """生成安全的 SECRET_KEY 并写入 .env 文件"""
    key = secrets.token_hex(32)
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

    existing_lines = []
    key_updated = False
    if os.path.isfile(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()

    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith('SECRET_KEY='):
            new_lines.append(f'SECRET_KEY={key}\n')
            key_updated = True
        else:
            new_lines.append(line)

    if not key_updated:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append(f'SECRET_KEY={key}\n')

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"  SECRET_KEY 已生成: {key[:8]}...{key[-8:]}")
    if key_updated:
        print(f"  已更新 .env 文件中的 SECRET_KEY")
    else:
        print(f"  已写入 .env 文件: {env_path}")

    if not os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gitignore')):
        print("  ⚠️  建议创建 .gitignore 并添加 .env 以防密钥泄露")
    else:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gitignore'), 'r', encoding='utf-8') as f:
            gitignore = f.read()
        if '.env' not in gitignore:
            print("  ⚠️  .gitignore 中未包含 .env，建议添加以防密钥泄露")


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
        'secret_key': lambda: generate_secret_key(),
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