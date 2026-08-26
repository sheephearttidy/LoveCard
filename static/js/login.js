document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();

    var errorBox = document.getElementById('errorBox');
    var username = document.getElementById('username').value.trim();
    var password = document.getElementById('password').value;
    var errors = [];

    if (!username) {
        errors.push('用户名不能为空');
    }
    if (!password) {
        errors.push('密码不能为空');
    } else if (password.length < 6) {
        errors.push('密码长度至少为 6 位');
    }

    if (errors.length > 0) {
        errorBox.textContent = errors.join('；');
        errorBox.style.display = 'block';
        return;
    }

    errorBox.style.display = 'none';

    var form = this;
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.success) {
            window.location.href = '/';
        } else {
            errorBox.textContent = data.message;
            errorBox.style.display = 'block';
        }
    })
    .catch(function () {
        errorBox.textContent = '请求失败，请稍后重试';
        errorBox.style.display = 'block';
    });
});