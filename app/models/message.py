import datetime
import json

from app.models import db

class Message(db.Model):
    """消息模型，存储原始采集数据"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False, index=True)  # twitter, telegram, wechat, qq
    source_id = db.Column(db.String(256), index=True)  # 源平台ID
    source_name = db.Column(db.String(100), index=True)  # 源用户名/群组名
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), unique=True, index=True)  # 内容哈希，防重复
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    author_id = db.Column(db.String(100), index=True)  # 作者ID
    author_name = db.Column(db.String(100), index=True)  # 作者名
    author_followers = db.Column(db.Integer)  # 作者粉丝数
    metadata = db.Column(db.Text)  # JSON格式的额外元数据
    collector_id = db.Column(db.Integer, db.ForeignKey('collectors.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系
    mentions = db.relationship('Mention', backref='message', lazy='dynamic')
    
    @property
    def metadata_dict(self):
        """将元数据字符串转换为字典"""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'author_followers': self.author_followers,
            'metadata': self.metadata_dict,
            'collector_id': self.collector_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'mention_count': self.mentions.count()
        }
    
    def __repr__(self):
        return f'<Message {self.id} from {self.platform}>' 