import datetime
from app import celery
from app.processors.processor_factory import ProcessorFactory
from app.models import db
from app.models.event import Event
from app.utils.logging import get_logger

logger = get_logger("tasks.processors.event")

@celery.task(bind=True, name="app.tasks.processors.event_processor.process_all")
def process_all(self, task_id=None):
    """
    处理所有未处理的事件
    
    Args:
        task_id: 任务ID，可选
    
    Returns:
        处理的事件数量
    """
    logger.info(f"Starting event processing task for all unprocessed events, task_id: {task_id}")
    
    try:
        # 使用工厂创建处理器
        event_processor = ProcessorFactory.create_processor('event')
        result = event_processor.process_unprocessed_events()
        
        logger.info(f"Event processing task completed, processed: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in event processing task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.event_processor.process_event")
def process_event(self, event_id, task_id=None):
    """
    处理特定事件
    
    Args:
        event_id: 事件ID
        task_id: 任务ID，可选
    
    Returns:
        处理结果
    """
    logger.info(f"Starting event processing task for event_id: {event_id}, task_id: {task_id}")
    
    try:
        # 获取事件
        event = Event.query.get(event_id)
        if not event:
            logger.error(f"Event {event_id} not found")
            raise ValueError(f"Event {event_id} not found")
        
        # 使用工厂创建处理器
        event_processor = ProcessorFactory.create_processor('event')
        
        # 解析事件数据
        import json
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
        result = event_processor.process(event_data)
        
        logger.info(f"Event processing task completed for event_id: {event_id}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in event processing task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise 