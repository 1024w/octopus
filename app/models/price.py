import datetime

from app.models import db

class Price(db.Model):
    """价格模型，存储代币价格历史"""
    __tablename__ = 'prices'
    
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    volume_24h = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    source = db.Column(db.String(50), default='coingecko')  # coingecko, cmc, etc.
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'token_id': self.token_id,
            'price': self.price,
            'volume_24h': self.volume_24h,
            'market_cap': self.market_cap,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Price {self.id} of token {self.token_id} at {self.timestamp}>' 