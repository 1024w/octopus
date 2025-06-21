from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.services.collector_service import CollectorService
from app.utils.logging import get_logger

logger = get_logger("api.collectors")
collector_service = CollectorService()

@api_bp.route('/collectors', methods=['GET'])
@jwt_required()
def get_collectors():
    """获取所有数据采集器配置"""
    collector_type = request.args.get('type')
    is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true' if x else None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    collectors = collector_service.get_collectors(
        collector_type=collector_type,
        is_active=is_active,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'data': [collector.to_dict() for collector in collectors],
        'pagination': {
            'page': page,
            'per_page': per_page
        }
    }), 200

@api_bp.route('/collectors/<int:collector_id>', methods=['GET'])
@jwt_required()
def get_collector(collector_id):
    """获取特定数据采集器配置"""
    collector = collector_service.get_collector_by_id(collector_id)
    
    if not collector:
        return jsonify({
            'success': False,
            'message': 'Collector not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': collector.to_dict()
    }), 200

@api_bp.route('/collectors', methods=['POST'])
@jwt_required()
def create_collector():
    """创建新的数据采集器配置"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    required_fields = ['name', 'type', 'config']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        collector = collector_service.create_collector(
            name=data['name'],
            collector_type=data['type'],
            config=data['config'],
            description=data.get('description', ''),
            schedule=data.get('schedule', ''),
            is_active=data.get('is_active', True),
            created_by=get_jwt_identity()
        )
        
        logger.info(f"Created new collector: {data['name']} of type {data['type']}")
        return jsonify({
            'success': True,
            'data': collector.to_dict(),
            'message': 'Collector created successfully'
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error creating collector: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the collector'
        }), 500

@api_bp.route('/collectors/<int:collector_id>', methods=['PUT'])
@jwt_required()
def update_collector(collector_id):
    """更新数据采集器配置"""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    collector = collector_service.get_collector_by_id(collector_id)
    
    if not collector:
        return jsonify({
            'success': False,
            'message': 'Collector not found'
        }), 404
    
    try:
        updated_collector = collector_service.update_collector(
            collector_id=collector_id,
            name=data.get('name'),
            collector_type=data.get('type'),
            config=data.get('config'),
            description=data.get('description'),
            schedule=data.get('schedule'),
            is_active=data.get('is_active')
        )
        
        logger.info(f"Updated collector: {collector_id}")
        return jsonify({
            'success': True,
            'data': updated_collector.to_dict(),
            'message': 'Collector updated successfully'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error updating collector: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the collector'
        }), 500

@api_bp.route('/collectors/<int:collector_id>', methods=['DELETE'])
@jwt_required()
def delete_collector(collector_id):
    """删除数据采集器配置"""
    collector = collector_service.get_collector_by_id(collector_id)
    
    if not collector:
        return jsonify({
            'success': False,
            'message': 'Collector not found'
        }), 404
    
    try:
        success = collector_service.delete_collector(collector_id)
        
        if success:
            logger.info(f"Deleted collector: {collector_id}")
            return jsonify({
                'success': True,
                'message': f'Collector with ID {collector_id} deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Collector with ID {collector_id} not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error deleting collector: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the collector'
        }), 500

@api_bp.route('/collectors/<int:collector_id>/run', methods=['POST'])
@jwt_required()
def run_collector(collector_id):
    """手动运行数据采集器"""
    collector = collector_service.get_collector_by_id(collector_id)
    
    if not collector:
        return jsonify({
            'success': False,
            'message': 'Collector not found'
        }), 404
    
    try:
        task_id = collector_service.run_collector(collector_id)
        
        logger.info(f"Manually running collector: {collector_id}, task_id: {task_id}")
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id
            },
            'message': 'Collector started successfully'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error running collector {collector_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error running collector: {str(e)}'
        }), 500

@api_bp.route('/collectors/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """获取采集任务状态"""
    try:
        task_status = collector_service.get_task_status(task_id)
        
        return jsonify({
            'success': True,
            'data': task_status
        }), 200
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting task status'
        }), 500

@api_bp.route('/collectors/types', methods=['GET'])
@jwt_required()
def get_collector_types():
    """获取支持的收集器类型"""
    try:
        types = collector_service.get_supported_collector_types()
        
        return jsonify({
            'success': True,
            'data': types
        })
    
    except Exception as e:
        logger.error(f"Error getting collector types: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting collector types'
        }), 500 