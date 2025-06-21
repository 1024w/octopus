from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.services.token_service import TokenService
from app.services.sentiment_service import SentimentService
from app.services.trend_service import TrendService
from app.utils.logging import get_logger

logger = get_logger("api.tokens")
token_service = TokenService()
sentiment_service = SentimentService()
trend_service = TrendService()

@api_bp.route('/tokens', methods=['GET'])
def get_tokens():
    """获取代币列表，支持分页和筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'mention_count')
    order = request.args.get('order', 'desc')
    name = request.args.get('name')
    symbol = request.args.get('symbol')
    chain = request.args.get('chain')
    
    tokens, total = token_service.get_tokens(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        name=name,
        symbol=symbol,
        chain=chain
    )
    
    return jsonify({
        'success': True,
        'data': [token.to_dict() for token in tokens],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200

@api_bp.route('/tokens/<int:token_id>', methods=['GET'])
def get_token(token_id):
    """获取特定代币详情"""
    token = token_service.get_token_by_id(token_id)
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': token.to_dict(with_stats=True)
    }), 200

@api_bp.route('/tokens/trending', methods=['GET'])
def get_trending_tokens():
    """获取热门代币"""
    period = request.args.get('period', '24h')  # 24h, 7d, 30d
    limit = request.args.get('limit', 10, type=int)
    days = request.args.get('days', 7, type=int)
    
    # 根据请求参数选择不同的实现
    if 'days' in request.args:
        trending_tokens = trend_service.get_trending_tokens(limit=limit, days=days)
        return jsonify({
            'success': True,
            'data': trending_tokens
        })
    else:
        tokens = token_service.get_trending_tokens(period=period, limit=limit)
        return jsonify({
            'success': True,
            'data': [token.to_dict(with_stats=True) for token in tokens],
            'period': period
        }), 200

@api_bp.route('/tokens/address/<address>', methods=['GET'])
def get_token_by_address(address):
    """通过合约地址获取代币"""
    chain = request.args.get('chain')  # 可选参数，指定链
    
    token = token_service.get_token_by_address(address, chain)
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': token.to_dict(with_stats=True)
    }), 200

@api_bp.route('/tokens', methods=['POST'])
@jwt_required()
def create_token():
    """创建新代币"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    required_fields = ['name', 'symbol', 'address', 'chain']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    token_service = TokenService()
    
    # 检查代币是否已存在
    existing_token = token_service.get_token_by_address(data['address'], data['chain'])
    if existing_token:
        return jsonify({
            'success': False,
            'message': 'Token with this address already exists'
        }), 409
    
    try:
        token = token_service.create_token(
            name=data['name'],
            symbol=data['symbol'],
            address=data['address'],
            chain=data['chain'],
            description=data.get('description', ''),
            logo_url=data.get('logo_url'),
            website=data.get('website'),
            twitter=data.get('twitter'),
            telegram=data.get('telegram'),
            created_by=get_jwt_identity()
        )
        
        logger.info(f"Created new token: {data['name']} ({data['symbol']})")
        return jsonify({
            'success': True,
            'message': 'Token created successfully',
            'token': token.to_dict()
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@api_bp.route('/tokens/<int:token_id>', methods=['PUT'])
@jwt_required()
def update_token(token_id):
    """更新代币信息"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    token_service = TokenService()
    token = token_service.get_token_by_id(token_id)
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token not found'
        }), 404
    
    try:
        updated_token = token_service.update_token(
            token_id=token_id,
            name=data.get('name'),
            symbol=data.get('symbol'),
            description=data.get('description'),
            logo_url=data.get('logo_url'),
            website=data.get('website'),
            twitter=data.get('twitter'),
            telegram=data.get('telegram')
        )
        
        logger.info(f"Updated token: {token_id}")
        return jsonify({
            'success': True,
            'message': 'Token updated successfully',
            'token': updated_token.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@api_bp.route('/tokens/<int:token_id>/mentions', methods=['GET'])
def get_token_mentions(token_id):
    """获取代币的提及记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform')  # twitter, telegram, wechat, qq
    
    token_service = TokenService()
    token = token_service.get_token_by_id(token_id)
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token not found'
        }), 404
    
    mentions, total = token_service.get_token_mentions(
        token_id=token_id,
        page=page,
        per_page=per_page,
        start_date=start_date,
        end_date=end_date,
        platform=platform
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

@api_bp.route('/tokens/<int:token_id>/stats', methods=['GET'])
def get_token_stats(token_id):
    """获取代币的统计数据"""
    period = request.args.get('period', '7d')  # 24h, 7d, 30d, all
    interval = request.args.get('interval', 'day')  # hour, day, week
    
    token_service = TokenService()
    token = token_service.get_token_by_id(token_id)
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token not found'
        }), 404
    
    stats = token_service.get_token_stats(
        token_id=token_id,
        period=period,
        interval=interval
    )
    
    return jsonify({
        'success': True,
        'token': {
            'id': token.id,
            'name': token.name,
            'symbol': token.symbol
        },
        'stats': stats,
        'period': period,
        'interval': interval
    }), 200 