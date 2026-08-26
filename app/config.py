SECRET_KEY = 'dev-secret-key'
SQLALCHEMY_TRACK_MODIFICATIONS = False
'''仅开发使用'''
ADMIN = 'admin'
ADMIN_PASSWORD = 'admin'

'''ORM'''
DB_DRIVER = 'mysqldb'
DB_USER = 'lovecard'
DB_PASSWORD = 'lovecard'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'lovecard'
SQLALCHEMY_DATABASE_URI = (
    f'mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
)

JSON_AS_ASCII = False # 中文乱码解决

'''session配置'''
PERMANENT_SESSION_LIFETIME = 1800 # 30分钟过期