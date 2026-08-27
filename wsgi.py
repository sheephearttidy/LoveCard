from app import app as application
from utils.rate_limit import cleanup_expired_records, start_cleanup_scheduler

if __name__ == '__main__':
    with application.app_context():
        cleanup_expired_records()
    start_cleanup_scheduler(application)
    application.run(debug=False, host='0.0.0.0', port=5000)