import os
import warnings

bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"

if not os.environ.get('SECRET_KEY'):
    warnings.warn(
        "SECRET_KEY is not set! Using default value is insecure in production. "
        "Set SECRET_KEY environment variable: python -c \"import secrets; print(secrets.token_hex(32))\"",
        RuntimeWarning,
        stacklevel=1
    )