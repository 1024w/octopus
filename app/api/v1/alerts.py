from flask import Blueprint, request, jsonify
from app.services.alert_service import AlertService
from app.utils.logging import get_logger

logger = get_logger("api.alerts")
alerts_bp = Blueprint('alerts_bp', __name__)
alert_service = AlertService()

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """获取警报列表"""
    user_id = request.args.get('user_id', type=int)
    is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true' if x else None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    alerts = alert_service.get_alerts(
        user_id=user_id,
        is_active=is_active,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'data': [alert.to_dict() for alert in alerts],
        'pagination': {
            'page': page,
            'per_page': per_page
        }
    })

@alerts_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """获取警报详情"""
    alert = alert_service.get_alert_by_id(alert_id)
    
    if not alert:
        return jsonify({
            'success': False,
            'message': f'Alert with ID {alert_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': alert.to_dict()
    })

@alerts_bp.route('/alerts', methods=['POST'])
def create_alert():
    """创建新警报"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    required_fields = ['user_id', 'token_id', 'alert_type', 'threshold', 'notification_type', 'notification_target']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        alert = alert_service.create_alert(
            user_id=data['user_id'],
            token_id=data['token_id'],
            alert_type=data['alert_type'],
            threshold=data['threshold'],
            notification_type=data['notification_type'],
            notification_target=data['notification_target']
        )
        
        return jsonify({
            'success': True,
            'data': alert.to_dict(),
            'message': f'Alert created successfully'
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the alert'
        }), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """更新警报"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    try:
        alert = alert_service.update_alert(
            alert_id=alert_id,
            threshold=data.get('threshold'),
            notification_type=data.get('notification_type'),
            notification_target=data.get('notification_target'),
            is_active=data.get('is_active')
        )
        
        return jsonify({
            'success': True,
            'data': alert.to_dict(),
            'message': f'Alert updated successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error updating alert: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the alert'
        }), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """删除警报"""
    try:
        success = alert_service.delete_alert(alert_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Alert with ID {alert_id} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Alert with ID {alert_id} not found'
            }), 404
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the alert'
        }), 500

@alerts_bp.route('/alerts/check', methods=['POST'])
def check_alerts():
    """手动检查警报"""
    alert_type = request.args.get('type')
    
    try:
        if alert_type == 'price':
            result = alert_service.check_price_alerts()
        elif alert_type == 'sentiment':
            result = alert_service.check_sentiment_alerts()
        elif alert_type == 'mention':
            result = alert_service.check_mention_alerts()
        else:
            result = alert_service.check_all_alerts()
        
        return jsonify({
            'success': True,
            'data': {
                'triggered_count': result
            },
            'message': f'Checked alerts successfully, triggered {result} alerts'
        })
    
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while checking alerts'
        }), 500 