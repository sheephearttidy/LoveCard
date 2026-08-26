from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from model.User import User
from model.Card import Card
from model.Comment import Comment
from model.db import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form.get("remember") == "1"

        user = db.session.execute(db.select(User).where(User.username == username)).scalar()

        if user is None or not user.check_password(password):
            return jsonify(success=False, message="用户名或密码错误")

        if user.status != 0:
            return jsonify(success=False, message="账号已被禁用")

        login_user(user, remember=remember)
        return jsonify(success=True, message="登录成功")

    return render_template("public/user/login.html")


@auth.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        existing = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if existing:
            return jsonify(success=False, message="用户名已存在")

        email_existing = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if email_existing:
            return jsonify(success=False, message="邮箱已被注册")

        max_id_result = db.session.execute(db.select(db.func.max(User.id))).scalar()
        new_number = str(1000000000 + (max_id_result or 0))

        new_user = User(number=new_number, username=username, email=email, status=0, roles_id=[2])
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(success=True, message="注册成功，3 秒后跳转到登录页")

    return render_template("public/user/register.html")


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.index'))