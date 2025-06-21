import datetime
import json
from app.processors.base_processor import BaseProcessor
from app.models import db
from app.models.event import Event
from app.models.token import Token
from app.utils.logging import get_logger

logger = get_logger("processors.event")

class EventProcessor(BaseProcessor):
    """事件处理器，处理与代币相关的事件"""
    
    def __init__(self):
        """初始化事件处理器"""
        super().__init__()
        logger.info("Event processor initialized")
    
    def _get_processor_type(self):
        """获取处理器类型"""
        return 'event'
    
    def process(self, event_data, **kwargs):
        """
        处理单个事件
        
        Args:
            event_data: 事件数据
            **kwargs: 额外参数
            
        Returns:
            处理结果，包含事件ID
        """
        logger.info(f"Processing event: {event_data.get('event_type')}")
        
        # 验证事件数据
        required_fields = ['event_type', 'timestamp', 'data']
        for field in required_fields:
            if field not in event_data:
                logger.error(f"Missing required field: {field}")
                raise ValueError(f"Missing required field: {field}")
        
        # 创建事件
        event = Event(
            event_type=event_data['event_type'],
            timestamp=event_data.get('timestamp') or datetime.datetime.utcnow(),
            data=json.dumps(event_data['data']),
            source=event_data.get('source'),
            token_id=event_data.get('token_id'),
            processed=False
        )
        
        db.session.add(event)
        db.session.commit()
        
        # 根据事件类型进行处理
        if event.event_type == 'price_change':
            self._process_price_change_event(event)
        elif event.event_type == 'listing':
            self._process_listing_event(event)
        elif event.event_type == 'delisting':
            self._process_delisting_event(event)
        elif event.event_type == 'trending':
            self._process_trending_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
        
        # 更新事件状态
        event.processed = True
        event.processed_at = datetime.datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Event processed: {event.id}")
        return {'event_id': event.id}
    
    def batch_process(self, event_data_list, **kwargs):
        """
        批量处理事件
        
        Args:
            event_data_list: 事件数据列表
            **kwargs: 额外参数
            
        Returns:
            处理结果，包含处理的事件数量和事件ID列表
        """
        processed_count = 0
        event_ids = []
        
        for event_data in event_data_list:
            try:
                result = self.process(event_data)
                processed_count += 1
                event_ids.append(result['event_id'])
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
        
        logger.info(f"Batch processed {processed_count} events")
        return {'processed_count': processed_count, 'event_ids': event_ids}
    
    def _process_price_change_event(self, event):
        """
        处理价格变化事件
        
        Args:
            event: 事件对象
        """
        try:
            # 解析事件数据
            data = json.loads(event.data)
            token_id = event.token_id
            
            if not token_id:
                # 尝试通过符号查找代币
                symbol = data.get('symbol')
                if symbol:
                    token = Token.query.filter_by(symbol=symbol).first()
                    if token:
                        token_id = token.id
                        event.token_id = token_id
            
            if token_id:
                # 更新代币价格
                token = Token.query.get(token_id)
                if token:
                    token.price = data.get('price')
                    token.price_change_24h = data.get('price_change_24h')
                    token.price_updated_at = datetime.datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Updated price for token {token.symbol}: {token.price}")
            else:
                logger.warning("Cannot process price change event: token not found")
        
        except Exception as e:
            logger.error(f"Error processing price change event: {str(e)}")
    
    def _process_listing_event(self, event):
        """
        处理上市事件
        
        Args:
            event: 事件对象
        """
        try:
            # 解析事件数据
            data = json.loads(event.data)
            
            # 检查代币是否已存在
            symbol = data.get('symbol')
            if not symbol:
                logger.warning("Cannot process listing event: missing symbol")
                return
            
            token = Token.query.filter_by(symbol=symbol).first()
            
            if token:
                # 更新代币信息
                token.name = data.get('name') or token.name
                token.address = data.get('address') or token.address
                token.chain = data.get('chain') or token.chain
                token.price = data.get('price') or token.price
                token.market_cap = data.get('market_cap') or token.market_cap
                token.is_listed = True
                token.updated_at = datetime.datetime.utcnow()
            else:
                # 创建新代币
                token = Token(
                    symbol=symbol,
                    name=data.get('name', symbol),
                    address=data.get('address', ''),
                    chain=data.get('chain', ''),
                    price=data.get('price'),
                    market_cap=data.get('market_cap'),
                    is_listed=True,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                db.session.add(token)
            
            db.session.commit()
            
            # 更新事件的代币ID
            if not event.token_id:
                event.token_id = token.id
                db.session.commit()
            
            logger.info(f"Processed listing event for token {symbol}")
        
        except Exception as e:
            logger.error(f"Error processing listing event: {str(e)}")
    
    def _process_delisting_event(self, event):
        """
        处理下架事件
        
        Args:
            event: 事件对象
        """
        try:
            # 解析事件数据
            data = json.loads(event.data)
            token_id = event.token_id
            
            if not token_id:
                # 尝试通过符号查找代币
                symbol = data.get('symbol')
                if symbol:
                    token = Token.query.filter_by(symbol=symbol).first()
                    if token:
                        token_id = token.id
                        event.token_id = token_id
            
            if token_id:
                # 更新代币状态
                token = Token.query.get(token_id)
                if token:
                    token.is_listed = False
                    token.updated_at = datetime.datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Marked token {token.symbol} as delisted")
            else:
                logger.warning("Cannot process delisting event: token not found")
        
        except Exception as e:
            logger.error(f"Error processing delisting event: {str(e)}")
    
    def _process_trending_event(self, event):
        """
        处理趋势事件
        
        Args:
            event: 事件对象
        """
        try:
            # 解析事件数据
            data = json.loads(event.data)
            token_id = event.token_id
            
            if not token_id:
                # 尝试通过符号查找代币
                symbol = data.get('symbol')
                if symbol:
                    token = Token.query.filter_by(symbol=symbol).first()
                    if token:
                        token_id = token.id
                        event.token_id = token_id
            
            if token_id:
                # 更新代币趋势信息
                token = Token.query.get(token_id)
                if token:
                    token.is_trending = True
                    token.trending_score = data.get('score', 0)
                    token.trending_rank = data.get('rank')
                    token.trending_since = datetime.datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Marked token {token.symbol} as trending with score {token.trending_score}")
            else:
                logger.warning("Cannot process trending event: token not found")
        
        except Exception as e:
            logger.error(f"Error processing trending event: {str(e)}")
    
    def process_unprocessed_events(self, limit=100):
        """
        处理未处理的事件
        
        Args:
            limit: 处理事件的最大数量
            
        Returns:
            处理的事件数量
        """
        # 查找未处理的事件
        unprocessed_events = Event.query.filter_by(processed=False).order_by(Event.timestamp).limit(limit).all()
        
        processed_count = 0
        
        for event in unprocessed_events:
            try:
                # 解析事件数据
                data = json.loads(event.data)
                
                # 构建事件数据
                event_data = {
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'data': data,
                    'source': event.source,
                    'token_id': event.token_id
                }
                
                # 处理事件
                self.process(event_data)
                processed_count += 1
            
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {str(e)}")
        
        logger.info(f"Processed {processed_count} unprocessed events")
        return processed_count 