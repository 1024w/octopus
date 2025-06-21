import os
from datetime import timedelta

class BaseConfig:
    """基础配置类"""
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key')
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://postgres:postgres@db:5432/octopus')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置
    REDIS_URI = os.getenv('REDIS_URI', 'redis://redis:6379/0')
    
    # Elasticsearch配置
    ELASTICSEARCH_URI = os.getenv('ELASTICSEARCH_URI', 'http://elasticsearch:9200')
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    
    # Celery配置
    CELERY_CONFIG = {
        'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
        'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1'),
        'timezone': 'UTC',
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'enable_utc': True,
    }
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # 文件上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # 第三方API配置
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET', '')
    
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID', '')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
    CMC_API_KEY = os.getenv('CMC_API_KEY', '')


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境可以使用SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///octopus_dev.db')


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 测试环境禁用CSRF保护
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境强制使用环境变量中的配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # 生产环境启用HTTPS
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True 