from flask import Blueprint, request, jsonify
from app.services.trend_service import TrendService
from app.utils.logging import get_logger

logger = get_logger("api.trends")
trends_bp = Blueprint('trends_bp', __name__)
trend_service = TrendService()

@trends_bp.route('/trends/mentions', methods=['GET'])
def get_mention_trends():
    """获取提及趋势"""
    token_id = request.args.get('token_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    if not token_id:
        return jsonify({
            'success': False,
            'message': 'Missing required parameter: token_id'
        }), 400
    
    try:
        trends = trend_service.get_mention_trends(token_id=token_id, days=days)
        
        return jsonify({
            'success': True,
            'data': trends
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error getting mention trends: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting mention trends'
        }), 500

@trends_bp.route('/trends/tokens/trending', methods=['GET'])
def get_trending_tokens():
    """获取热门代币"""
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    try:
        trending_tokens = trend_service.get_trending_tokens(days=days, limit=limit)
        
        return jsonify({
            'success': True,
            'data': trending_tokens
        })
    
    except Exception as e:
        logger.error(f"Error getting trending tokens: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting trending tokens'
        }), 500

@trends_bp.route('/trends/platforms/activity', methods=['GET'])
def get_platform_activity():
    """获取平台活动数据"""
    days = request.args.get('days', 7, type=int)
    
    try:
        activity = trend_service.get_platform_activity(days=days)
        
        return jsonify({
            'success': True,
            'data': activity
        })
    
    except Exception as e:
        logger.error(f"Error getting platform activity: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting platform activity'
        }), 500

@trends_bp.route('/trends/correlation', methods=['GET'])
def get_correlation_analysis():
    """获取相关性分析"""
    token_id = request.args.get('token_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    if not token_id:
        return jsonify({
            'success': False,
            'message': 'Missing required parameter: token_id'
        }), 400
    
    try:
        correlation = trend_service.get_correlation_analysis(token_id=token_id, days=days)
        
        return jsonify({
            'success': True,
            'data': correlation
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error getting correlation analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting correlation analysis'
        }), 500

@trends_bp.route('/trends/overview', methods=['GET'])
def get_trend_overview():
    """获取趋势概览"""
    days = request.args.get('days', 7, type=int)
    
    try:
        # 获取热门代币
        trending_tokens = trend_service.get_trending_tokens(days=days, limit=5)
        
        # 获取平台活动
        platform_activity = trend_service.get_platform_activity(days=days)
        
        # 组合数据
        overview = {
            'trending_tokens': trending_tokens,
            'platform_activity': platform_activity,
            'time_range': {
                'days': days
            }
        }
        
        return jsonify({
            'success': True,
            'data': overview
        })
    
    except Exception as e:
        logger.error(f"Error getting trend overview: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting trend overview'
        }), 500 