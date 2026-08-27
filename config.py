import os
import warnings

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-do-not-use-in-production')
if SECRET_KEY == 'dev-secret-key-do-not-use-in-production':
    warnings.warn('⚠️  正在使用默认 SECRET_KEY，请在生产环境中设置环境变量 SECRET_KEY！', RuntimeWarning)

SQLALCHEMY_TRACK_MODIFICATIONS = False



'''ORM'''
DB_DRIVER = 'mysqldb'
DB_USER = os.environ.get('DB_USER', 'lovecard')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'lovecard')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'lovecard')
SQLALCHEMY_DATABASE_URI = (
    f'mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
)

JSON_AS_ASCII = False

'''session配置'''
PERMANENT_SESSION_LIFETIME = 1800
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
SESSION_COOKIE_SAMESITE = 'Lax'

'''remember cookie配置'''
REMEMBER_COOKIE_DURATION = 2592000
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
REMEMBER_COOKIE_SAMESITE = 'Lax'