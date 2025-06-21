import datetime
import json
import requests
from app.processors.base_processor import BaseProcessor
from app.models import db
from app.models.token import Token
from app.models.event import Event
from app.utils.logging import get_logger

logger = get_logger("processors.price")

class PriceProcessor(BaseProcessor):
    """价格处理器，处理代币价格数据"""
    
    def __init__(self, api_key=None):
        """
        初始化价格处理器
        
        Args:
            api_key: 价格API密钥，可选
        """
        super().__init__()
        
        from flask import current_app
        
        self.api_key = api_key or current_app.config.get('PRICE_API_KEY')
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        
        logger.info("Price processor initialized")
    
    def _get_processor_type(self):
        """获取处理器类型"""
        return 'price'
    
    def process(self, token_id=None, symbol=None, **kwargs):
        """
        处理单个代币的价格
        
        Args:
            token_id: 代币ID，可选
            symbol: 代币符号，可选，当token_id未提供时使用
            **kwargs: 额外参数
            
        Returns:
            处理结果，包含价格信息
        """
        # 获取代币
        token = None
        if token_id:
            token = Token.query.get(token_id)
        elif symbol:
            token = Token.query.filter_by(symbol=symbol).first()
        
        if not token:
            logger.error(f"Token not found: ID={token_id}, symbol={symbol}")
            raise ValueError(f"Token not found: ID={token_id}, symbol={symbol}")
        
        logger.info(f"Processing price for token: {token.symbol}")
        
        # 获取价格数据
        try:
            price_data = self._fetch_price_data(token.symbol)
            
            if not price_data:
                logger.warning(f"No price data found for token: {token.symbol}")
                return {'success': False, 'message': 'No price data found'}
            
            # 更新代币价格
            old_price = token.price
            token.price = price_data.get('price')
            token.price_change_24h = price_data.get('price_change_24h')
            token.market_cap = price_data.get('market_cap')
            token.volume_24h = price_data.get('volume_24h')
            token.price_updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            # 如果价格变化超过阈值，创建价格变化事件
            if old_price and token.price:
                price_change_pct = (token.price - old_price) / old_price * 100
                if abs(price_change_pct) >= 5:  # 5%阈值
                    self._create_price_change_event(token, old_price, token.price, price_change_pct)
            
            logger.info(f"Updated price for token {token.symbol}: {token.price}")
            return {
                'success': True,
                'symbol': token.symbol,
                'price': token.price,
                'price_change_24h': token.price_change_24h,
                'market_cap': token.market_cap,
                'volume_24h': token.volume_24h
            }
        
        except Exception as e:
            logger.error(f"Error processing price for token {token.symbol}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def batch_process(self, token_ids=None, symbols=None, **kwargs):
        """
        批量处理代币价格
        
        Args:
            token_ids: 代币ID列表，可选
            symbols: 代币符号列表，可选，当token_ids未提供时使用
            **kwargs: 额外参数
            
        Returns:
            处理结果，包含处理的代币数量和价格信息
        """
        tokens = []
        
        # 获取代币列表
        if token_ids:
            for token_id in token_ids:
                token = Token.query.get(token_id)
                if token:
                    tokens.append(token)
        elif symbols:
            for symbol in symbols:
                token = Token.query.filter_by(symbol=symbol).first()
                if token:
                    tokens.append(token)
        else:
            # 如果未提供代币列表，处理所有活跃代币
            tokens = Token.query.filter_by(is_active=True).all()
        
        processed_count = 0
        results = []
        
        for token in tokens:
            try:
                result = self.process(token_id=token.id)
                if result.get('success'):
                    processed_count += 1
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing price for token {token.symbol}: {str(e)}")
                results.append({
                    'success': False,
                    'symbol': token.symbol,
                    'message': str(e)
                })
        
        logger.info(f"Batch processed prices for {processed_count} tokens")
        return {'processed_count': processed_count, 'results': results}
    
    def _fetch_price_data(self, symbol):
        """
        从API获取价格数据
        
        Args:
            symbol: 代币符号
            
        Returns:
            价格数据字典
        """
        try:
            # 尝试从CoinGecko获取数据
            url = f"{self.coingecko_api_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': symbol.lower(),
                'order': 'market_cap_desc',
                'per_page': 1,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    coin_data = data[0]
                    return {
                        'price': coin_data.get('current_price'),
                        'price_change_24h': coin_data.get('price_change_percentage_24h'),
                        'market_cap': coin_data.get('market_cap'),
                        'volume_24h': coin_data.get('total_volume'),
                        'last_updated': coin_data.get('last_updated')
                    }
            
            # 如果CoinGecko失败，可以尝试其他API
            # 这里可以添加备用API的实现
            
            logger.warning(f"Failed to fetch price data for {symbol}: API returned status {response.status_code}")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {str(e)}")
            return None
    
    def _create_price_change_event(self, token, old_price, new_price, change_percentage):
        """
        创建价格变化事件
        
        Args:
            token: 代币对象
            old_price: 旧价格
            new_price: 新价格
            change_percentage: 变化百分比
        """
        try:
            event_data = {
                'symbol': token.symbol,
                'name': token.name,
                'old_price': old_price,
                'new_price': new_price,
                'change_percentage': change_percentage,
                'direction': 'up' if new_price > old_price else 'down'
            }
            
            event = Event(
                event_type='price_change',
                timestamp=datetime.datetime.utcnow(),
                data=json.dumps(event_data),
                source='price_processor',
                token_id=token.id,
                processed=False
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"Created price change event for {token.symbol}: {change_percentage:.2f}%")
        
        except Exception as e:
            logger.error(f"Error creating price change event for {token.symbol}: {str(e)}")
    
    def update_all_prices(self):
        """
        更新所有代币的价格
        
        Returns:
            更新的代币数量
        """
        # 获取所有活跃代币
        tokens = Token.query.filter_by(is_active=True).all()
        
        result = self.batch_process(token_ids=[token.id for token in tokens])
        return result['processed_count']
    
    def update_trending_tokens(self):
        """
        更新趋势代币
        
        Returns:
            更新的代币数量
        """
        try:
            # 从CoinGecko获取趋势代币
            url = f"{self.coingecko_api_url}/search/trending"
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch trending tokens: API returned status {response.status_code}")
                return 0
            
            data = response.json()
            coins = data.get('coins', [])
            
            updated_count = 0
            
            for i, coin_data in enumerate(coins):
                coin = coin_data.get('item', {})
                symbol = coin.get('symbol')
                
                if not symbol:
                    continue
                
                # 查找或创建代币
                token = Token.query.filter_by(symbol=symbol).first()
                
                if not token:
                    # 创建新代币
                    token = Token(
                        symbol=symbol,
                        name=coin.get('name', symbol),
                        is_active=True,
                        created_at=datetime.datetime.utcnow(),
                        updated_at=datetime.datetime.utcnow()
                    )
                    db.session.add(token)
                
                # 更新趋势信息
                token.is_trending = True
                token.trending_rank = i + 1
                token.trending_score = coin.get('score', 0)
                token.trending_since = datetime.datetime.utcnow()
                token.updated_at = datetime.datetime.utcnow()
                
                # 创建趋势事件
                event_data = {
                    'symbol': token.symbol,
                    'name': token.name,
                    'rank': token.trending_rank,
                    'score': token.trending_score
                }
                
                event = Event(
                    event_type='trending',
                    timestamp=datetime.datetime.utcnow(),
                    data=json.dumps(event_data),
                    source='price_processor',
                    token_id=token.id,
                    processed=False
                )
                
                db.session.add(event)
                updated_count += 1
            
            # 重置不再趋势的代币
            non_trending_symbols = [t.symbol for t in Token.query.filter_by(is_trending=True).all() 
                                  if t.symbol not in [c.get('item', {}).get('symbol') for c in coins]]
            
            for symbol in non_trending_symbols:
                token = Token.query.filter_by(symbol=symbol).first()
                if token:
                    token.is_trending = False
                    token.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Updated {updated_count} trending tokens")
            return updated_count
        
        except Exception as e:
            logger.error(f"Error updating trending tokens: {str(e)}")
            return 0 