from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from datetime import datetime, timedelta

from app.api import api_bp
from app.services.user_service import UserService
from app.utils.logging import get_logger

logger = get_logger("api.users")
user_service = UserService()

# 用户注册和登录接口

@api_bp.route('/users/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        # 检查用户名和邮箱是否已存在
        if user_service.get_user_by_username(data['username']):
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400
        
        if user_service.get_user_by_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Email already exists'
            }), 400
        
        # 创建用户
        user = user_service.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user')
        )
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'message': 'User registered successfully'
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while registering the user'
        }), 500

@api_bp.route('/users/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # 检查用户名/邮箱和密码
    username_or_email = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not username_or_email or not password:
        return jsonify({
            'success': False,
            'message': 'Missing username/email or password'
        }), 400
    
    try:
        # 验证用户
        user = None
        if '@' in username_or_email:
            user = user_service.get_user_by_email(username_or_email)
        else:
            user = user_service.get_user_by_username(username_or_email)
        
        if not user or not user_service.verify_password(user.id, password):
            return jsonify({
                'success': False,
                'message': 'Invalid username/email or password'
            }), 401
        
        # 生成令牌
        expires = timedelta(hours=24)
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'username': user.username,
                'role': user.role
            },
            expires_delta=expires
        )
        
        # 更新最后登录时间
        user_service.update_last_login(user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'token': access_token,
                'expires_at': (datetime.utcnow() + expires).isoformat(),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            },
            'message': 'Login successful'
        })
    
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during login'
        }), 500

# 用户个人资料接口

@api_bp.route('/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户个人资料"""
    user_id = get_jwt_identity()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    })

@api_bp.route('/users/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户个人资料"""
    user_id = get_jwt_identity()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    try:
        # 更新用户信息
        updated_user = user_service.update_user(
            user_id=user_id,
            username=data.get('username'),
            email=data.get('email')
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': updated_user.id,
                'username': updated_user.username,
                'email': updated_user.email,
                'role': updated_user.role
            },
            'message': 'Profile updated successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the profile'
        }), 500

@api_bp.route('/users/change-password', methods=['POST'])
@jwt_required()
def change_user_password():
    """修改当前用户密码"""
    user_id = get_jwt_identity()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({
            'success': False,
            'message': 'Missing current password or new password'
        }), 400
    
    try:
        # 验证当前密码
        if not user_service.verify_password(user_id, current_password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 401
        
        # 更新密码
        success = user_service.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to change password'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while changing the password'
        }), 500

# 用户管理接口（管理员）

@api_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表，需要管理员权限"""
    user_id = get_jwt_identity()
    current_user = user_service.get_user_by_id(user_id)
    
    # 检查权限
    if not current_user or current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    try:
        users, total = user_service.get_users(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting users'
        }), 500

@api_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取特定用户信息，需要管理员权限或本人"""
    current_user_id = get_jwt_identity()
    current_user = user_service.get_user_by_id(current_user_id)
    
    # 检查权限
    if not current_user or (current_user.id != user_id and current_user.role != 'admin'):
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息，需要管理员权限或本人"""
    current_user_id = get_jwt_identity()
    current_user = user_service.get_user_by_id(current_user_id)
    
    # 检查权限
    if not current_user or (current_user.id != user_id and current_user.role != 'admin'):
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    try:
        # 仅管理员可以更改角色
        role = data.get('role')
        if role and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Only administrators can change user roles'
            }), 403
        
        updated_user = user_service.update_user(
            user_id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            role=role
        )
        
        logger.info(f"Updated user: {user_id}")
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': updated_user.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the user'
        }), 500

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户，需要管理员权限"""
    current_user_id = get_jwt_identity()
    current_user = user_service.get_user_by_id(current_user_id)
    
    # 检查权限
    if not current_user or current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # 防止删除自己
    if current_user.id == user_id:
        return jsonify({
            'success': False,
            'message': 'Cannot delete your own account'
        }), 400
    
    user_service.delete_user(user_id)
    
    logger.info(f"Deleted user: {user_id}")
    return jsonify({
        'success': True,
        'message': 'User deleted successfully'
    }), 200

@api_bp.route('/users/<int:user_id>/change-password', methods=['POST'])
@jwt_required()
def change_password(user_id):
    """修改指定用户密码，需要管理员权限或本人"""
    current_user_id = get_jwt_identity()
    current_user = user_service.get_user_by_id(current_user_id)
    
    # 检查权限
    if not current_user or (current_user.id != user_id and current_user.role != 'admin'):
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # 管理员可以直接设置新密码，不需要当前密码
    if current_user.role == 'admin' and current_user.id != user_id:
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({
                'success': False,
                'message': 'New password is required'
            }), 400
        
        try:
            user_service.set_password(user_id, new_password)
            
            logger.info(f"Admin changed password for user: {user_id}")
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            }), 200
        
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    else:
        # 用户修改自己的密码，需要当前密码
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current password and new password are required'
            }), 400
        
        try:
            success = user_service.change_password(
                user_id=user_id,
                current_password=current_password,
                new_password=new_password
            )
            
            if not success:
                return jsonify({
                    'success': False,
                    'message': 'Current password is incorrect'
                }), 400
            
            logger.info(f"Changed password for user: {user_id}")
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            }), 200
        
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred while changing the password'
            }), 500