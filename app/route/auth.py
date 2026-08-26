from flask import Blueprint, request, render_template, jsonify

from model.User import User
from model.db import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if user is None:
            return jsonify(success=False, message="用户名或密码错误")
        if user.password != password:
            return jsonify(success=False, message="用户名或密码错误")
        return jsonify(success=True, message="登录成功")

    return render_template("public/user/login.html")


@auth.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        existing = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if existing:
            return jsonify(success=False, message="用户名已存在")
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(success=True, message="注册成功，3 秒后跳转到登录页")
    return render_template("public/user/register.html")