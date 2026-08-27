import re

from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from model.InviteCode import InviteCode
from model.User import User
from model.db import db
from utils.email import send_email, is_smtp_configured
from utils.rate_limit import check_rate_limit, get_remaining_time, record_failed_attempt, clear_attempts
from utils.system import get_config, get_site_config
from utils.notification import notify_admins
from utils.theme import render_themed

auth = Blueprint('auth', __name__)


def _get_serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.secret_key, salt='password-reset')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return jsonify(success=False, message="用户名和密码不能为空")

        ip = request.remote_addr or '0.0.0.0'
        if not check_rate_limit(ip, max_attempts=5, window=300):
            remaining = get_remaining_time(ip, window=300)
            return jsonify(success=False, message=f"登录尝试过于频繁，请 {remaining} 秒后再试")

        remember = request.form.get("remember") == "1"

        if '@' in username:
            user = db.session.execute(db.select(User).where(User.email == username)).scalar()
        else:
            user = db.session.execute(db.select(User).where(User.username == username)).scalar()

        if user is None or not user.check_password(password):
            record_failed_attempt(ip)
            return jsonify(success=False, message="用户名或密码错误")

        if user.status == 2:
            return jsonify(success=False, message="账号正在审核中，请等待管理员通过")

        if user.status != 0:
            return jsonify(success=False, message="账号已被禁用")

        clear_attempts(ip)
        login_user(user, remember=remember)
        return jsonify(success=True, message="登录成功")

    return render_themed("public/user/login.html")


@auth.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if get_config('siteAllowRegister') == 'false':
        flash('站点已关闭注册', 'error')
        return redirect(url_for('auth.login'))

    require_invite_code = get_config('siteRequireInviteCode') == 'true'
    need_review = get_config('siteRegisterNeedReview') == 'true'

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        captcha_input = request.form.get("captcha", "").strip()
        invite_code_input = request.form.get("invite_code", "").strip()

        if not username or not password or not email:
            return jsonify(success=False, message="用户名、邮箱和密码不能为空")

        captcha_answer = session.pop('captcha', '')
        captcha_time = session.pop('captcha_time', 0)
        import time
        if not captcha_answer or not captcha_input or captcha_input != captcha_answer:
            return jsonify(success=False, message="验证码错误")
        if captcha_time and (int(time.time()) - captcha_time) > 300:
            return jsonify(success=False, message="验证码已过期，请刷新重试")

        if len(username) < 3 or len(username) > 20:
            return jsonify(success=False, message="用户名长度需在 3-20 个字符之间")

        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', username):
            return jsonify(success=False, message="用户名只能包含字母、数字、下划线和中文")

        if len(password) < 6:
            return jsonify(success=False, message="密码长度至少为 6 位")

        existing = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if existing:
            return jsonify(success=False, message="用户名已存在")

        email_existing = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if email_existing:
            return jsonify(success=False, message="邮箱已被注册")

        if require_invite_code:
            if not invite_code_input:
                return jsonify(success=False, message="邀请码不能为空")
            invite = db.session.execute(
                db.select(InviteCode).where(InviteCode.code == invite_code_input)
            ).scalar()
            if not invite or not invite.is_valid:
                return jsonify(success=False, message="邀请码无效或已过期")

        initial_status = 2 if need_review else 0
        new_user = User(number='0', username=username, nickname=username, email=email, status=initial_status, roles_id=[2])
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()
        new_user.number = str(1000000000 + new_user.id)

        if require_invite_code and invite:
            invite.used_count += 1

        if need_review:
            notify_admins('user_pending', '新用户待审核', f'用户 {username} 注册待审核', {'user_id': new_user.id})
        db.session.commit()

        if need_review:
            return jsonify(success=True, message="注册成功，账号正在审核中，审核通过后即可登录")
        return jsonify(success=True, message="注册成功，3 秒后跳转到登录页")

    return render_themed("public/user/register.html",
                           require_invite_code=require_invite_code,
                           need_review=need_review)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.index'))


@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    smtp_ok = is_smtp_configured()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('请输入邮箱地址', 'error')
            return redirect(url_for('auth.forgot_password'))

        if not smtp_ok:
            flash('邮件服务未配置，请联系管理员重置密码', 'error')
            return redirect(url_for('auth.forgot_password'))

        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar()

        if user and user.status == 0:
            s = _get_serializer()
            token = s.dumps({'user_id': user.id})
            site_config = get_site_config()
            site_url = site_config.get('siteUrl', '').rstrip('/')
            reset_url = f"{site_url}/reset_password/{token}"

            html = f"""
            <div style="max-width:480px;margin:0 auto;font-family:sans-serif;">
                <h2 style="color:#667eea;">密码重置</h2>
                <p>你好，{user.display_name}：</p>
                <p>我们收到了你的密码重置请求。请点击下方按钮重置密码：</p>
                <a href="{reset_url}" style="display:inline-block;padding:10px 24px;background:#667eea;color:#fff;border-radius:8px;text-decoration:none;margin:12px 0;">重置密码</a>
                <p style="color:#999;font-size:13px;">此链接 1 小时内有效。如非本人操作，请忽略此邮件。</p>
                <p style="color:#999;font-size:13px;">如按钮无法点击，请复制链接到浏览器：<br>{reset_url}</p>
            </div>
            """
            send_email(email, f'{site_config.get("siteName", "LoveCards")} - 密码重置', html)

        flash('如果该邮箱已注册，重置链接已发送至你的邮箱', 'success')
        return redirect(url_for('auth.forgot_password'))

    return render_themed("public/user/forgot_password.html", smtp_ok=smtp_ok)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    s = _get_serializer()
    try:
        data = s.loads(token, max_age=3600)
    except SignatureExpired:
        flash('重置链接已过期，请重新申请', 'error')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('重置链接无效', 'error')
        return redirect(url_for('auth.forgot_password'))

    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user or user.status != 0:
        flash('用户不存在或已被禁用', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            flash('请填写完整信息', 'error')
            return redirect(request.url)

        if len(new_password) < 6:
            flash('密码长度至少 6 位', 'error')
            return redirect(request.url)

        if new_password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(request.url)

        user.set_password(new_password)
        db.session.commit()
        flash('密码重置成功，请使用新密码登录', 'success')
        return redirect(url_for('auth.login'))

    return render_themed("public/user/reset_password.html", token=token)