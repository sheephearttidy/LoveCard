import time
from collections import defaultdict
from threading import Lock

_attempts = defaultdict(list)
_lock = Lock()


def _cleanup(ip, now, window):
    _attempts[ip] = [t for t in _attempts[ip] if now - t < window]


def check_rate_limit(ip, max_attempts=5, window=300):
    now = time.time()
    with _lock:
        _cleanup(ip, now, window)
        if len(_attempts[ip]) >= max_attempts:
            return False
    return True


def record_failed_attempt(ip):
    now = time.time()
    with _lock:
        _attempts[ip].append(now)


def clear_attempts(ip):
    with _lock:
        _attempts.pop(ip, None)


def get_remaining_time(ip, window=300):
    now = time.time()
    with _lock:
        _cleanup(ip, now, window)
        if not _attempts[ip]:
            return 0
        return int(window - (now - _attempts[ip][0]))