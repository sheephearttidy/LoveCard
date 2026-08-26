from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from model.User import User
from model.db import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 已登录用户访问登录页时直接跳转首页
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 根据用户名查找用户
        user = db.session.execute(db.select(User).where(User.username == username)).scalar()

        # 用户不存在或密码错误
        if user is None or not user.check_password(password):
            return jsonify(success=False, message="用户名或密码错误")

        # 账号已被禁用（status != 0 表示禁用）
        if user.status != 0:
            return jsonify(success=False, message="账号已被禁用")

        # 登录成功，建立会话
        login_user(user)
        return jsonify(success=True, message="登录成功")

    return render_template("public/user/login.html")


@auth.route('/register', methods=["POST", "GET"])
def register():
    # 已登录用户访问注册页时直接跳转首页
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        # 检查用户名是否已存在
        existing = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if existing:
            return jsonify(success=False, message="用户名已存在")

        # 检查邮箱是否已被注册
        email_existing = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if email_existing:
            return jsonify(success=False, message="邮箱已被注册")

        # 生成用户编号：查询当前最大 id，新编号 = 1000000000 + max_id
        max_id_result = db.session.execute(db.select(db.func.max(User.id))).scalar()
        new_number = str(1000000000 + (max_id_result or 0))

        # 创建新用户，通过 set_password 方法加密存储密码
        new_user = User(number=new_number, username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(success=True, message="注册成功，3 秒后跳转到登录页")

    return render_template("public/user/register.html")


@auth.route('/logout')
@login_required  # 只有登录用户才能退出
def logout():
    logout_user()
    return redirect(url_for('public.index'))