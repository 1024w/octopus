from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化SQLAlchemy
db = SQLAlchemy()

# 导入所有模型
from app.models.user import User
from app.models.token import Token
from app.models.message import Message
from app.models.mention import Mention
from app.models.event import Event
from app.models.collector import Collector
from app.models.price import Price

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    
    # 初始化数据库迁移
    Migrate(app, db)
    
    # 在应用上下文中创建所有表
    with app.app_context():
        db.create_all() 