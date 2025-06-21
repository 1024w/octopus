from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch.exceptions import ElasticsearchException
from redis.exceptions import RedisError
from jwt.exceptions import PyJWTError

from app.utils.logging import get_logger

logger = get_logger("error_handlers")

def register_error_handlers(app):
    """
    注册全局错误处理函数
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(400)
    def bad_request_error(error):
        logger.error(f"Bad request: {error}")
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.error(f"Unauthorized: {error}")
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.error(f"Forbidden: {error}")
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"Not found: {error}")
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        logger.error(f"Method not allowed: {error}")
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for the requested URL'
        }), 405
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        logger.error(f"Too many requests: {error}")
        return jsonify({
            'success': False,
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded'
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        logger.error(f"Database error: {error}")
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'A database error occurred'
        }), 500
    
    @app.errorhandler(ElasticsearchException)
    def handle_es_error(error):
        logger.error(f"Elasticsearch error: {error}")
        return jsonify({
            'success': False,
            'error': 'Search Engine Error',
            'message': 'A search engine error occurred'
        }), 500
    
    @app.errorhandler(RedisError)
    def handle_redis_error(error):
        logger.error(f"Redis error: {error}")
        return jsonify({
            'success': False,
            'error': 'Cache Error',
            'message': 'A cache error occurred'
        }), 500
    
    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        logger.error(f"JWT error: {error}")
        return jsonify({
            'success': False,
            'error': 'Authentication Error',
            'message': 'An authentication error occurred'
        }), 401
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        logger.error(f"HTTP exception: {error}")
        return jsonify({
            'success': False,
            'error': error.name,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        logger.exception(f"Unhandled exception: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500 