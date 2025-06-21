# 导入所有API路由
from app.api.v1.auth import *
from app.api.v1.collectors import *
from app.api.v1.tokens import *
from app.api.v1.users import *
from app.api.v1.mentions import *
from app.api.v1.events import *
from app.api.v1.analytics import *
from app.api.v1.alerts import alerts_bp
from app.api.v1.messages import messages_bp
from app.api.v1.processors import processors_bp
from app.api.v1.trends import trends_bp

# 以下导入已合并到对应的文件中，不再需要
# from app.api.v1.alert_api import alert_api
# from app.api.v1.collector_api import collector_api
# from app.api.v1.processor_api import processor_api
# from app.api.v1.message_api import message_api
# from app.api.v1.trend_api import trend_api
# from app.api.v1.token_api import token_api
# from app.api.v1.user_api import user_api 