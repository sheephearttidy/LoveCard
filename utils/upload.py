import os
import uuid
from datetime import datetime

from flask import current_app


def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())


def save_upload(file, sub_dir='cards'):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    save_dir = os.path.join(upload_folder, sub_dir)
    os.makedirs(save_dir, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[1].lower()
    date_prefix = datetime.now().strftime('%Y%m%d')
    unique_name = f"{date_prefix}_{uuid.uuid4().hex[:8]}.{ext}"

    filepath = os.path.join(save_dir, unique_name)
    file.save(filepath)

    return f"/uploads/{sub_dir}/{unique_name}"