import datetime

from app.models import db

class Token(db.Model):
    """代币模型"""
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    address = db.Column(db.String(256), nullable=False, index=True)
    chain = db.Column(db.String(20), nullable=False)  # eth, bsc, etc.
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(256))
    website = db.Column(db.String(256))
    twitter = db.Column(db.String(256))
    telegram = db.Column(db.String(256))
    is_verified = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    mentions = db.relationship('Mention', backref='token', lazy='dynamic')
    events = db.relationship('Event', backref='token', lazy='dynamic')
    prices = db.relationship('Price', backref='token', lazy='dynamic')
    
    def to_dict(self, with_stats=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'address': self.address,
            'chain': self.chain,
            'description': self.description,
            'logo_url': self.logo_url,
            'website': self.website,
            'twitter': self.twitter,
            'telegram': self.telegram,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 添加统计数据
        if with_stats:
            result.update({
                'mention_count': self.mentions.count(),
                'event_count': self.events.count(),
                'latest_price': self._get_latest_price(),
                'price_change_24h': self._get_price_change('24h'),
                'price_change_7d': self._get_price_change('7d')
            })
        
        return result
    
    def _get_latest_price(self):
        """获取最新价格"""
        latest_price = self.prices.order_by(Price.timestamp.desc()).first()
        if latest_price:
            return {
                'price': latest_price.price,
                'timestamp': latest_price.timestamp.isoformat()
            }
        return None
    
    def _get_price_change(self, period):
        """获取价格变化"""
        latest_price = self.prices.order_by(Price.timestamp.desc()).first()
        if not latest_price:
            return None
        
        if period == '24h':
            delta = datetime.timedelta(hours=24)
        elif period == '7d':
            delta = datetime.timedelta(days=7)
        else:
            return None
        
        previous_time = latest_price.timestamp - delta
        previous_price = self.prices.filter(Price.timestamp <= previous_time).order_by(Price.timestamp.desc()).first()
        
        if not previous_price:
            return None
        
        change = (latest_price.price - previous_price.price) / previous_price.price * 100
        return {
            'percentage': round(change, 2),
            'from': {
                'price': previous_price.price,
                'timestamp': previous_price.timestamp.isoformat()
            },
            'to': {
                'price': latest_price.price,
                'timestamp': latest_price.timestamp.isoformat()
            }
        }
    
    def __repr__(self):
        return f'<Token {self.symbol}>' 