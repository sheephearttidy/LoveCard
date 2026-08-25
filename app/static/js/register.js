document.getElementById('registerForm').addEventListener('submit', function (e) {
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
        e.preventDefault();
        errorBox.textContent = errors.join('；');
        errorBox.style.display = 'block';
    } else {
        errorBox.style.display = 'none';
    }
});