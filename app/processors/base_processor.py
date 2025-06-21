from abc import ABC, abstractmethod
from app.utils.logging import get_logger

logger = get_logger("processors.base")

class BaseProcessor(ABC):
    """处理器基类，定义处理器通用接口"""
    
    def __init__(self):
        """初始化处理器"""
        self.processor_type = self._get_processor_type()
        logger.info(f"Initialized {self.processor_type} processor")
    
    @abstractmethod
    def _get_processor_type(self):
        """获取处理器类型，由子类实现"""
        pass
    
    @abstractmethod
    def process(self, data, **kwargs):
        """
        处理数据，由子类实现
        
        Args:
            data: 待处理的数据
            **kwargs: 额外参数
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def batch_process(self, data_list, **kwargs):
        """
        批量处理数据，由子类实现
        
        Args:
            data_list: 待处理的数据列表
            **kwargs: 额外参数
            
        Returns:
            处理结果
        """
        pass 