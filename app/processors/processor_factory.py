from app.processors.message_processor import MessageProcessor
from app.processors.event_processor import EventProcessor
from app.processors.price_processor import PriceProcessor
from app.utils.logging import get_logger

logger = get_logger("processors.factory")

class ProcessorFactory:
    """处理器工厂，负责创建不同类型的处理器"""
    
    @staticmethod
    def create_processor(processor_type, **kwargs):
        """
        创建处理器实例
        
        Args:
            processor_type: 处理器类型，支持 'message', 'event', 'price'
            **kwargs: 传递给处理器构造函数的参数
            
        Returns:
            处理器实例
            
        Raises:
            ValueError: 如果处理器类型不支持
        """
        logger.info(f"Creating processor of type: {processor_type}")
        
        if processor_type == 'message':
            return MessageProcessor(**kwargs)
        elif processor_type == 'event':
            return EventProcessor(**kwargs)
        elif processor_type == 'price':
            return PriceProcessor(**kwargs)
        else:
            logger.error(f"Unsupported processor type: {processor_type}")
            raise ValueError(f"Unsupported processor type: {processor_type}")
    
    @staticmethod
    def get_supported_types():
        """
        获取支持的处理器类型
        
        Returns:
            支持的处理器类型列表
        """
        # 当前已实现的类型
        implemented = ['message', 'event', 'price']
        
        # 计划支持但未实现的类型
        planned = []
        
        return {
            'implemented': implemented,
            'planned': planned
        } 