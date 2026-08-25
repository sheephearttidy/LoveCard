var form = document.getElementById('adminLoginForm');
var errorBox = document.getElementById('errorBox');
var submitBtn = document.getElementById('submitBtn');
var successPanel = document.getElementById('successPanel');
var passwordInput = document.getElementById('password');

form.addEventListener('submit', function (e) {
    e.preventDefault();

    var username = document.getElementById('username').value.trim();
    var password = passwordInput.value;
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
    submitBtn.disabled = true;
    submitBtn.textContent = '登录中…';

    setTimeout(function () {
        form.style.display = 'none';
        document.getElementById('welcomeName').textContent = username;
        successPanel.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = '登 录';
    }, 900);
});

document.getElementById('togglePwd').addEventListener('click', function () {
    var isHidden = passwordInput.type === 'password';
    passwordInput.type = isHidden ? 'text' : 'password';
    this.setAttribute('aria-label', isHidden ? '隐藏密码' : '显示密码');
    this.style.color = isHidden ? '#3b82f6' : '';
});

function updateCapslockHint(e) {
    var hint = document.getElementById('capslockHint');
    var capsOn = e.getModifierState && e.getModifierState('CapsLock');
    hint.classList.toggle('show', !!capsOn);
}
passwordInput.addEventListener('keydown', updateCapslockHint);
passwordInput.addEventListener('keyup', updateCapslockHint);

document.getElementById('backBtn').addEventListener('click', function () {
    successPanel.style.display = 'none';
    form.style.display = 'block';
    form.reset();
    document.getElementById('username').focus();
});