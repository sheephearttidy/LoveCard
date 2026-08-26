from flask_migrate import Migrate
from app import app
from model import db, User, Card, Comment, Good, Images, System, Tags, TagsMap
from werkzeug.security import generate_password_hash

migrate = Migrate(app, db)


def seed_admin():
    with app.app_context():
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


if __name__ == '__main__':
    seed_admin()