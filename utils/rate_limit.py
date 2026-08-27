import time
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock

from sqlalchemy import func, select, delete

_cache = defaultdict(list)
_lock = Lock()


def _cleanup_cache(ip, now, window):
    _cache[ip] = [t for t in _cache[ip] if now - t < window]


def _db_count_attempts(ip, window):
    from model.RateLimitAttempt import RateLimitAttempt
    from model.db import db
    cutoff = datetime.now() - timedelta(seconds=window)
    result = db.session.execute(
        select(func.count()).select_from(RateLimitAttempt).where(
            RateLimitAttempt.ip == ip,
            RateLimitAttempt.created_at >= cutoff
        )
    ).scalar()
    return result or 0


def _db_earliest_attempt(ip, window):
    from model.RateLimitAttempt import RateLimitAttempt
    from model.db import db
    cutoff = datetime.now() - timedelta(seconds=window)
    return db.session.execute(
        select(RateLimitAttempt).where(
            RateLimitAttempt.ip == ip,
            RateLimitAttempt.created_at >= cutoff
        ).order_by(RateLimitAttempt.created_at.asc()).limit(1)
    ).scalar_one_or_none()


def check_rate_limit(ip, max_attempts=5, window=300):
    now = time.time()
    with _lock:
        _cleanup_cache(ip, now, window)
        if len(_cache[ip]) >= max_attempts:
            return False

    try:
        db_count = _db_count_attempts(ip, window)
        if db_count >= max_attempts:
            return False
    except Exception:
        if not _cache[ip]:
            return True

    return True


def record_failed_attempt(ip, action='login'):
    now = time.time()
    with _lock:
        _cache[ip].append(now)

    try:
        from model.RateLimitAttempt import RateLimitAttempt
        from model.db import db
        record = RateLimitAttempt(ip=ip, action=action, created_at=datetime.now())
        db.session.add(record)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def clear_attempts(ip):
    with _lock:
        _cache.pop(ip, None)

    try:
        from model.RateLimitAttempt import RateLimitAttempt
        from model.db import db
        db.session.execute(
            delete(RateLimitAttempt).where(RateLimitAttempt.ip == ip)
        )
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def get_remaining_time(ip, window=300):
    now = time.time()
    with _lock:
        _cleanup_cache(ip, now, window)
        if _cache[ip]:
            return int(window - (now - _cache[ip][0]))

    try:
        earliest = _db_earliest_attempt(ip, window)
        if earliest:
            elapsed = (datetime.now() - earliest.created_at).total_seconds()
            remaining = int(window - elapsed)
            return max(remaining, 0)
    except Exception:
        pass

    return 0


def cleanup_expired_records(window=86400):
    try:
        from model.RateLimitAttempt import RateLimitAttempt
        from model.db import db
        cutoff = datetime.now() - timedelta(seconds=window)
        db.session.execute(
            delete(RateLimitAttempt).where(RateLimitAttempt.created_at < cutoff)
        )
        db.session.commit()
        return True
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        return False


def start_cleanup_scheduler(app, interval=3600, window=86400):
    import threading

    def _run():
        while True:
            time.sleep(interval)
            with app.app_context():
                cleanup_expired_records(window)

    t = threading.Thread(target=_run, daemon=True)
    t.start()