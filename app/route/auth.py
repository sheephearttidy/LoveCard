from flask import Blueprint, request, render_template
from model.db import db
from model.User import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if user is None:
            return "Username or Password is incorrect"
        if user.password != password:
            return "Username or Password is incorrect"
        # 登录成功
        return f"Login Successful  {username}:{password}"

    return render_template("public/user/login.html")


@auth.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        # return f"Register Successful  {username}:{password}:{email}"
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()
    return render_template("public/user/register.html")