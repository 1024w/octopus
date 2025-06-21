from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.services.event_service import EventService
from app.utils.logging import get_logger

logger = get_logger("api.events")

@api_bp.route('/events', methods=['GET'])
def get_events():
    """获取事件列表，支持分页和筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    token_id = request.args.get('token_id', type=int)
    event_type = request.args.get('event_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform')
    
    event_service = EventService()
    events, total = event_service.get_events(
        page=page,
        per_page=per_page,
        token_id=token_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        platform=platform
    )
    
    return jsonify({
        'success': True,
        'events': [event.to_dict() for event in events],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

@api_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """获取特定事件详情"""
    event_service = EventService()
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({
            'success': False,
            'message': 'Event not found'
        }), 404
    
    return jsonify({
        'success': True,
        'event': event.to_dict(with_related=True)
    }), 200

@api_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    """创建新事件"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    required_fields = ['token_id', 'event_type', 'title', 'timestamp']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    event_service = EventService()
    
    try:
        event = event_service.create_event(
            token_id=data['token_id'],
            event_type=data['event_type'],
            title=data['title'],
            description=data.get('description', ''),
            timestamp=data['timestamp'],
            platform=data.get('platform'),
            source_url=data.get('source_url'),
            source_id=data.get('source_id'),
            mention_id=data.get('mention_id'),
            price_impact=data.get('price_impact'),
            created_by=get_jwt_identity()
        )
        
        logger.info(f"Created new event: {data['title']} for token {data['token_id']}")
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event': event.to_dict()
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@api_bp.route('/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """更新事件信息"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    event_service = EventService()
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({
            'success': False,
            'message': 'Event not found'
        }), 404
    
    try:
        updated_event = event_service.update_event(
            event_id=event_id,
            token_id=data.get('token_id'),
            event_type=data.get('event_type'),
            title=data.get('title'),
            description=data.get('description'),
            timestamp=data.get('timestamp'),
            platform=data.get('platform'),
            source_url=data.get('source_url'),
            source_id=data.get('source_id'),
            mention_id=data.get('mention_id'),
            price_impact=data.get('price_impact'),
            is_significant=data.get('is_significant')
        )
        
        logger.info(f"Updated event: {event_id}")
        return jsonify({
            'success': True,
            'message': 'Event updated successfully',
            'event': updated_event.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@api_bp.route('/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """删除事件"""
    event_service = EventService()
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({
            'success': False,
            'message': 'Event not found'
        }), 404
    
    event_service.delete_event(event_id)
    
    logger.info(f"Deleted event: {event_id}")
    return jsonify({
        'success': True,
        'message': 'Event deleted successfully'
    }), 200

@api_bp.route('/tokens/<int:token_id>/timeline', methods=['GET'])
def get_token_timeline(token_id):
    """获取代币的事件时间线"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    event_types = request.args.get('event_types')
    include_price = request.args.get('include_price', 'true').lower() == 'true'
    include_mentions = request.args.get('include_mentions', 'true').lower() == 'true'
    
    # 解析事件类型列表
    if event_types:
        event_types = event_types.split(',')
    
    event_service = EventService()
    timeline = event_service.get_token_timeline(
        token_id=token_id,
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        include_price=include_price,
        include_mentions=include_mentions
    )
    
    return jsonify({
        'success': True,
        'token_id': token_id,
        'timeline': timeline
    }), 200

@api_bp.route('/events/types', methods=['GET'])
def get_event_types():
    """获取所有事件类型"""
    event_service = EventService()
    event_types = event_service.get_event_types()
    
    return jsonify({
        'success': True,
        'event_types': event_types
    }), 200 