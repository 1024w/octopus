from celery import chain
from app import celery
from app.tasks.collectors.twitter_collector import collect as twitter_collect
from app.tasks.collectors.telegram_collector import collect as telegram_collect
from app.tasks.collectors.reddit_collector import collect as reddit_collect
from app.tasks.collectors.discord_collector import collect as discord_collect
from app.tasks.processors.message_processor import process_collector_messages
from app.utils.logging import get_logger

logger = get_logger("tasks.chains")

@celery.task(bind=True, name="app.tasks.chains.collect_and_process")
def collect_and_process(self, collector_id, collector_type, task_id=None):
    """
    创建采集和处理的任务链
    
    Args:
        collector_id: 采集器ID
        collector_type: 采集器类型 (twitter, telegram, reddit, discord)
        task_id: 任务ID，可选
    
    Returns:
        任务链ID
    """
    logger.info(f"Creating task chain for collector_id: {collector_id}, type: {collector_type}, task_id: {task_id}")
    
    # 根据采集器类型选择采集任务
    if collector_type == 'twitter':
        collect_task = twitter_collect.s(collector_id, task_id)
    elif collector_type == 'telegram':
        collect_task = telegram_collect.s(collector_id, task_id)
    elif collector_type == 'reddit':
        collect_task = reddit_collect.s(collector_id, task_id)
    elif collector_type == 'discord':
        collect_task = discord_collect.s(collector_id, task_id)
    else:
        logger.error(f"Unsupported collector type: {collector_type}")
        raise ValueError(f"Unsupported collector type: {collector_type}")
    
    # 创建处理任务
    process_task = process_collector_messages.s(collector_id, task_id)
    
    # 创建并执行任务链
    task_chain = chain(collect_task, process_task)
    result = task_chain.apply_async()
    
    logger.info(f"Task chain created with ID: {result.id}")
    return result.id 