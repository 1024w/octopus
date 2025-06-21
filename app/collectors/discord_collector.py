import discord
import asyncio
import datetime
import hashlib
import json
from app.collectors.base_collector import BaseCollector
from app.models import db
from app.models.message import Message
from app.utils.logging import get_logger

logger = get_logger("collectors.discord")

class DiscordCollector(BaseCollector):
    """Discord数据采集器"""
    
    def __init__(self, token=None):
        """
        初始化Discord采集器
        
        Args:
            token: Discord机器人令牌，可选
        """
        super().__init__()
        
        from flask import current_app
        
        self.token = token or current_app.config.get('DISCORD_BOT_TOKEN')
        
        # 初始化客户端
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        logger.info("Discord collector initialized")
    
    def _get_collector_type(self):
        """获取采集器类型"""
        return 'discord'
    
    async def collect_channel_messages(self, channel_id, limit=100):
        """
        采集频道消息
        
        Args:
            channel_id: 频道ID
            limit: 采集数量限制
            
        Returns:
            采集的消息列表和频道信息
        """
        logger.info(f"Collecting messages from channel: {channel_id}, limit: {limit}")
        
        try:
            # 连接客户端
            if not self.client.is_ready():
                await self.client.login(self.token)
                
            # 获取频道
            channel = await self.client.fetch_channel(channel_id)
            
            # 获取消息
            messages = []
            async for message in channel.history(limit=limit):
                messages.append(message)
            
            logger.info(f"Collected {len(messages)} messages from channel {channel_id}")
            return {
                'messages': messages, 
                'channel': channel, 
                'source_name': f"channel:{channel.name}", 
                'type': 'channel',
                'guild_name': channel.guild.name if hasattr(channel, 'guild') else 'DM'
            }
        
        except Exception as e:
            logger.error(f"Error collecting messages from channel {channel_id}: {str(e)}")
            return {
                'messages': [], 
                'channel': None, 
                'source_name': f"channel:{channel_id}", 
                'type': 'channel'
            }
    
    async def collect_guild_messages(self, guild_id, limit=100):
        """
        采集服务器消息
        
        Args:
            guild_id: 服务器ID
            limit: 每个频道的采集数量限制
            
        Returns:
            采集的消息列表和服务器信息
        """
        logger.info(f"Collecting messages from guild: {guild_id}")
        
        try:
            # 连接客户端
            if not self.client.is_ready():
                await self.client.login(self.token)
                
            # 获取服务器
            guild = await self.client.fetch_guild(guild_id)
            
            # 获取所有文本频道
            channels = []
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    channels.append(channel)
            
            # 采集每个频道的消息
            all_messages = []
            for channel in channels:
                result = await self.collect_channel_messages(channel.id, limit)
                all_messages.extend(result.get('messages', []))
            
            logger.info(f"Collected {len(all_messages)} messages from guild {guild_id}")
            return {
                'messages': all_messages, 
                'guild': guild, 
                'source_name': f"guild:{guild.name}", 
                'type': 'guild'
            }
        
        except Exception as e:
            logger.error(f"Error collecting messages from guild {guild_id}: {str(e)}")
            return {
                'messages': [], 
                'guild': None, 
                'source_name': f"guild:{guild_id}", 
                'type': 'guild'
            }
    
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
        if not self.client.is_ready():
            await self.client.login(self.token)
        
        # 处理频道采集
        if 'channels' in config:
            for channel in config['channels']:
                result = await self.collect_channel_messages(
                    channel_id=channel.get('id'),
                    limit=channel.get('limit', 100)
                )
                results.append(result)
        
        # 处理服务器采集
        if 'guilds' in config:
            for guild in config['guilds']:
                result = await self.collect_guild_messages(
                    guild_id=guild.get('id'),
                    limit=guild.get('limit', 100)
                )
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
            discord_messages = data.get('messages', [])
            data_source_name = data.get('source_name') or source_name
            
            for msg in discord_messages:
                # 跳过空消息
                if not msg.content:
                    continue
                
                # 生成内容哈希，用于去重
                content_hash = hashlib.md5(msg.content.encode()).hexdigest()
                
                # 创建消息对象
                message = Message(
                    platform='discord',
                    source_id=str(msg.id),
                    source_name=data_source_name,
                    content=msg.content,
                    content_hash=content_hash,
                    timestamp=msg.created_at,
                    author_id=str(msg.author.id),
                    author_name=msg.author.name,
                    author_followers=0,  # Discord不直接提供关注者数量
                    metadata=json.dumps({
                        'channel_id': str(msg.channel.id),
                        'channel_name': msg.channel.name,
                        'guild_id': str(msg.guild.id) if hasattr(msg, 'guild') and msg.guild else None,
                        'guild_name': msg.guild.name if hasattr(msg, 'guild') and msg.guild else None,
                        'attachments': [a.url for a in msg.attachments],
                        'embeds': [e.to_dict() for e in msg.embeds],
                        'reactions': [{
                            'emoji': str(r.emoji),
                            'count': r.count
                        } for r in msg.reactions],
                        'collection_type': data.get('type')
                    }),
                    collector_id=collector_id
                )
                
                messages.append(message)
        
        return messages 