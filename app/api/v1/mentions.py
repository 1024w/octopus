from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.services.mention_service import MentionService
from app.utils.logging import get_logger

logger = get_logger("api.mentions")

@api_bp.route('/mentions', methods=['GET'])
def get_mentions():
    """获取提及记录列表，支持分页和筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    platform = request.args.get('platform')  # twitter, telegram, wechat, qq
    token_id = request.args.get('token_id', type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    mention_service = MentionService()
    mentions, total = mention_service.get_mentions(
        page=page,
        per_page=per_page,
        platform=platform,
        token_id=token_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'success': True,
        'mentions': [mention.to_dict() for mention in mentions],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

@api_bp.route('/mentions/<int:mention_id>', methods=['GET'])
def get_mention(mention_id):
    """获取特定提及记录详情"""
    mention_service = MentionService()
    mention = mention_service.get_mention_by_id(mention_id)
    
    if not mention:
        return jsonify({
            'success': False,
            'message': 'Mention not found'
        }), 404
    
    return jsonify({
        'success': True,
        'mention': mention.to_dict(with_message=True)
    }), 200

@api_bp.route('/mentions/search', methods=['GET'])
def search_mentions():
    """全文搜索提及记录"""
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    platform = request.args.get('platform')
    token_id = request.args.get('token_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'Search query is required'
        }), 400
    
    mention_service = MentionService()
    mentions, total = mention_service.search_mentions(
        query=query,
        page=page,
        per_page=per_page,
        platform=platform,
        token_id=token_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'success': True,
        'mentions': [mention.to_dict() for mention in mentions],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

@api_bp.route('/mentions/<int:mention_id>/verify', methods=['POST'])
@jwt_required()
def verify_mention(mention_id):
    """验证或修正提及记录，需要管理员权限"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    is_valid = data.get('is_valid')
    token_id = data.get('token_id')
    notes = data.get('notes')
    
    if is_valid is None:
        return jsonify({
            'success': False,
            'message': 'is_valid field is required'
        }), 400
    
    mention_service = MentionService()
    mention = mention_service.get_mention_by_id(mention_id)
    
    if not mention:
        return jsonify({
            'success': False,
            'message': 'Mention not found'
        }), 404
    
    try:
        updated_mention = mention_service.verify_mention(
            mention_id=mention_id,
            is_valid=is_valid,
            token_id=token_id,
            notes=notes,
            verified_by=get_jwt_identity()
        )
        
        logger.info(f"Verified mention: {mention_id}, is_valid: {is_valid}")
        return jsonify({
            'success': True,
            'message': 'Mention verified successfully',
            'mention': updated_mention.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@api_bp.route('/mentions/stats', methods=['GET'])
def get_mention_stats():
    """获取提及记录的统计数据"""
    period = request.args.get('period', '7d')  # 24h, 7d, 30d, all
    platform = request.args.get('platform')
    group_by = request.args.get('group_by', 'day')  # hour, day, week, platform, token
    
    mention_service = MentionService()
    stats = mention_service.get_mention_stats(
        period=period,
        platform=platform,
        group_by=group_by
    )
    
    return jsonify({
        'success': True,
        'stats': stats,
        'period': period,
        'group_by': group_by
    }), 200 