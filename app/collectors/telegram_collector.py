import asyncio
import datetime
import hashlib
import json
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, PeerChat

from app.collectors.base_collector import BaseCollector
from app.models import db
from app.models.message import Message
from app.utils.logging import get_logger

logger = get_logger("collectors.telegram")

class TelegramCollector(BaseCollector):
    """Telegram数据采集器"""
    
    def __init__(self, api_id=None, api_hash=None, session_name='octopus'):
        """
        初始化Telegram采集器
        
        Args:
            api_id: Telegram API ID，可选
            api_hash: Telegram API Hash，可选
            session_name: 会话名称，默认为'octopus'
        """
        super().__init__()
        
        from flask import current_app
        
        self.api_id = api_id or current_app.config.get('TELEGRAM_API_ID')
        self.api_hash = api_hash or current_app.config.get('TELEGRAM_API_HASH')
        self.session_name = session_name
        
        # 初始化客户端
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        logger.info("Telegram collector initialized")
    
    def _get_collector_type(self):
        """获取采集器类型"""
        return 'telegram'
    
    async def collect_channel_messages(self, channel, limit=100, offset_id=0):
        """
        采集频道消息
        
        Args:
            channel: 频道用户名或ID
            limit: 采集数量
            offset_id: 起始消息ID
            
        Returns:
            采集的消息列表和频道信息
        """
        logger.info(f"Collecting messages from channel: {channel}, limit: {limit}")
        
        try:
            # 连接客户端
            if not self.client.is_connected():
                await self.client.connect()
            
            # 解析频道
            if isinstance(channel, str) and channel.isdigit():
                entity = PeerChannel(int(channel))
            else:
                entity = channel
            
            # 获取频道信息
            channel_entity = await self.client.get_entity(entity)
            
            # 获取消息历史
            messages = []
            result = await self.client(GetHistoryRequest(
                peer=channel_entity,
                limit=limit,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            messages.extend(result.messages)
            
            logger.info(f"Collected {len(messages)} messages from channel {channel}")
            return {
                'messages': messages, 
                'entity': channel_entity, 
                'source_name': getattr(channel_entity, 'username', '') or getattr(channel_entity, 'title', ''),
                'type': 'channel',
                'channel_id': channel
            }
        
        except Exception as e:
            logger.error(f"Error collecting messages from channel {channel}: {str(e)}")
            return {'messages': [], 'entity': None, 'source_name': str(channel), 'type': 'channel', 'channel_id': channel}
    
    async def collect_group_messages(self, group, limit=100, offset_id=0):
        """
        采集群组消息
        
        Args:
            group: 群组用户名或ID
            limit: 采集数量
            offset_id: 起始消息ID
            
        Returns:
            采集的消息列表和群组信息
        """
        logger.info(f"Collecting messages from group: {group}, limit: {limit}")
        
        try:
            # 连接客户端
            if not self.client.is_connected():
                await self.client.connect()
            
            # 解析群组
            if isinstance(group, str) and group.isdigit():
                entity = PeerChat(int(group))
            else:
                entity = group
            
            # 获取群组信息
            group_entity = await self.client.get_entity(entity)
            
            # 获取消息历史
            messages = []
            result = await self.client(GetHistoryRequest(
                peer=group_entity,
                limit=limit,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            messages.extend(result.messages)
            
            logger.info(f"Collected {len(messages)} messages from group {group}")
            return {
                'messages': messages, 
                'entity': group_entity, 
                'source_name': getattr(group_entity, 'username', '') or getattr(group_entity, 'title', ''),
                'type': 'group',
                'group_id': group
            }
        
        except Exception as e:
            logger.error(f"Error collecting messages from group {group}: {str(e)}")
            return {'messages': [], 'entity': None, 'source_name': str(group), 'type': 'group', 'group_id': group}
    
    async def collect_data_async(self, config):
        """
        异步采集数据
        
        Args:
            config: 采集配置
            
        Returns:
            采集的原始数据
        """
        results = []
        
        # 连接客户端
        if not self.client.is_connected():
            await self.client.connect()
        
        if not await self.client.is_user_authorized():
            logger.error(f"Telegram client not authorized, please login first")
            return results
        
        # 处理频道采集
        if 'channels' in config:
            for channel in config['channels']:
                result = await self.collect_channel_messages(
                    channel=channel.get('username') or channel.get('id'),
                    limit=channel.get('limit', 100),
                    offset_id=channel.get('offset_id', 0)
                )
                
                # 更新offset_id
                if result['messages'] and len(result['messages']) > 0:
                    for i, c in enumerate(config['channels']):
                        if (c.get('username') == channel.get('username') or 
                            c.get('id') == channel.get('id')):
                            config['channels'][i]['offset_id'] = result['messages'][0].id
                
                results.append(result)
        
        # 处理群组采集
        if 'groups' in config:
            for group in config['groups']:
                result = await self.collect_group_messages(
                    group=group.get('username') or group.get('id'),
                    limit=group.get('limit', 100),
                    offset_id=group.get('offset_id', 0)
                )
                
                # 更新offset_id
                if result['messages'] and len(result['messages']) > 0:
                    for i, g in enumerate(config['groups']):
                        if (g.get('username') == group.get('username') or 
                            g.get('id') == group.get('id')):
                            config['groups'][i]['offset_id'] = result['messages'][0].id
                
                results.append(result)
        
        return results
    
    def collect_data(self, config):
        """
        采集数据
        
        Args:
            config: 采集配置
            
        Returns:
            采集的原始数据
        """
        # 使用事件循环运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.collect_data_async(config))
        finally:
            loop.close()
    
    def standardize_message(self, raw_data, collector_id=None, source_name=None):
        """
        将原始数据标准化为统一格式
        
        Args:
            raw_data: 原始数据
            collector_id: 采集器ID
            source_name: 来源名称，可选
            
        Returns:
            标准化后的消息对象列表
        """
        messages = []
        
        for data in raw_data:
            tg_messages = data.get('messages', [])
            entity = data.get('entity')
            data_source_name = data.get('source_name') or source_name
            
            if not entity:
                continue
            
            for msg in tg_messages:
                # 跳过空消息
                if not msg.message:
                    continue
                
                # 生成内容哈希，用于去重
                content_hash = hashlib.md5(msg.message.encode()).hexdigest()
                
                # 获取作者信息
                author_id = ''
                author_name = ''
                author_followers = 0
                
                if msg.from_id:
                    try:
                        # 注意：这里不能使用asyncio.run，因为它会创建新的事件循环
                        # 使用一个简单的同步方法获取作者ID
                        author_id = str(msg.from_id.user_id) if hasattr(msg.from_id, 'user_id') else ''
                        # 作者名称可能需要额外查询，这里简化处理
                    except:
                        pass
                
                # 创建消息对象
                message = Message(
                    platform='telegram',
                    source_id=str(msg.id),
                    source_name=data_source_name,
                    content=msg.message,
                    content_hash=content_hash,
                    timestamp=msg.date,
                    author_id=author_id,
                    author_name=author_name,
                    author_followers=author_followers,
                    metadata=json.dumps({
                        'views': getattr(msg, 'views', 0),
                        'forwards': getattr(msg, 'forwards', 0),
                        'replies': getattr(msg, 'replies', 0) if hasattr(msg, 'replies') else 0,
                        'has_media': bool(msg.media),
                        'media_type': str(type(msg.media).__name__) if msg.media else None,
                        'channel_id': entity.id,
                        'channel_title': getattr(entity, 'title', ''),
                        'channel_username': getattr(entity, 'username', ''),
                        'collection_type': data.get('type')
                    }),
                    collector_id=collector_id
                )
                
                messages.append(message)
        
        return messages
    
    def run_collector(self, collector_id):
        """
        重写运行采集器方法，确保异步操作正确执行
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            采集的消息数量
        """
        # 调用父类方法
        return super().run_collector(collector_id) 