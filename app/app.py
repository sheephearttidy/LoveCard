from flask import Flask
from flask_login import LoginManager

import config
from model import db
from model.User import User
from route import public, auth, admin

app = Flask(__name__)
app.config.from_object(config)

# 初始化数据库
db.init_app(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # 未登录时重定向到登录页


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 回调函数，根据 user_id 加载用户对象"""
    return db.session.get(User, int(user_id))


# 注册蓝图
app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(admin)

if __name__ == '__main__':
    app.run(debug=True, port=8000)