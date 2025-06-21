import datetime
import json

from app.models import db

class Collector(db.Model):
    """采集器模型，存储数据采集配置"""
    __tablename__ = 'collectors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    collector_type = db.Column(db.String(20), nullable=False)  # twitter, telegram, wechat, qq
    config = db.Column(db.Text, nullable=False)  # JSON格式的配置
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    last_run_at = db.Column(db.DateTime)
    last_run_status = db.Column(db.String(20))  # success, failure, running
    last_run_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    messages = db.relationship('Message', backref='collector', lazy='dynamic')
    
    @property
    def config_dict(self):
        """将配置字符串转换为字典"""
        if not self.config:
            return {}
        try:
            return json.loads(self.config)
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'collector_type': self.collector_type,
            'config': self.config_dict,
            'description': self.description,
            'is_active': self.is_active,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'last_run_message': self.last_run_message,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': self.messages.count()
        }
    
    def __repr__(self):
        return f'<Collector {self.id} {self.name} ({self.collector_type})>'