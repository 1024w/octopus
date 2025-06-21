import datetime

from app.models import db

class Mention(db.Model):
    """提及模型，存储消息中提及的代币"""
    __tablename__ = 'mentions'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=False)
    confidence = db.Column(db.Float, default=1.0)  # 置信度
    is_valid = db.Column(db.Boolean, default=True)  # 是否有效提及
    is_verified = db.Column(db.Boolean, default=False)  # 是否已人工验证
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)  # 验证备注
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系
    events = db.relationship('Event', backref='mention', lazy='dynamic')
    verifier = db.relationship('User', backref='verified_mentions')
    
    def to_dict(self, with_message=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'message_id': self.message_id,
            'token_id': self.token_id,
            'confidence': self.confidence,
            'is_valid': self.is_valid,
            'is_verified': self.is_verified,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # 添加代币信息
        if self.token:
            result['token'] = {
                'id': self.token.id,
                'name': self.token.name,
                'symbol': self.token.symbol,
                'chain': self.token.chain
            }
        
        # 添加消息内容
        if with_message and self.message:
            result['message'] = {
                'id': self.message.id,
                'platform': self.message.platform,
                'content': self.message.content,
                'author_name': self.message.author_name,
                'timestamp': self.message.timestamp.isoformat() if self.message.timestamp else None,
                'source_name': self.message.source_name
            }
        
        return result
    
    def __repr__(self):
        return f'<Mention {self.id} of token {self.token_id} in message {self.message_id}>' 