import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, '.')
from app import app
from model.db import db
from model.BanRecord import BanRecord
from model.User import User
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    print("=== 重建 ban_records 表 ===")
    try:
        db.session.execute(text("DROP TABLE IF EXISTS ban_records"))
        db.session.commit()
        print("已删除旧表")
    except Exception as e:
        print("删除失败: " + str(e))
        db.session.rollback()

    BanRecord.__table__.create(db.engine, checkfirst=True)
    print("ban_records 表已重建")

    print("\n=== 验证字符集 ===")
    result = db.session.execute(text("SHOW CREATE TABLE ban_records")).fetchone()
    create_sql = result[1]
    if 'utf8mb4' in create_sql:
        print("ban_records 字符集: utf8mb4 ✓")
    else:
        print("ban_records 字符集异常!")
        print(create_sql)

    print("\n=== 测试中文插入 ===")
    try:
        record = BanRecord(
            user_id=999,
            username='test_user',
            reason='测试中文：诈骗、骚扰、违规',
            tags=['诈骗', '骚扰'],
            banned_by=1,
            banned_by_name='admin'
        )
        db.session.add(record)
        db.session.commit()
        print("中文插入成功! ID: " + str(record.id))
        db.session.execute(text("DELETE FROM ban_records WHERE id = " + str(record.id)))
        db.session.commit()
        print("测试数据已清理")
    except Exception as e:
        print("中文插入失败: " + str(e))
        db.session.rollback()

    print("\n=== 创建初始 admin 用户 ===")
    existing = db.session.execute(
        db.select(User).where(User.username == 'admin')
    ).scalar_one_or_none()

    if existing:
        print("admin 用户已存在 (ID: " + str(existing.id) + ")，跳过创建")
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
        db.session.commit()
        print("admin 用户创建成功! (用户名: admin, 密码: admin, 角色: 超级管理员)")

    print("\n=== 完成 ===")