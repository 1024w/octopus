from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.api import api_bp
from app.services.auth_service import AuthService
from app.utils.logging import get_logger

logger = get_logger("api.auth")

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录API"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        }), 400
    
    auth_service = AuthService()
    user = auth_service.authenticate(username, password)
    
    if not user:
        logger.warning(f"Failed login attempt for user: {username}")
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    # 创建访问令牌
    access_token = create_access_token(identity=user.id)
    
    logger.info(f"User {username} logged in successfully")
    return jsonify({
        'success': True,
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    
    auth_service = AuthService()
    user = auth_service.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册API"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No input data provided'
        }), 400
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({
            'success': False,
            'message': 'Username, password and email are required'
        }), 400
    
    auth_service = AuthService()
    
    # 检查用户名是否已存在
    if auth_service.get_user_by_username(username):
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 409
    
    # 检查邮箱是否已存在
    if auth_service.get_user_by_email(email):
        return jsonify({
            'success': False,
            'message': 'Email already exists'
        }), 409
    
    # 创建新用户
    user = auth_service.create_user(username, password, email)
    
    logger.info(f"New user registered: {username}")
    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201 