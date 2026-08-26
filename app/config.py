SECRET_KEY = 'dev-secret-key'
SQLALCHEMY_TRACK_MODIFICATIONS = False

'''仅开发使用'''
ADMIN = 'admin'
ADMIN_PASSWORD = 'admin'

'''ORM'''
DB_DRIVER = 'mysqldb'
DB_USER = 'test'
DB_PASSWORD = 'test'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'test'
SQLALCHEMY_DATABASE_URI = (
    f'mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
