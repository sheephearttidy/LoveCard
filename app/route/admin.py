from flask import Blueprint, request, render_template

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/', methods=['GET', 'POST'])
def admin_index():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    return render_template("admin/admin_index.html")