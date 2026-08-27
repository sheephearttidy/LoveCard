import os

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
    raise RuntimeError(
        "SECRET_KEY environment variable is required in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )