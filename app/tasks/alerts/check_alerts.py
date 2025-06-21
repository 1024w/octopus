import datetime
from app import celery
from app.services.alert_service import AlertService
from app.utils.logging import get_logger

logger = get_logger("tasks.alerts.check_alerts")

@celery.task(bind=True, name="app.tasks.alerts.check_alerts.check_all")
def check_all(self):
    """
    检查所有警报
    
    Returns:
        触发的警报数量
    """
    logger.info("Starting check_all_alerts task")
    
    try:
        alert_service = AlertService()
        result = alert_service.check_all_alerts()
        
        logger.info(f"Check all alerts task completed, triggered: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in check all alerts task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.alerts.check_alerts.check_price_alerts")
def check_price_alerts(self):
    """
    检查价格警报
    
    Returns:
        触发的警报数量
    """
    logger.info("Starting check_price_alerts task")
    
    try:
        alert_service = AlertService()
        result = alert_service.check_price_alerts()
        
        logger.info(f"Check price alerts task completed, triggered: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in check price alerts task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.alerts.check_alerts.check_sentiment_alerts")
def check_sentiment_alerts(self):
    """
    检查情感警报
    
    Returns:
        触发的警报数量
    """
    logger.info("Starting check_sentiment_alerts task")
    
    try:
        alert_service = AlertService()
        result = alert_service.check_sentiment_alerts()
        
        logger.info(f"Check sentiment alerts task completed, triggered: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in check sentiment alerts task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise

@celery.task(bind=True, name="app.tasks.alerts.check_alerts.check_mention_alerts")
def check_mention_alerts(self):
    """
    检查提及警报
    
    Returns:
        触发的警报数量
    """
    logger.info("Starting check_mention_alerts task")
    
    try:
        alert_service = AlertService()
        result = alert_service.check_mention_alerts()
        
        logger.info(f"Check mention alerts task completed, triggered: {result}")
        return result
    
    except Exception as e:
        logger.exception(f"Error in check mention alerts task: {str(e)}")
        # 重新引发异常，让Celery知道任务失败
        raise 