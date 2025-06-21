from abc import ABC, abstractmethod
import datetime
import hashlib
import json
from app.models import db
from app.models.message import Message
from app.models.collector import Collector
from app.utils.logging import get_logger

logger = get_logger("collectors.base")

class BaseCollector(ABC):
    """采集器基类，定义采集器通用接口"""
    
    def __init__(self):
        """初始化采集器"""
        self.collector_type = self._get_collector_type()
        logger.info(f"Initialized {self.collector_type} collector")
    
    @abstractmethod
    def _get_collector_type(self):
        """获取采集器类型，由子类实现"""
        pass
    
    @abstractmethod
    def collect_data(self, config):
        """
        采集数据，由子类实现
        
        Args:
            config: 采集配置
            
        Returns:
            采集的原始数据
        """
        pass
    
    def standardize_message(self, raw_data, collector_id=None, source_name=None):
        """
        将原始数据标准化为统一格式
        
        Args:
            raw_data: 原始数据
            collector_id: 采集器ID
            source_name: 来源名称
            
        Returns:
            标准化后的消息对象列表
        """
        # 由子类实现具体的标准化逻辑
        return []
    
    def save_messages(self, messages):
        """
        保存消息到数据库
        
        Args:
            messages: 消息对象列表
            
        Returns:
            保存的消息数量
        """
        saved_count = 0
        
        for message in messages:
            # 检查是否已存在
            existing = Message.query.filter_by(content_hash=message.content_hash).first()
            if existing:
                continue
            
            db.session.add(message)
            saved_count += 1
        
        if saved_count > 0:
            db.session.commit()
            logger.info(f"Saved {saved_count} new messages to database")
        
        return saved_count
    
    def run_collector(self, collector_id):
        """
        运行采集器
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            采集的消息数量
        """
        # 获取采集器配置
        collector = Collector.query.get(collector_id)
        if not collector:
            logger.error(f"Collector {collector_id} not found")
            return 0
        
        if collector.collector_type != self.collector_type:
            logger.error(f"Collector {collector_id} is not a {self.collector_type} collector")
            return 0
        
        # 解析配置
        try:
            config = json.loads(collector.config)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON config for collector {collector_id}")
            return 0
        
        # 更新采集器状态
        collector.last_run_at = datetime.datetime.utcnow()
        collector.last_run_status = 'running'
        db.session.commit()
        
        total_saved = 0
        
        try:
            # 采集数据
            raw_data = self.collect_data(config)
            
            # 标准化数据
            messages = self.standardize_message(raw_data, collector_id)
            
            # 保存数据
            total_saved = self.save_messages(messages)
            
            # 更新采集器配置和状态
            collector.config = json.dumps(config)
            collector.last_run_status = 'success'
            collector.last_run_message = f"Collected {total_saved} new messages"
            
        except Exception as e:
            logger.exception(f"Error running {self.collector_type} collector {collector_id}: {str(e)}")
            collector.last_run_status = 'failure'
            collector.last_run_message = f"Error: {str(e)}"
        
        db.session.commit()
        return total_saved 