import re
import spacy
import datetime
import hashlib
from app.processors.base_processor import BaseProcessor
from app.models import db
from app.models.message import Message
from app.models.token import Token
from app.models.mention import Mention
from app.utils.logging import get_logger

logger = get_logger("processors.message")

class MessageProcessor(BaseProcessor):
    """消息处理器，处理消息中的代币提及"""
    
    def __init__(self):
        """初始化消息处理器"""
        super().__init__()
        
        # 加载NLP模型
        try:
            self.nlp_en = spacy.load("en_core_web_sm")
            self.nlp_zh = spacy.load("zh_core_web_sm")
        except Exception as e:
            logger.error(f"Error loading NLP models: {str(e)}")
            self.nlp_en = None
            self.nlp_zh = None
        
        logger.info("Message processor initialized")
    
    def _get_processor_type(self):
        """获取处理器类型"""
        return 'message'
    
    def detect_language(self, text):
        """
        检测文本语言
        
        Args:
            text: 待检测文本
            
        Returns:
            语言代码，'en'或'zh'或'unknown'
        """
        # 简单语言检测，实际项目可能需要更复杂的方法
        if not text:
            return 'unknown'
        
        # 计算英文字符和中文字符的比例
        en_chars = len(re.findall(r'[a-zA-Z]', text))
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        if en_chars > zh_chars:
            return 'en'
        elif zh_chars > 0:
            return 'zh'
        else:
            return 'en'  # 默认英文
    
    def extract_token_mentions(self, message):
        """
        从消息中提取代币提及
        
        Args:
            message: 消息对象
            
        Returns:
            提及列表，每个提及是(token, confidence)元组
        """
        if not message or not message.content:
            return []
        
        text = message.content
        mentions = []
        
        # 1. 提取所有可能的代币符号（$符号后面的字母数字组合）
        symbol_pattern = r'\$([A-Za-z0-9]{2,10})'
        symbols = re.findall(symbol_pattern, text)
        
        # 2. 查找所有代币
        all_tokens = Token.query.all()
        token_map = {token.symbol.lower(): token for token in all_tokens}
        
        # 3. 匹配符号提及
        for symbol in symbols:
            token = token_map.get(symbol.lower())
            if token:
                mentions.append((token, 0.9))  # 符号匹配，高置信度
        
        # 4. 使用NLP进行实体识别
        language = self.detect_language(text)
        if language == 'en' and self.nlp_en:
            doc = self.nlp_en(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT']:
                    # 查找匹配的代币名称
                    for token in all_tokens:
                        if token.name.lower() == ent.text.lower():
                            # 避免重复
                            if not any(m[0].id == token.id for m in mentions):
                                mentions.append((token, 0.7))  # 名称匹配，中等置信度
        
        elif language == 'zh' and self.nlp_zh:
            doc = self.nlp_zh(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT']:
                    # 查找匹配的代币名称
                    for token in all_tokens:
                        if token.name.lower() == ent.text.lower():
                            # 避免重复
                            if not any(m[0].id == token.id for m in mentions):
                                mentions.append((token, 0.7))  # 名称匹配，中等置信度
        
        # 5. 直接匹配代币名称和地址
        for token in all_tokens:
            # 名称匹配
            if token.name.lower() in text.lower() and not any(m[0].id == token.id for m in mentions):
                mentions.append((token, 0.8))  # 直接名称匹配，较高置信度
            
            # 地址匹配（仅匹配完整地址）
            if token.address.lower() in text.lower() and not any(m[0].id == token.id for m in mentions):
                mentions.append((token, 1.0))  # 地址匹配，最高置信度
        
        return mentions
    
    def save_mentions(self, message, mentions):
        """
        保存代币提及
        
        Args:
            message: 消息对象
            mentions: 提及列表，每个提及是(token, confidence)元组
            
        Returns:
            保存的提及数量
        """
        saved_count = 0
        
        for token, confidence in mentions:
            # 创建提及对象
            mention = Mention(
                message_id=message.id,
                token_id=token.id,
                confidence=confidence,
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(mention)
            saved_count += 1
        
        if saved_count > 0:
            db.session.commit()
            logger.info(f"Saved {saved_count} mentions for message {message.id}")
        
        return saved_count
    
    def process(self, message_id, **kwargs):
        """
        处理单条消息
        
        Args:
            message_id: 消息ID
            **kwargs: 额外参数
            
        Returns:
            处理的提及数量
        """
        message = Message.query.get(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found")
            return 0
        
        # 检查消息是否已处理
        if message.mentions.count() > 0:
            logger.info(f"Message {message_id} already processed, skipping")
            return 0
        
        # 提取代币提及
        mentions = self.extract_token_mentions(message)
        
        # 保存提及
        saved_count = self.save_mentions(message, mentions)
        
        return saved_count
    
    def batch_process(self, message_ids, **kwargs):
        """
        批量处理消息
        
        Args:
            message_ids: 消息ID列表
            **kwargs: 额外参数
            
        Returns:
            (processed_count, mention_count) 处理的消息数和提及数
        """
        processed_count = 0
        mention_count = 0
        
        for message_id in message_ids:
            mentions = self.process(message_id)
            if mentions > 0:
                processed_count += 1
                mention_count += mentions
        
        logger.info(f"Batch processed {processed_count} messages, found {mention_count} mentions")
        return processed_count, mention_count
    
    def process_unprocessed_messages(self, limit=100):
        """
        处理未处理的消息
        
        Args:
            limit: 处理消息的最大数量
            
        Returns:
            (message_count, mention_count) 处理的消息数量和提及数量
        """
        # 查找未处理的消息
        # 子查询：已处理消息的ID
        processed_ids = db.session.query(Mention.message_id).distinct().subquery()
        
        # 查询未处理的消息
        unprocessed_messages = Message.query.filter(
            ~Message.id.in_(processed_ids)
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        message_ids = [message.id for message in unprocessed_messages]
        return self.batch_process(message_ids)
    
    def process_collector_messages(self, collector_id, limit=100):
        """
        处理特定采集器的消息
        
        Args:
            collector_id: 采集器ID
            limit: 处理消息的最大数量
            
        Returns:
            (message_count, mention_count) 处理的消息数量和提及数量
        """
        # 查找采集器的未处理消息
        # 子查询：已处理消息的ID
        processed_ids = db.session.query(Mention.message_id).distinct().subquery()
        
        # 查询采集器的未处理消息
        unprocessed_messages = Message.query.filter(
            Message.collector_id == collector_id,
            ~Message.id.in_(processed_ids)
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        message_ids = [message.id for message in unprocessed_messages]
        return self.batch_process(message_ids) 