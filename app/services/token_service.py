import datetime
from sqlalchemy import desc, func, and_

from app.models import db
from app.models.token import Token
from app.models.mention import Mention
from app.models.price import Price
from app.utils.logging import get_logger

logger = get_logger("service.token")

class TokenService:
    """代币服务，处理代币相关业务逻辑"""
    
    def get_tokens(self, page=1, per_page=20, sort_by='mention_count', order='desc', name=None, symbol=None, chain=None):
        """
        获取代币列表，支持分页和筛选
        
        Args:
            page: 页码，从1开始
            per_page: 每页数量
            sort_by: 排序字段
            order: 排序方式，'asc'或'desc'
            name: 按名称筛选，可选
            symbol: 按符号筛选，可选
            chain: 按链筛选，可选
            
        Returns:
            (tokens, total) 代币列表和总数
        """
        # 基础查询
        query = Token.query
        
        # 应用筛选
        if name:
            query = query.filter(Token.name.ilike(f'%{name}%'))
        if symbol:
            query = query.filter(Token.symbol.ilike(f'%{symbol}%'))
        if chain:
            query = query.filter(Token.chain == chain)
        
        # 应用排序
        if sort_by == 'mention_count':
            # 按提及次数排序需要特殊处理
            subquery = db.session.query(
                Mention.token_id,
                func.count(Mention.id).label('mention_count')
            ).group_by(Mention.token_id).subquery()
            
            query = query.outerjoin(
                subquery,
                Token.id == subquery.c.token_id
            )
            
            if order == 'desc':
                query = query.order_by(desc(subquery.c.mention_count.nullsfirst()))
            else:
                query = query.order_by(subquery.c.mention_count.nullslast())
        else:
            # 其他字段直接排序
            sort_column = getattr(Token, sort_by, Token.id)
            if order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination.total
    
    def get_token_by_id(self, token_id):
        """
        通过ID获取代币
        
        Args:
            token_id: 代币ID
            
        Returns:
            代币对象或None
        """
        return Token.query.get(token_id)
    
    def get_token_by_address(self, address, chain=None):
        """
        通过合约地址获取代币
        
        Args:
            address: 合约地址
            chain: 链，可选
            
        Returns:
            代币对象或None
        """
        query = Token.query.filter(Token.address.ilike(address))
        if chain:
            query = query.filter(Token.chain == chain)
        return query.first()
    
    def create_token(self, name, symbol, address, chain, description=None, logo_url=None, website=None, twitter=None, telegram=None, created_by=None):
        """
        创建新代币
        
        Args:
            name: 代币名称
            symbol: 代币符号
            address: 合约地址
            chain: 链
            description: 描述，可选
            logo_url: Logo URL，可选
            website: 网站，可选
            twitter: Twitter，可选
            telegram: Telegram，可选
            created_by: 创建者ID，可选
            
        Returns:
            新创建的代币对象
            
        Raises:
            ValueError: 如果参数无效或代币已存在
        """
        # 检查代币是否已存在
        existing_token = self.get_token_by_address(address, chain)
        if existing_token:
            logger.warning(f"Failed to create token: token with address {address} on chain {chain} already exists")
            raise ValueError(f"Token with address {address} on chain {chain} already exists")
        
        # 创建新代币
        token = Token(
            name=name,
            symbol=symbol,
            address=address,
            chain=chain,
            description=description,
            logo_url=logo_url,
            website=website,
            twitter=twitter,
            telegram=telegram,
            created_by=created_by
        )
        
        db.session.add(token)
        db.session.commit()
        
        logger.info(f"Created new token: {name} ({symbol}) on {chain}")
        return token
    
    def update_token(self, token_id, name=None, symbol=None, description=None, logo_url=None, website=None, twitter=None, telegram=None):
        """
        更新代币信息
        
        Args:
            token_id: 代币ID
            name: 新名称，可选
            symbol: 新符号，可选
            description: 新描述，可选
            logo_url: 新Logo URL，可选
            website: 新网站，可选
            twitter: 新Twitter，可选
            telegram: 新Telegram，可选
            
        Returns:
            更新后的代币对象
            
        Raises:
            ValueError: 如果代币不存在
        """
        token = self.get_token_by_id(token_id)
        
        if not token:
            logger.warning(f"Failed to update token: token {token_id} not found")
            raise ValueError(f"Token with ID {token_id} not found")
        
        # 更新字段
        if name:
            token.name = name
        if symbol:
            token.symbol = symbol
        if description is not None:
            token.description = description
        if logo_url is not None:
            token.logo_url = logo_url
        if website is not None:
            token.website = website
        if twitter is not None:
            token.twitter = twitter
        if telegram is not None:
            token.telegram = telegram
        
        db.session.commit()
        
        logger.info(f"Updated token: {token_id}")
        return token
    
    def get_trending_tokens(self, period='24h', limit=10):
        """
        获取热门代币
        
        Args:
            period: 时间段，'24h', '7d', '30d'
            limit: 返回数量
            
        Returns:
            代币列表
        """
        # 计算时间范围
        now = datetime.datetime.utcnow()
        if period == '24h':
            start_time = now - datetime.timedelta(hours=24)
        elif period == '7d':
            start_time = now - datetime.timedelta(days=7)
        elif period == '30d':
            start_time = now - datetime.timedelta(days=30)
        else:
            start_time = now - datetime.timedelta(hours=24)  # 默认24小时
        
        # 查询在指定时间段内提及次数最多的代币
        subquery = db.session.query(
            Mention.token_id,
            func.count(Mention.id).label('mention_count')
        ).join(
            Token, Mention.token_id == Token.id
        ).filter(
            Mention.created_at >= start_time
        ).group_by(
            Mention.token_id
        ).subquery()
        
        tokens = db.session.query(
            Token
        ).outerjoin(
            subquery, Token.id == subquery.c.token_id
        ).order_by(
            desc(subquery.c.mention_count.nullsfirst())
        ).limit(limit).all()
        
        return tokens
    
    def get_token_mentions(self, token_id, page=1, per_page=20, start_date=None, end_date=None, platform=None):
        """
        获取代币的提及记录
        
        Args:
            token_id: 代币ID
            page: 页码，从1开始
            per_page: 每页数量
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            platform: 平台，可选
            
        Returns:
            (mentions, total) 提及记录列表和总数
        """
        # 基础查询
        query = Mention.query.filter(Mention.token_id == token_id)
        
        # 应用筛选
        if start_date:
            try:
                start_date = datetime.datetime.fromisoformat(start_date)
                query = query.filter(Mention.created_at >= start_date)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                end_date = datetime.datetime.fromisoformat(end_date)
                query = query.filter(Mention.created_at <= end_date)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        
        if platform:
            query = query.join(Mention.message).filter(Message.platform == platform)
        
        # 按时间倒序排序
        query = query.order_by(desc(Mention.created_at))
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination.total
    
    def get_token_stats(self, token_id, period='7d', interval='day'):
        """
        获取代币的统计数据
        
        Args:
            token_id: 代币ID
            period: 时间段，'24h', '7d', '30d', 'all'
            interval: 时间间隔，'hour', 'day', 'week'
            
        Returns:
            统计数据字典
        """
        # 计算时间范围
        now = datetime.datetime.utcnow()
        if period == '24h':
            start_time = now - datetime.timedelta(hours=24)
            if interval == 'hour':
                group_format = '%Y-%m-%d %H:00:00'
            else:
                group_format = '%Y-%m-%d'
        elif period == '7d':
            start_time = now - datetime.timedelta(days=7)
            if interval == 'hour':
                group_format = '%Y-%m-%d %H:00:00'
            else:
                group_format = '%Y-%m-%d'
        elif period == '30d':
            start_time = now - datetime.timedelta(days=30)
            group_format = '%Y-%m-%d'
        elif period == 'all':
            start_time = datetime.datetime(1970, 1, 1)
            if interval == 'week':
                group_format = '%Y-%U'
            else:
                group_format = '%Y-%m-%d'
        else:
            start_time = now - datetime.timedelta(days=7)
            group_format = '%Y-%m-%d'
        
        # 获取代币
        token = self.get_token_by_id(token_id)
        if not token:
            logger.warning(f"Failed to get stats: token {token_id} not found")
            return {}
        
        # 查询提及数据
        mention_stats = self._get_mention_time_series(token_id, start_time, group_format)
        
        # 查询价格数据
        price_stats = self._get_price_time_series(token_id, start_time, group_format)
        
        # 整合统计数据
        stats = {
            'mentions': mention_stats,
            'prices': price_stats,
            'total_mentions': token.mentions.count(),
            'total_mentions_period': token.mentions.filter(Mention.created_at >= start_time).count(),
            'latest_price': token._get_latest_price(),
            'price_change_24h': token._get_price_change('24h'),
            'price_change_7d': token._get_price_change('7d')
        }
        
        return stats
    
    def _get_mention_time_series(self, token_id, start_time, group_format):
        """获取提及时间序列数据"""
        from app.models.message import Message
        
        # 使用SQL函数按时间分组
        mentions_by_time = db.session.query(
            func.date_format(Message.timestamp, group_format).label('time_group'),
            func.count(Mention.id).label('count')
        ).join(
            Message, Mention.message_id == Message.id
        ).filter(
            Mention.token_id == token_id,
            Message.timestamp >= start_time
        ).group_by(
            'time_group'
        ).order_by(
            'time_group'
        ).all()
        
        # 转换为字典格式
        result = [{'time': item[0], 'count': item[1]} for item in mentions_by_time]
        return result
    
    def _get_price_time_series(self, token_id, start_time, group_format):
        """获取价格时间序列数据"""
        # 使用SQL函数按时间分组，取每组的最后一个价格
        prices_by_time = db.session.query(
            func.date_format(Price.timestamp, group_format).label('time_group'),
            func.avg(Price.price).label('avg_price')
        ).filter(
            Price.token_id == token_id,
            Price.timestamp >= start_time
        ).group_by(
            'time_group'
        ).order_by(
            'time_group'
        ).all()
        
        # 转换为字典格式
        result = [{'time': item[0], 'price': item[1]} for item in prices_by_time]
        return result 