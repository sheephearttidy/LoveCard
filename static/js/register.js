document.getElementById('registerForm').addEventListener('submit', function (e) {
    e.preventDefault();

    var errorBox = document.getElementById('errorBox');
    var username = document.getElementById('username').value.trim();
    var email = document.getElementById('email').value.trim();
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirmPassword').value;
    var agree = document.getElementById('agree').checked;
    var errors = [];

    if (!username) {
        errors.push('用户名不能为空');
    } else if (username.length < 3 || username.length > 20) {
        errors.push('用户名长度需在 3-20 个字符之间');
    }

    if (!email) {
        errors.push('邮箱不能为空');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.push('邮箱格式不正确');
    }

    if (!password) {
        errors.push('密码不能为空');
    } else if (password.length < 6) {
        errors.push('密码长度至少为 6 位');
    }

    if (password !== confirmPassword) {
        errors.push('两次输入的密码不一致');
    }

    if (!agree) {
        errors.push('请先阅读并同意服务条款和隐私政策');
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
            errorBox.style.display = 'block';
            errorBox.className = 'mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300 text-sm';
            var countdown = 3;
            errorBox.textContent = '注册成功，' + countdown + ' 秒后跳转到登录页';
            var timer = setInterval(function () {
                countdown--;
                if (countdown <= 0) {
                    clearInterval(timer);
                    window.location.href = '/login';
                } else {
                    errorBox.textContent = '注册成功，' + countdown + ' 秒后跳转到登录页';
                }
            }, 1000);
        } else {
            errorBox.className = 'mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 text-sm';
            errorBox.textContent = data.message;
            errorBox.style.display = 'block';
        }
    })
    .catch(function () {
        errorBox.textContent = '请求失败，请稍后重试';
        errorBox.style.display = 'block';
    });
});