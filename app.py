import os
import uuid
from datetime import datetime

from flask import Flask, render_template, send_from_directory, session, Response, request
from flask_login import LoginManager
from flask_compress import Compress

import config
from model import db
from model.User import User
from model.DeletedUser import DeletedUser
from model.Card import Card
from model.Comment import Comment
from model.Good import Good
from route import public, auth, admin
from route.api import api
from utils.system import get_site_config
from utils.captcha import generate_captcha_text, generate_captcha_svg

app = Flask(__name__)
app.config.from_object(config)

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400

Compress(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = ''
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user and (user.deleted_at is not None or user.status != 0):
        return None
    return user


@app.context_processor
def inject_site_config():
    try:
        ctx = {'site_config': get_site_config()}
    except Exception:
        from utils.system import SITE_CONFIG_DEFAULTS
        ctx = {'site_config': dict(SITE_CONFIG_DEFAULTS)}
    if 'csrf_token' not in session:
        session['csrf_token'] = uuid.uuid4().hex
    ctx['csrf_token'] = session['csrf_token']
    return ctx


# 注册蓝图
app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(api)


@app.before_request
def verify_csrf():
    if request.method != 'POST':
        return
    if request.blueprint == 'api':
        return
    if request.is_json:
        return
    token = session.get('csrf_token')
    form_token = request.form.get('csrf_token')
    if not token or not form_token or form_token != token:
        from flask import abort
        abort(403)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("public/404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("public/403.html"), 403


@app.errorhandler(500)
def internal_error(e):
    return render_template("public/500.html"), 500


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/captcha.svg')
def captcha():
    import time
    text = generate_captcha_text()
    session['captcha'] = text
    session['captcha_time'] = int(time.time())
    svg = generate_captcha_svg(text)
    resp = Response(svg, mimetype='image/svg+xml')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def _cleanup_expired_deletions():
    with app.app_context():
        expired = db.session.execute(
            db.select(DeletedUser).where(DeletedUser.delete_scheduled_at <= datetime.now())
        ).scalars().all()
        for archive in expired:
            user = db.session.get(User, archive.original_id)
            now = datetime.now()
            if user:
                for c in db.session.execute(
                    db.select(Card).where(Card.user_id == user.id, Card.deleted_at.is_(None))
                ).scalars().all():
                    c.deleted_at = now
                for c in db.session.execute(
                    db.select(Comment).where(Comment.user_id == user.id, Comment.deleted_at.is_(None))
                ).scalars().all():
                    c.deleted_at = now
                for g in db.session.execute(
                    db.select(Good).where(Good.uid == user.id)
                ).scalars().all():
                    db.session.delete(g)
                user.deleted_at = now
                user.status = 1
            db.session.delete(archive)
        if expired:
            db.session.commit()


if __name__ == '__main__':
    _cleanup_expired_deletions()
    app.run(debug=True, port=8000,host='0.0.0.0')