from flask import Blueprint, request, jsonify
from app.services.message_service import MessageService
from app.utils.logging import get_logger

logger = get_logger("api.messages")
messages_bp = Blueprint('messages_bp', __name__)
message_service = MessageService()

@messages_bp.route('/messages', methods=['GET'])
def get_messages():
    """获取消息列表"""
    collector_id = request.args.get('collector_id', type=int)
    platform = request.args.get('platform')
    processed = request.args.get('processed', type=lambda x: x.lower() == 'true' if x else None)
    has_mentions = request.args.get('has_mentions', type=lambda x: x.lower() == 'true' if x else None)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    messages = message_service.get_messages(
        collector_id=collector_id,
        platform=platform,
        processed=processed,
        has_mentions=has_mentions,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )
    
    total_count = message_service.count_messages(
        collector_id=collector_id,
        platform=platform,
        processed=processed,
        has_mentions=has_mentions,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'success': True,
        'data': [message.to_dict() for message in messages],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page
        }
    })

@messages_bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    """获取消息详情"""
    message = message_service.get_message_by_id(message_id)
    
    if not message:
        return jsonify({
            'success': False,
            'message': f'Message with ID {message_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': message.to_dict(include_content=True)
    })

@messages_bp.route('/messages/<int:message_id>/mentions', methods=['GET'])
def get_message_mentions(message_id):
    """获取消息中的代币提及"""
    message = message_service.get_message_by_id(message_id)
    
    if not message:
        return jsonify({
            'success': False,
            'message': f'Message with ID {message_id} not found'
        }), 404
    
    mentions = message_service.get_message_mentions(message_id)
    
    return jsonify({
        'success': True,
        'data': {
            'message': message.to_dict(),
            'mentions': [mention.to_dict() for mention in mentions]
        }
    })

@messages_bp.route('/messages/search', methods=['GET'])
def search_messages():
    """搜索消息"""
    query = request.args.get('q')
    collector_id = request.args.get('collector_id', type=int)
    platform = request.args.get('platform')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'Missing required parameter: q (search query)'
        }), 400
    
    messages, total_count = message_service.search_messages(
        query=query,
        collector_id=collector_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'data': [message.to_dict() for message in messages],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page
        }
    })

@messages_bp.route('/messages/stats', methods=['GET'])
def get_message_stats():
    """获取消息统计数据"""
    collector_id = request.args.get('collector_id', type=int)
    platform = request.args.get('platform')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        stats = message_service.get_message_stats(
            collector_id=collector_id,
            platform=platform,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting message stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting message stats'
        }), 500

@messages_bp.route('/messages/platforms', methods=['GET'])
def get_platforms():
    """获取所有消息平台"""
    try:
        platforms = message_service.get_platforms()
        
        return jsonify({
            'success': True,
            'data': platforms
        })
    
    except Exception as e:
        logger.error(f"Error getting platforms: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting platforms'
        }), 500 