import datetime
from app import celery
from app.processors.processor_factory import ProcessorFactory
from app.models import db
from app.models.collector import Collector
from app.utils.logging import get_logger

logger = get_logger("tasks.processors.message")

@celery.task(bind=True, name="app.tasks.processors.message_processor.process_all")
def process_all(self, task_id=None):
    """
    处理所有未处理的消息
    
    Args:
        task_id: 任务ID，可选
    
    Returns:
        处理的消息数量
    """
    logger.info(f"Starting message processing task for all unprocessed messages, task_id: {task_id}")
    
    try:
        # 使用工厂创建处理器
        message_processor = ProcessorFactory.create_processor('message')
        result = message_processor.process_unprocessed_messages()
        
        logger.info(f"Message processing task completed, processed: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in message processing task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.message_processor.process_collector_messages")
def process_collector_messages(self, collector_id, task_id=None):
    """
    处理特定采集器的消息
    
    Args:
        collector_id: 采集器ID
        task_id: 任务ID，可选
    
    Returns:
        处理的消息数量
    """
    logger.info(f"Starting message processing task for collector_id: {collector_id}, task_id: {task_id}")
    
    # 更新采集器状态
    collector = Collector.query.get(collector_id)
    if collector:
        collector.processing_status = 'running'
        collector.processing_message = f"Task ID: {task_id}" if task_id else "Running"
        db.session.commit()
    
    try:
        # 使用工厂创建处理器
        message_processor = ProcessorFactory.create_processor('message')
        result = message_processor.process_collector_messages(collector_id)
        
        # 更新采集器状态
        if collector:
            collector.processing_status = 'success'
            collector.processing_message = f"Processed {result} messages"
            collector.last_processed_at = datetime.datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Message processing task completed for collector_id: {collector_id}, processed: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in message processing task: {str(e)}")
        
        # 更新采集器状态为失败
        if collector:
            collector.processing_status = 'failure'
            collector.processing_message = f"Error: {str(e)}"
            db.session.commit()
        
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.message_processor.process_messages")
def process_messages(self, collector_id=None, task_id=None, limit=100):
    """
    消息处理任务
    
    Args:
        collector_id: 采集器ID，可选，如果提供则只处理该采集器的消息
        task_id: 任务ID，可选
        limit: 处理消息的最大数量，默认100
    
    Returns:
        处理的消息数量和提及数量
    """
    logger.info(f"Starting message processor task, collector_id: {collector_id}, task_id: {task_id}, limit: {limit}")
    
    # 更新采集器状态（如果提供了采集器ID）
    if collector_id:
        collector = Collector.query.get(collector_id)
        if collector:
            collector.last_run_message = f"Processing messages... Task ID: {task_id}" if task_id else "Processing messages..."
            db.session.commit()
    
    try:
        # 创建处理器
        processor = MessageProcessor()
        
        # 处理消息
        if collector_id:
            message_count, mention_count = processor.process_collector_messages(collector_id, limit)
        else:
            message_count, mention_count = processor.process_unprocessed_messages(limit)
        
        # 更新采集器状态
        if collector_id:
            collector = Collector.query.get(collector_id)
            if collector:
                collector.last_run_message = f"Processed {message_count} messages, found {mention_count} mentions"
                db.session.commit()
        
        logger.info(f"Message processor task completed, processed {message_count} messages, found {mention_count} mentions")
        return {'message_count': message_count, 'mention_count': mention_count}
    
    except Exception as e:
        logger.exception(f"Error in message processor task: {str(e)}")
        
        # 更新采集器状态
        if collector_id:
            collector = Collector.query.get(collector_id)
            if collector:
                collector.last_run_message = f"Error processing messages: {str(e)}"
                db.session.commit()
        
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.processors.message_processor.process_all_messages")
def process_all_messages(self, batch_size=100, max_batches=10):
    """
    处理所有未处理的消息
    
    Args:
        batch_size: 每批处理的消息数量，默认100
        max_batches: 最大批次数，默认10
        
    Returns:
        处理的消息数量和提及数量
    """
    logger.info(f"Starting process_all_messages task, batch_size: {batch_size}, max_batches: {max_batches}")
    
    processor = MessageProcessor()
    total_message_count = 0
    total_mention_count = 0
    
    for i in range(max_batches):
        message_count, mention_count = processor.process_unprocessed_messages(batch_size)
        total_message_count += message_count
        total_mention_count += mention_count
        
        # 如果没有处理任何消息，说明已经处理完所有消息
        if message_count == 0:
            break
    
    logger.info(f"process_all_messages task completed, processed {total_message_count} messages, found {total_mention_count} mentions")
    return {'message_count': total_message_count, 'mention_count': total_mention_count} 