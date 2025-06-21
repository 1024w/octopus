import datetime
from app import celery
from app.processors.processor_factory import ProcessorFactory
from app.models import db
from app.models.token import Token
from app.utils.logging import get_logger

logger = get_logger("tasks.processors.price")

@celery.task(bind=True, name="app.tasks.processors.price_processor.update_all_prices")
def update_all_prices(self, task_id=None):
    """
    更新所有代币价格
    
    Args:
        task_id: 任务ID，可选
    
    Returns:
        更新的代币数量
    """
    logger.info(f"Starting price update task for all tokens, task_id: {task_id}")
    
    try:
        # 使用工厂创建处理器
        price_processor = ProcessorFactory.create_processor('price')
        result = price_processor.update_all_prices()
        
        logger.info(f"Price update task completed, updated: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in price update task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.price_processor.update_token_price")
def update_token_price(self, token_id=None, symbol=None, task_id=None):
    """
    更新特定代币价格
    
    Args:
        token_id: 代币ID，可选
        symbol: 代币符号，可选，当token_id未提供时使用
        task_id: 任务ID，可选
    
    Returns:
        更新结果
    """
    logger.info(f"Starting price update task for token_id: {token_id}, symbol: {symbol}, task_id: {task_id}")
    
    try:
        # 使用工厂创建处理器
        price_processor = ProcessorFactory.create_processor('price')
        result = price_processor.process(token_id=token_id, symbol=symbol)
        
        logger.info(f"Price update task completed for token: {symbol or token_id}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in price update task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.price_processor.update_trending_tokens")
def update_trending_tokens(self, task_id=None):
    """
    更新趋势代币
    
    Args:
        task_id: 任务ID，可选
    
    Returns:
        更新的代币数量
    """
    logger.info(f"Starting trending tokens update task, task_id: {task_id}")
    
    try:
        # 使用工厂创建处理器
        price_processor = ProcessorFactory.create_processor('price')
        result = price_processor.update_trending_tokens()
        
        logger.info(f"Trending tokens update task completed, updated: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in trending tokens update task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise 