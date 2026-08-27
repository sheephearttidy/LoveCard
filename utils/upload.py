import os
import uuid
import struct
from datetime import datetime

from flask import current_app

_IMAGE_SIGNATURES = {
    b'\xff\xd8\xff': 'jpg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',
}


def _check_magic_bytes(file_stream, claimed_ext):
    header = file_stream.read(32)
    file_stream.seek(0)
    if not header:
        return False
    for sig, ext in _IMAGE_SIGNATURES.items():
        if header.startswith(sig) and claimed_ext in (ext, 'jpeg') if ext == 'jpg' else claimed_ext == ext:
            return True
    if claimed_ext == 'webp' and header.startswith(b'RIFF') and b'WEBP' in header[:16:]:
        return True
    return False


def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())


ALLOWED_SUB_DIRS = {'cards', 'avatars', 'images'}


def save_upload(file, sub_dir='cards'):
    if sub_dir not in ALLOWED_SUB_DIRS:
        raise ValueError(f'不允许的上传目录: {sub_dir}')

    upload_folder = current_app.config['UPLOAD_FOLDER']
    save_dir = os.path.join(upload_folder, sub_dir)
    os.makedirs(save_dir, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[1].lower()
    if not _check_magic_bytes(file.stream, ext):
        raise ValueError('文件内容与扩展名不匹配，可能不是有效的图片文件')

    date_prefix = datetime.now().strftime('%Y%m%d')
    unique_name = f"{date_prefix}_{uuid.uuid4().hex[:8]}.{ext}"

    filepath = os.path.join(save_dir, unique_name)
    file.save(filepath)

    return f"/uploads/{sub_dir}/{unique_name}"