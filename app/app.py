import os
from flask import Flask, render_template, send_from_directory
from flask_login import LoginManager

import config
from model import db
from model.User import User
from model.DeletedUser import DeletedUser
from model.BanRecord import BanRecord
from route import public, auth, admin
from route.api import api

app = Flask(__name__)
app.config.from_object(config)

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = ''
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 回调函数，根据 user_id 加载用户对象"""
    user = db.session.get(User, int(user_id))
    if user and (user.deleted_at is not None or user.status != 0):
        return None
    return user


# 注册蓝图
app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(api)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("public/404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("public/403.html"), 403


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=8000,host='0.0.0.0')