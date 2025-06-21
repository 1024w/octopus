import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from loguru import logger

def setup_logging(app):
    """
    配置应用的日志系统
    
    Args:
        app: Flask应用实例
    """
    # 创建日志目录
    log_dir = Path(app.root_path) / '../logs'
    log_dir.mkdir(exist_ok=True)
    
    # 获取日志级别
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=log_level,
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        log_dir / "app.log",
        rotation="10 MB",  # 日志大小达到10MB时轮转
        retention="1 week",  # 保留1周的日志
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level=log_level,
        compression="zip"  # 压缩轮转的日志
    )
    
    # 配置Flask的日志处理器
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # 获取对应的Loguru级别
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
                
            # 找到调用者的文件和行号
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
                
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # 将Flask的日志重定向到loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    
    # 设置其他库的日志级别
    for logger_name in ['werkzeug', 'sqlalchemy', 'elasticsearch', 'celery']:
        logging.getLogger(logger_name).setLevel(log_level)
    
    app.logger.info(f"Logging is set up with level: {log_level}")
    
    return logger

def get_logger(name=None):
    """
    获取命名的logger实例
    
    Args:
        name: 日志名称，默认为None
        
    Returns:
        loguru.logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger 