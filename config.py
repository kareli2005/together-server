from dotenv import load_dotenv
import redis
import os


load_dotenv()


class ApplicationConfig:

    # dotenv variables
    SECRET_KEY = os.getenv('SECRET_KEY')

    # database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'

    # session
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis.from_url(os.getenv('REDIS_URL'))
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    SESSION_KEY_PREFIX = 'session:'


    # mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587 
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = 'cotneqareli123@gmail.com'
    MAIL_USERNAME = 'cotneqareli123@gmail.com'
    MAIL_PASSWORD = 'eyry rpwu clou owkd'

    # folders
    USERS_FOLDER = os.getenv('USERS_FOLDER')
    STATIC_FOLDER = os.getenv('STATIC_FOLDER')

    # files
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    DEFAULT_PICTURE_URL = 'https://res.cloudinary.com/drwk04rlc/image/upload/v1719829805/xgqujxjidzrlfujyc5wh.webp'

    # urls
    FRONTEND_URL = os.getenv('FRONTEND_URL')
    BACKEND_URL = os.getenv('BACKEND_URL')