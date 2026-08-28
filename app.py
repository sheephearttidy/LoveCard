import hmac
import os
import uuid
from datetime import datetime

from flask import Flask, render_template, send_from_directory, session, Response, request, abort
from flask_compress import Compress
from flask_login import LoginManager, current_user

import config
from model import db
from model.Card import Card
from model.Comment import Comment
from model.DeletedUser import DeletedUser
from model.Good import Good
from model.User import User
from route import public, auth, admin
from route.api import api
from utils.captcha import generate_captcha_text, generate_captcha_svg
from utils.markdown_utils import render_markdown, strip_markdown
from utils.system import get_site_config
from utils.theme import setup_theme_loader, render_themed

app = Flask(__name__)
app.config.from_object(config)

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400

Compress(app)

setup_theme_loader(app)

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
    if user and not user.email_verified and get_config('siteRequireEmailVerify') == 'true':
        return None
    return user


@app.before_request
def _check_user_status():
    if current_user.is_authenticated:
        if current_user.deleted_at is not None or current_user.status != 0:
            from flask_login import logout_user
            logout_user()
            session.clear()
            return
        if not current_user.email_verified and get_config('siteRequireEmailVerify') == 'true':
            from flask_login import logout_user
            logout_user()
            session.clear()
            return


@app.context_processor
def inject_site_config():
    try:
        cfg = get_site_config()
        ctx = {'site_config': cfg}
    except Exception:
        from utils.system import SITE_CONFIG_DEFAULTS
        cfg = dict(SITE_CONFIG_DEFAULTS)
        ctx = {'site_config': cfg}
    ctx['site_theme'] = cfg.get('siteTheme', 'classic')
    if current_user.is_authenticated:
        try:
            from utils.notification import get_unread_count
            ctx['unread_count'] = get_unread_count(current_user.id)
        except Exception:
            ctx['unread_count'] = 0
    else:
        ctx['unread_count'] = 0
    return ctx


# 注册蓝图
app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(api)

# Jinja2 过滤器
app.jinja_env.filters['markdown'] = render_markdown
app.jinja_env.filters['strip_markdown'] = strip_markdown


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_themed("public/404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_themed("public/403.html"), 403


@app.errorhandler(500)
def internal_error(e):
    return render_themed("public/500.html"), 500


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    safe_dir = os.path.normpath(app.config['UPLOAD_FOLDER'])
    filepath = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    try:
        common = os.path.commonpath([safe_dir, filepath])
        if common != safe_dir:
            abort(403)
    except ValueError:
        abort(403)
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
    from utils.rate_limit import cleanup_expired_records, start_cleanup_scheduler
    cleanup_expired_records()
    start_cleanup_scheduler(app)
    app.run(debug=True, port=8000,host='0.0.0.0')