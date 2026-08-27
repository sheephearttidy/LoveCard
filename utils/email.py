import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from model.System import System
from model.db import db


def _get_smtp_config():
    defaults = {
        'smtpHost': '',
        'smtpPort': '465',
        'smtpUser': '',
        'smtpPassword': '',
        'smtpSecure': 'ssl',
        'smtpSender': '',
    }
    result = dict(defaults)
    configs = db.session.execute(
        db.select(System).where(System.name.in_(defaults.keys()))
    ).scalars().all()
    for c in configs:
        result[c.name] = c.value
    return result


def send_email(to, subject, html_body):
    cfg = _get_smtp_config()
    if not cfg['smtpHost'] or not cfg['smtpUser']:
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = cfg['smtpSender'] or cfg['smtpUser']
    msg['To'] = to
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        port = int(cfg['smtpPort'])
        if cfg['smtpSecure'] == 'ssl':
            server = smtplib.SMTP_SSL(cfg['smtpHost'], port, timeout=10)
        else:
            server = smtplib.SMTP(cfg['smtpHost'], port, timeout=10)
            server.starttls()
        server.login(cfg['smtpUser'], cfg['smtpPassword'])
        server.sendmail(msg['From'], to, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


def is_smtp_configured():
    cfg = _get_smtp_config()
    return bool(cfg['smtpHost'] and cfg['smtpUser'])