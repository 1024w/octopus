import json
import datetime
import uuid
from app import celery
from app.models import db
from app.models.collector import Collector
from app.tasks.chains import collect_and_process
from app.utils.logging import get_logger

logger = get_logger("services.collector")

class CollectorService:
    """采集器服务类，处理与采集器相关的业务逻辑"""
    
    def get_all_collectors(self):
        """
        获取所有采集器
        
        Returns:
            所有采集器的列表
        """
        logger.info("Fetching all collectors")
        collectors = Collector.query.all()
        return collectors
    
    def get_collector_by_id(self, collector_id):
        """
        根据ID获取采集器
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            采集器对象，如果不存在则返回None
        """
        logger.info(f"Fetching collector with ID: {collector_id}")
        collector = Collector.query.get(collector_id)
        return collector
    
    def create_collector(self, name, collector_type, config, description=None, creator_id=None):
        """
        创建新的采集器
        
        Args:
            name: 采集器名称
            collector_type: 采集器类型 (twitter, telegram, reddit, discord等)
            config: 采集器配置，JSON格式的字符串或字典
            description: 采集器描述，可选
            creator_id: 创建者ID，可选
            
        Returns:
            新创建的采集器对象
            
        Raises:
            ValueError: 如果配置格式不正确或采集器类型不支持
        """
        logger.info(f"Creating new collector: {name}, type: {collector_type}")
        
        # 验证采集器类型
        if collector_type not in ['twitter', 'telegram', 'reddit', 'discord']:
            logger.error(f"Unsupported collector type: {collector_type}")
            raise ValueError(f"Unsupported collector type: {collector_type}")
        
        # 确保配置是有效的JSON
        if isinstance(config, dict):
            config_json = json.dumps(config)
        else:
            try:
                # 验证是否为有效的JSON
                json.loads(config)
                config_json = config
            except Exception as e:
                logger.error(f"Invalid configuration format: {str(e)}")
                raise ValueError(f"Invalid configuration format: {str(e)}")
        
        collector = Collector(
            name=name,
            type=collector_type,
            config=config_json,
            description=description,
            creator_id=creator_id,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.session.add(collector)
        db.session.commit()
        
        logger.info(f"Collector created with ID: {collector.id}")
        return collector
    
    def update_collector(self, collector_id, name=None, collector_type=None, 
                         config=None, description=None, active=None):
        """
        更新采集器
        
        Args:
            collector_id: 采集器ID
            name: 新的采集器名称，可选
            collector_type: 新的采集器类型，可选
            config: 新的采集器配置，可选
            description: 新的采集器描述，可选
            active: 是否激活，可选
            
        Returns:
            更新后的采集器对象
            
        Raises:
            ValueError: 如果采集器不存在或配置格式不正确
        """
        logger.info(f"Updating collector with ID: {collector_id}")
        
        collector = Collector.query.get(collector_id)
        if not collector:
            logger.error(f"Collector with ID {collector_id} not found")
            raise ValueError(f"Collector with ID {collector_id} not found")
        
        if name is not None:
            collector.name = name
        
        if collector_type is not None:
            # 验证采集器类型
            if collector_type not in ['twitter', 'telegram', 'reddit', 'discord']:
                logger.error(f"Unsupported collector type: {collector_type}")
                raise ValueError(f"Unsupported collector type: {collector_type}")
            collector.type = collector_type
        
        if config is not None:
            # 确保配置是有效的JSON
            if isinstance(config, dict):
                config_json = json.dumps(config)
            else:
                try:
                    # 验证是否为有效的JSON
                    json.loads(config)
                    config_json = config
                except Exception as e:
                    logger.error(f"Invalid configuration format: {str(e)}")
                    raise ValueError(f"Invalid configuration format: {str(e)}")
            collector.config = config_json
        
        if description is not None:
            collector.description = description
        
        if active is not None:
            collector.active = active
        
        collector.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Collector updated: {collector.id}")
        return collector
    
    def delete_collector(self, collector_id):
        """
        删除采集器
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            是否成功删除
            
        Raises:
            ValueError: 如果采集器不存在
        """
        logger.info(f"Deleting collector with ID: {collector_id}")
        
        collector = Collector.query.get(collector_id)
        if not collector:
            logger.error(f"Collector with ID {collector_id} not found")
            raise ValueError(f"Collector with ID {collector_id} not found")
        
        db.session.delete(collector)
        db.session.commit()
        
        logger.info(f"Collector deleted: {collector_id}")
        return True
    
    def run_collector(self, collector_id):
        """
        手动运行采集器
        
        Args:
            collector_id: 采集器ID
            
        Returns:
            任务ID
            
        Raises:
            ValueError: 如果采集器不存在或不活跃
        """
        logger.info(f"Running collector with ID: {collector_id}")
        
        collector = Collector.query.get(collector_id)
        if not collector:
            logger.error(f"Collector with ID {collector_id} not found")
            raise ValueError(f"Collector with ID {collector_id} not found")
        
        if not collector.active:
            logger.error(f"Collector with ID {collector_id} is not active")
            raise ValueError(f"Collector with ID {collector_id} is not active")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 更新采集器状态
        collector.last_run_at = datetime.datetime.utcnow()
        collector.last_run_status = 'pending'
        collector.last_run_message = f"Task ID: {task_id}"
        db.session.commit()
        
        # 创建任务链
        result_id = collect_and_process.delay(collector_id, collector.type, task_id)
        
        logger.info(f"Collector task chain started with ID: {result_id}")
        return result_id
    
    def get_task_status(self, task_id):
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        logger.info(f"Checking status for task ID: {task_id}")
        
        # 获取任务状态
        task = celery.AsyncResult(task_id)
        
        # 查找与此任务关联的采集器
        collector = Collector.query.filter(
            (Collector.last_run_message.like(f"%Task ID: {task_id}%"))
        ).first()
        
        result = {
            'task_id': task_id,
            'status': task.status,
            'result': task.result if task.successful() else None,
            'collector': {
                'id': collector.id,
                'name': collector.name,
                'type': collector.type,
                'last_run_status': collector.last_run_status,
                'last_run_message': collector.last_run_message,
                'last_run_at': collector.last_run_at
            } if collector else None
        }
        
        logger.info(f"Task status: {task.status} for task ID: {task_id}")
        return result 