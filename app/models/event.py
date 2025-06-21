import datetime
import json

from app.models import db

class Event(db.Model):
    """事件模型，存储代币相关事件"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # kol_mention, listing, airdrop, etc.
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    platform = db.Column(db.String(20), index=True)  # 事件发生平台
    source_url = db.Column(db.String(512))  # 事件来源URL
    source_id = db.Column(db.String(256))  # 事件来源ID
    mention_id = db.Column(db.Integer, db.ForeignKey('mentions.id'))  # 关联的提及ID
    price_impact = db.Column(db.Float)  # 价格影响百分比
    is_significant = db.Column(db.Boolean, default=False)  # 是否重要事件
    metadata = db.Column(db.Text)  # JSON格式的额外元数据
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    @property
    def metadata_dict(self):
        """将元数据字符串转换为字典"""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self, with_related=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'token_id': self.token_id,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'platform': self.platform,
            'source_url': self.source_url,
            'source_id': self.source_id,
            'mention_id': self.mention_id,
            'price_impact': self.price_impact,
            'is_significant': self.is_significant,
            'metadata': self.metadata_dict,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 添加相关数据
        if with_related:
            if self.token:
                result['token'] = {
                    'id': self.token.id,
                    'name': self.token.name,
                    'symbol': self.token.symbol,
                    'chain': self.token.chain
                }
            
            if self.mention:
                result['mention'] = self.mention.to_dict(with_message=True)
        
        return result
    
    def __repr__(self):
        return f'<Event {self.id} {self.event_type} for token {self.token_id}>' 