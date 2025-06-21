import datetime
from app import celery
from app.collectors.collector_factory import CollectorFactory
from app.models import db
from app.models.collector import Collector
from app.utils.logging import get_logger

logger = get_logger("tasks.collectors.telegram")

@celery.task(bind=True, name="app.tasks.collectors.telegram_collector.collect")
def collect(self, collector_id, task_id=None):
    """
    Telegram采集任务
    
    Args:
        collector_id: 采集器ID
        task_id: 任务ID，可选
    
    Returns:
        采集的消息数量
    """
    logger.info(f"Starting Telegram collector task for collector_id: {collector_id}, task_id: {task_id}")
    
    # 更新采集器状态
    collector = Collector.query.get(collector_id)
    if collector:
        collector.last_run_at = datetime.datetime.utcnow()
        collector.last_run_status = 'running'
        collector.last_run_message = f"Task ID: {task_id}" if task_id else "Running"
        db.session.commit()
    
    try:
        # 使用工厂创建采集器
        telegram_collector = CollectorFactory.create_collector('telegram')
        result = telegram_collector.run_collector(collector_id)
        
        logger.info(f"Telegram collector task completed for collector_id: {collector_id}, collected: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in Telegram collector task: {str(e)}")
        
        # 更新采集器状态为失败
        if collector:
            collector.last_run_status = 'failure'
            collector.last_run_message = f"Error: {str(e)}"
            db.session.commit()
        
        # 重新引发异常，让Celery知道任务失败
        raise 