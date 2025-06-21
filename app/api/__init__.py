from flask import Blueprint, jsonify
from app.utils.logging import get_logger

logger = get_logger("api")
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# 导入v1目录下的API路由
from app.api.v1 import *

# 注册新的API蓝图
api_bp.register_blueprint(alerts_bp, url_prefix='/alert')
api_bp.register_blueprint(processors_bp, url_prefix='/processor')
api_bp.register_blueprint(messages_bp, url_prefix='/message')
api_bp.register_blueprint(trends_bp, url_prefix='/trend')
# 以下蓝图已合并到对应的文件中，不再需要注册
# api_bp.register_blueprint(alert_api, url_prefix='/alert')
# api_bp.register_blueprint(collector_api, url_prefix='/collector')
# api_bp.register_blueprint(processor_api, url_prefix='/processor')
# api_bp.register_blueprint(message_api, url_prefix='/message')
# api_bp.register_blueprint(trend_api, url_prefix='/trend')
# api_bp.register_blueprint(token_api, url_prefix='/token')
# api_bp.register_blueprint(user_api, url_prefix='/user')

@api_bp.route('/', methods=['GET'])
def index():
    """API根路径，返回API版本信息"""
    return jsonify({
        'success': True,
        'data': {
            'name': 'Octopus API',
            'version': 'v1',
            'status': 'running'
        }
    })

@api_bp.errorhandler(404)
def handle_not_found(e):
    """处理404错误"""
    return jsonify({
        'success': False,
        'message': 'API endpoint not found'
    }), 404

@api_bp.errorhandler(405)
def handle_method_not_allowed(e):
    """处理405错误"""
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@api_bp.errorhandler(500)
def handle_server_error(e):
    """处理500错误"""
    logger.error(f"Server error: {str(e)}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

def init_app(app):
    """初始化API蓝图"""
    app.register_blueprint(api_bp)
    logger.info("API blueprints registered") 