# 任务模块初始化文件
from app.utils.logging import get_logger

logger = get_logger("tasks")

# 导入任务子模块
from app.tasks import collectors
from app.tasks import processors 