(function () {
    'use strict';

    var toggle = document.getElementById('anonymousToggle');
    var value = document.getElementById('anonymousValue');

    if (toggle && value) {
        toggle.addEventListener('change', function () {
            value.value = this.checked ? '1' : '0';
        });
    }

    var form = document.querySelector('.publish-form form');
    if (form) {
        var textarea = form.querySelector('textarea[name="content"]');
        var charCount = document.getElementById('charCount');
        if (textarea && charCount) {
            textarea.addEventListener('input', function () {
                var len = this.value.length;
                charCount.textContent = len;
                if (len > 2000) {
                    charCount.classList.add('text-red-500');
                } else {
                    charCount.classList.remove('text-red-500');
                }
            });
        }
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
                reader.onload = function (e) {
                    showCoverPreview(e.target.result);
                };
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
                urlTimer = setTimeout(function () {
                    showCoverPreview(url);
                }, 500);
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