import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # 关系
    tokens = db.relationship('Token', backref='creator', lazy='dynamic')
    events = db.relationship('Event', backref='creator', lazy='dynamic')
    collectors = db.relationship('Collector', backref='creator', lazy='dynamic')
    
    @property
    def password(self):
        """密码属性不可读"""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """设置密码，自动加密"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>' 