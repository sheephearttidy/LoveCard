document.getElementById('loginForm').addEventListener('submit', function (e) {
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
        e.preventDefault();
        errorBox.textContent = errors.join('；');
        errorBox.style.display = 'block';
    } else {
        errorBox.style.display = 'none';
    }
});