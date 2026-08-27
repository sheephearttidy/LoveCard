from flask import request
from flask_login import current_user

from model.AuditLog import AuditLog
from model.db import db


def log_action(action, target_type='', target_id=0, detail=''):
    entry = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else 0,
        username=current_user.display_name if current_user.is_authenticated else '',
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip=request.remote_addr or '',
    )
    db.session.add(entry)