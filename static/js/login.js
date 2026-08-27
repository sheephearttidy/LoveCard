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
            if (data.need_verify) {
                var link = document.createElement('a');
                link.href = '/resend_verify';
                link.textContent = ' 重新发送验证邮件';
                link.style.cssText = 'color:#8b5cf6;font-weight:600;text-decoration:underline;margin-left:4px;';
                errorBox.appendChild(link);
            }
        }
    })
    .catch(function () {
        errorBox.textContent = '请求失败，请稍后重试';
        errorBox.style.display = 'block';
    });
});