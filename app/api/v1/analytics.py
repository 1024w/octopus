from flask import request, jsonify
from flask_jwt_extended import jwt_required

from app.api import api_bp
from app.services.analytics_service import AnalyticsService
from app.utils.logging import get_logger

logger = get_logger("api.analytics")

@api_bp.route('/analytics/trending', methods=['GET'])
def get_trending_analysis():
    """获取热门趋势分析"""
    period = request.args.get('period', '24h')  # 24h, 7d, 30d
    limit = request.args.get('limit', 10, type=int)
    platform = request.args.get('platform')  # 可选平台过滤
    
    analytics_service = AnalyticsService()
    trending = analytics_service.get_trending_analysis(
        period=period,
        limit=limit,
        platform=platform
    )
    
    return jsonify({
        'success': True,
        'trending': trending,
        'period': period
    }), 200

@api_bp.route('/analytics/kol/influence', methods=['GET'])
def get_kol_influence():
    """获取KOL影响力分析"""
    period = request.args.get('period', '30d')  # 7d, 30d, 90d
    limit = request.args.get('limit', 20, type=int)
    platform = request.args.get('platform')  # 可选平台过滤
    
    analytics_service = AnalyticsService()
    kol_influence = analytics_service.get_kol_influence(
        period=period,
        limit=limit,
        platform=platform
    )
    
    return jsonify({
        'success': True,
        'kol_influence': kol_influence,
        'period': period
    }), 200

@api_bp.route('/analytics/token/<int:token_id>/price-correlation', methods=['GET'])
def get_token_price_correlation(token_id):
    """获取代币提及与价格相关性分析"""
    period = request.args.get('period', '30d')  # 7d, 30d, 90d, all
    interval = request.args.get('interval', 'day')  # hour, day, week
    
    analytics_service = AnalyticsService()
    correlation = analytics_service.get_token_price_correlation(
        token_id=token_id,
        period=period,
        interval=interval
    )
    
    return jsonify({
        'success': True,
        'token_id': token_id,
        'correlation': correlation,
        'period': period,
        'interval': interval
    }), 200

@api_bp.route('/analytics/token/<int:token_id>/kol-impact', methods=['GET'])
def get_token_kol_impact(token_id):
    """获取KOL对特定代币的影响分析"""
    period = request.args.get('period', '30d')  # 7d, 30d, 90d, all
    limit = request.args.get('limit', 10, type=int)
    
    analytics_service = AnalyticsService()
    kol_impact = analytics_service.get_token_kol_impact(
        token_id=token_id,
        period=period,
        limit=limit
    )
    
    return jsonify({
        'success': True,
        'token_id': token_id,
        'kol_impact': kol_impact,
        'period': period
    }), 200

@api_bp.route('/analytics/platform-distribution', methods=['GET'])
def get_platform_distribution():
    """获取各平台提及分布分析"""
    period = request.args.get('period', '30d')  # 7d, 30d, 90d, all
    
    analytics_service = AnalyticsService()
    distribution = analytics_service.get_platform_distribution(period=period)
    
    return jsonify({
        'success': True,
        'distribution': distribution,
        'period': period
    }), 200

@api_bp.route('/analytics/token/<int:token_id>/sentiment', methods=['GET'])
def get_token_sentiment(token_id):
    """获取代币情感分析"""
    period = request.args.get('period', '30d')  # 7d, 30d, 90d, all
    interval = request.args.get('interval', 'day')  # day, week
    
    analytics_service = AnalyticsService()
    sentiment = analytics_service.get_token_sentiment(
        token_id=token_id,
        period=period,
        interval=interval
    )
    
    return jsonify({
        'success': True,
        'token_id': token_id,
        'sentiment': sentiment,
        'period': period,
        'interval': interval
    }), 200

@api_bp.route('/analytics/explosion-detection', methods=['GET'])
def get_explosion_detection():
    """获取爆发检测结果"""
    days = request.args.get('days', 7, type=int)  # 分析最近多少天的数据
    threshold = request.args.get('threshold', 200, type=int)  # 爆发阈值百分比
    
    analytics_service = AnalyticsService()
    explosions = analytics_service.get_explosion_detection(
        days=days,
        threshold=threshold
    )
    
    return jsonify({
        'success': True,
        'explosions': explosions,
        'days': days,
        'threshold': threshold
    }), 200

@api_bp.route('/analytics/token/<int:token_id>/event-impact', methods=['GET'])
def get_token_event_impact(token_id):
    """获取事件对代币的影响分析"""
    period = request.args.get('period', '90d')  # 30d, 90d, all
    
    analytics_service = AnalyticsService()
    event_impact = analytics_service.get_token_event_impact(
        token_id=token_id,
        period=period
    )
    
    return jsonify({
        'success': True,
        'token_id': token_id,
        'event_impact': event_impact,
        'period': period
    }), 200