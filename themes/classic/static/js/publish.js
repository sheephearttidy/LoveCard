(function () {
    'use strict';

    var toggle = document.getElementById('anonymousToggle');
    var value = document.getElementById('anonymousValue');
    if (toggle && value) {
        toggle.addEventListener('change', function () {
            value.value = this.checked ? '1' : '0';
        });
    }

    var textarea = document.getElementById('content');
    var charCount = document.getElementById('charCount');
    var previewBtn = document.getElementById('mdPreviewBtn');
    var previewDiv = document.getElementById('mdPreview');
    var isPreview = false;
    var previewTimer = null;

    function updateCharCount() {
        if (!textarea || !charCount) return;
        var len = textarea.value.length;
        charCount.textContent = len;
        if (len > 2000) {
            charCount.classList.add('text-red-500');
        } else {
            charCount.classList.remove('text-red-500');
        }
    }

    if (textarea) {
        textarea.addEventListener('input', updateCharCount);
        updateCharCount();
    }

    function insertText(before, after, placeholder) {
        if (!textarea) return;
        textarea.focus();
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var selected = textarea.value.substring(start, end);
        var text = selected || placeholder || '';
        var replacement = before + text + (after || '');
        textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
        var cursorPos = start + before.length + text.length;
        textarea.setSelectionRange(start + before.length, cursorPos);
        updateCharCount();
    }

    function insertLine(prefix) {
        if (!textarea) return;
        textarea.focus();
        var start = textarea.selectionStart;
        var val = textarea.value;
        var lineStart = val.lastIndexOf('\n', start - 1) + 1;
        var lineEnd = val.indexOf('\n', start);
        if (lineEnd === -1) lineEnd = val.length;
        var line = val.substring(lineStart, lineEnd);
        if (line.indexOf(prefix) === 0) {
            textarea.value = val.substring(0, lineStart) + val.substring(lineStart + prefix.length);
            textarea.setSelectionRange(start - prefix.length, start - prefix.length);
        } else {
            textarea.value = val.substring(0, lineStart) + prefix + val.substring(lineStart);
            textarea.setSelectionRange(start + prefix.length, start + prefix.length);
        }
        updateCharCount();
    }

    var mdActions = {
        bold: function () { insertText('**', '**', '粗体文本'); },
        italic: function () { insertText('*', '*', '斜体文本'); },
        strikethrough: function () { insertText('~~', '~~', '删除文本'); },
        heading: function () { insertLine('# '); },
        quote: function () { insertLine('> '); },
        ul: function () { insertLine('- '); },
        ol: function () { insertLine('1. '); },
        link: function () {
            var sel = textarea ? textarea.value.substring(textarea.selectionStart, textarea.selectionEnd) : '';
            if (sel && sel.match(/^https?:\/\//)) {
                insertText('[链接文字](', ')', sel);
            } else {
                insertText('[', '](https://)', '链接文字');
            }
        },
        image: function () {
            insertText('![图片描述](', ')', 'https://');
        },
        code: function () { insertText('`', '`', '代码'); },
        codeblock: function () { insertText('\n```\n', '\n```\n', '代码内容'); },
        hr: function () { insertText('\n---\n', '', ''); },
    };

    document.querySelectorAll('.md-toolbar [data-md]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var action = this.getAttribute('data-md');
            if (mdActions[action]) mdActions[action]();
        });
    });

    if (textarea) {
        textarea.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                mdActions.bold();
            }
            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                mdActions.italic();
            }
        });
    }

    function fetchPreview() {
        if (!textarea || !previewDiv) return;
        var content = textarea.value;
        if (!content.trim()) {
            previewDiv.innerHTML = '<p style="color:#9ca3af;font-style:italic">暂无内容可预览</p>';
            return;
        }
        fetch('/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content }),
        })
        .then(function (res) {
            if (!res.ok) {
                throw new Error('HTTP ' + res.status);
            }
            return res.json();
        })
        .then(function (data) {
            if (data.error) {
                previewDiv.innerHTML = '<p style="color:#ef4444">' + data.error + '</p>';
            } else if (data.html !== undefined) {
                previewDiv.innerHTML = data.html || '<p style="color:#9ca3af;font-style:italic">暂无内容可预览</p>';
            }
        })
        .catch(function (err) {
            previewDiv.innerHTML = '<p style="color:#ef4444">预览加载失败：' + (err.message || '未知错误') + '</p>';
        });
    }

    if (previewBtn && textarea && previewDiv) {
        previewBtn.addEventListener('click', function () {
            isPreview = !isPreview;
            if (isPreview) {
                textarea.classList.add('hidden');
                previewDiv.classList.remove('hidden');
                previewBtn.classList.add('active');
                fetchPreview();
            } else {
                textarea.classList.remove('hidden');
                previewDiv.classList.add('hidden');
                previewBtn.classList.remove('active');
            }
        });

        textarea.addEventListener('input', function () {
            if (isPreview) {
                clearTimeout(previewTimer);
                previewTimer = setTimeout(fetchPreview, 500);
            }
        });
    }

    var form = document.querySelector('form.publish-form') || document.querySelector('.publish-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            var content = textarea ? textarea.value.trim() : '';
            if (!content) {
                e.preventDefault();
                alert('内容不能为空');
                return;
            }
            if (content.length > 2000) {
                e.preventDefault();
                alert('内容不能超过 2000 个字符');
                return;
            }
        });
    }

    var coverFile = document.getElementById('coverFile');
    var coverUrl = document.getElementById('coverUrl');
    var coverPreview = document.getElementById('coverPreview');
    var coverPreviewImg = document.getElementById('coverPreviewImg');
    var coverRemoveBtn = document.getElementById('coverRemoveBtn');

    function showCoverPreview(src) {
        if (coverPreview && coverPreviewImg) {
            coverPreviewImg.src = src;
            coverPreview.classList.remove('hidden');
        }
    }

    function hideCoverPreview() {
        if (coverPreview && coverPreviewImg) {
            coverPreviewImg.src = '';
            coverPreview.classList.add('hidden');
        }
    }

    if (coverFile) {
        coverFile.addEventListener('change', function () {
            var file = this.files[0];
            if (file && file.type.startsWith('image/')) {
                var reader = new FileReader();
                reader.onload = function (e) { showCoverPreview(e.target.result); };
                reader.readAsDataURL(file);
                if (coverUrl) coverUrl.value = '';
            } else {
                hideCoverPreview();
            }
        });
    }

    if (coverUrl) {
        var urlTimer = null;
        coverUrl.addEventListener('input', function () {
            clearTimeout(urlTimer);
            var url = this.value.trim();
            if (url) {
                urlTimer = setTimeout(function () { showCoverPreview(url); }, 500);
            } else {
                hideCoverPreview();
            }
        });
    }

    if (coverRemoveBtn) {
        coverRemoveBtn.addEventListener('click', function () {
            hideCoverPreview();
            if (coverFile) coverFile.value = '';
            if (coverUrl) coverUrl.value = '';
        });
    }

    var extraImages = document.getElementById('extraImages');
    var imagePreview = document.getElementById('imagePreview');
    if (extraImages && imagePreview) {
        extraImages.addEventListener('change', function () {
            imagePreview.innerHTML = '';
            var files = this.files;
            for (var i = 0; i < files.length; i++) {
                (function (file) {
                    if (!file.type.startsWith('image/')) return;
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        var div = document.createElement('div');
                        div.className = 'relative w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600';
                        var img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'w-full h-full object-cover';
                        div.appendChild(img);
                        imagePreview.appendChild(div);
                    };
                    reader.readAsDataURL(file);
                })(files[i]);
            }
        });
    }
})();