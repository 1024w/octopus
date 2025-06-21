import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from celery import Celery

from app.config import config_by_name
from app.utils.logging import setup_logging

# 初始化Celery
celery = Celery(__name__)

def create_app(config_name=None):
    """创建Flask应用实例"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    # 初始化日志
    setup_logging()
    
    # 创建应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_by_name[config_name])
    
    # 配置跨域资源共享
    CORS(app)
    
    # 注册API蓝图
    from app.api import init_app as init_api
    init_api(app)
    
    # 初始化数据库
    from app.models import init_app as init_db
    init_db(app)
    
    # 初始化Celery
    from app.tasks import init_app as init_celery
    init_celery(app)
    
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        return {
            'status': 'ok',
            'version': app.config.get('VERSION', '1.0.0')
        }
    
    return app

# 在Celery Worker中创建应用上下文
@celery.task
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery 