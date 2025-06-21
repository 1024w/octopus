from app.collectors.twitter_collector import TwitterCollector
from app.collectors.telegram_collector import TelegramCollector
from app.collectors.reddit_collector import RedditCollector
from app.collectors.discord_collector import DiscordCollector
from app.utils.logging import get_logger

logger = get_logger("collectors.factory")

class CollectorFactory:
    """采集器工厂，负责创建不同类型的采集器"""
    
    @staticmethod
    def create_collector(collector_type, **kwargs):
        """
        创建采集器实例
        
        Args:
            collector_type: 采集器类型，支持 'twitter', 'telegram', 'reddit', 'discord', 'wechat', 'qq'
            **kwargs: 传递给采集器构造函数的参数
            
        Returns:
            采集器实例
            
        Raises:
            ValueError: 如果采集器类型不支持
        """
        logger.info(f"Creating collector of type: {collector_type}")
        
        if collector_type == 'twitter':
            return TwitterCollector(**kwargs)
        elif collector_type == 'telegram':
            return TelegramCollector(**kwargs)
        elif collector_type == 'reddit':
            return RedditCollector(**kwargs)
        elif collector_type == 'discord':
            return DiscordCollector(**kwargs)
        elif collector_type == 'wechat':
            # 未实现，预留接口
            raise ValueError(f"Collector type '{collector_type}' is not implemented yet")
        elif collector_type == 'qq':
            # 未实现，预留接口
            raise ValueError(f"Collector type '{collector_type}' is not implemented yet")
        else:
            logger.error(f"Unsupported collector type: {collector_type}")
            raise ValueError(f"Unsupported collector type: {collector_type}")
    
    @staticmethod
    def get_supported_types():
        """
        获取支持的采集器类型
        
        Returns:
            支持的采集器类型列表
        """
        # 当前已实现的类型
        implemented = ['twitter', 'telegram', 'reddit', 'discord']
        
        # 计划支持但未实现的类型
        planned = ['wechat', 'qq']
        
        return {
            'implemented': implemented,
            'planned': planned
        } 