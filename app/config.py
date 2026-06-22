import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ITEMS_PER_PAGE = 12
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

    # Upload folder (not used on Vercel / serverless)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'xiaoyuan.db'
        )
    )


class ProductionConfig(Config):
    DEBUG = False
    _url = os.getenv('DATABASE_URL', '')
    if _url:
        if _url.startswith('postgres://'):
            _url = _url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _url
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
