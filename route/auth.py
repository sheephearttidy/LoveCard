import re

from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from model.InviteCode import InviteCode
from model.User import User
from model.db import db
from utils.system import get_config

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return jsonify(success=False, message="用户名和密码不能为空")

        remember = request.form.get("remember") == "1"

        user = db.session.execute(db.select(User).where(User.username == username)).scalar()

        if user is None or not user.check_password(password):
            return jsonify(success=False, message="用户名或密码错误")

        if user.status == 2:
            return jsonify(success=False, message="账号正在审核中，请等待管理员通过")

        if user.status != 0:
            return jsonify(success=False, message="账号已被禁用")

        login_user(user, remember=remember)
        return jsonify(success=True, message="登录成功")

    return render_template("public/user/login.html")


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
        new_user = User(number='0', username=username, email=email, status=initial_status, roles_id=[2])
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()
        new_user.number = str(1000000000 + new_user.id)

        if require_invite_code and invite:
            invite.used_count += 1

        db.session.commit()

        if need_review:
            return jsonify(success=True, message="注册成功，账号正在审核中，审核通过后即可登录")
        return jsonify(success=True, message="注册成功，3 秒后跳转到登录页")

    return render_template("public/user/register.html",
                           require_invite_code=require_invite_code,
                           need_review=need_review)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.index'))