(function () {
    'use strict';

    function toggleDark() {
        var d = document.documentElement;
        if (d.classList.contains('dark')) {
            d.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        } else {
            d.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        }
    }

    var darkToggle = document.getElementById('darkToggle');
    var darkToggleMobile = document.getElementById('darkToggleMobile');
    if (darkToggle) darkToggle.addEventListener('click', toggleDark);
    if (darkToggleMobile) darkToggleMobile.addEventListener('click', toggleDark);

    var mobileMenuBtn = document.getElementById('mobileMenuBtn');
    var mobileMenu = document.getElementById('mobileMenu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function () {
            mobileMenu.classList.toggle('open');
            var icon = mobileMenuBtn.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            }
        });
    }

    document.querySelectorAll('.toggle-switch').forEach(function (el) {
        el.addEventListener('click', function () {
            this.classList.toggle('active');
            var input = this.previousElementSibling;
            if (input && input.type === 'checkbox') {
                input.checked = !input.checked;
            }
            var hiddenInput = this.parentElement.querySelector('input[type="hidden"]');
            if (hiddenInput) {
                hiddenInput.value = this.classList.contains('active') ? '1' : '0';
            }
        });
    });

    document.querySelectorAll('.checkbox-custom').forEach(function (el) {
        el.addEventListener('click', function () {
            this.classList.toggle('checked');
            var input = this.previousElementSibling;
            if (input && input.type === 'checkbox') {
                input.checked = !input.checked;
            }
        });
    });

    var flashMsgs = document.querySelectorAll('.flash-msg');
    flashMsgs.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.3s';
            msg.style.opacity = '0';
            setTimeout(function () { msg.remove(); }, 300);
        }, 5000);
    });

    var tagPills = document.querySelectorAll('.tag-pill');
    var tagContainer = tagPills[0]?.parentElement;
    if (tagContainer && tagPills.length > 5) {
        var toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'px-3 py-1.5 rounded-full text-xs text-gray-400 hover:text-gray-600 transition';
        toggleBtn.textContent = '展开更多';
        var expanded = false;
        var hiddenTags = Array.from(tagPills).slice(5);
        hiddenTags.forEach(function (t) { t.style.display = 'none'; });
        tagContainer.appendChild(toggleBtn);
        toggleBtn.addEventListener('click', function () {
            expanded = !expanded;
            hiddenTags.forEach(function (t) { t.style.display = expanded ? '' : 'none'; });
            toggleBtn.textContent = expanded ? '收起' : '展开更多';
        });
    }
})();