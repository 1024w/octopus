from flask import Blueprint, request, jsonify
from app.processors.processor_factory import ProcessorFactory
from app.services.message_service import MessageService
from app.utils.logging import get_logger

logger = get_logger("api.processors")
processors_bp = Blueprint('processors_bp', __name__)
message_service = MessageService()

@processors_bp.route('/processors/types', methods=['GET'])
def get_processor_types():
    """获取支持的处理器类型"""
    try:
        types = ProcessorFactory.get_supported_types()
        
        return jsonify({
            'success': True,
            'data': types
        })
    
    except Exception as e:
        logger.error(f"Error getting processor types: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while getting processor types'
        }), 500

@processors_bp.route('/processors/message/process', methods=['POST'])
def process_message():
    """处理单条消息"""
    data = request.json
    
    if not data or 'message_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing required field: message_id'
        }), 400
    
    try:
        message_id = data['message_id']
        message = message_service.get_message_by_id(message_id)
        
        if not message:
            return jsonify({
                'success': False,
                'message': f'Message with ID {message_id} not found'
            }), 404
        
        processor = ProcessorFactory.create_processor('message')
        result = processor.process(message)
        
        return jsonify({
            'success': True,
            'data': {
                'message_id': message_id,
                'processed': result
            },
            'message': f'Message processed successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing the message'
        }), 500

@processors_bp.route('/processors/message/batch', methods=['POST'])
def process_messages_batch():
    """批量处理消息"""
    data = request.json
    
    if not data or 'message_ids' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing required field: message_ids'
        }), 400
    
    try:
        message_ids = data['message_ids']
        messages = message_service.get_messages_by_ids(message_ids)
        
        if not messages:
            return jsonify({
                'success': False,
                'message': 'No messages found with the provided IDs'
            }), 404
        
        processor = ProcessorFactory.create_processor('message')
        results = processor.batch_process(messages)
        
        return jsonify({
            'success': True,
            'data': {
                'processed_count': len(results),
                'total_count': len(message_ids)
            },
            'message': f'Processed {len(results)} out of {len(message_ids)} messages'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error batch processing messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while batch processing messages'
        }), 500

@processors_bp.route('/processors/message/unprocessed', methods=['POST'])
def process_unprocessed_messages():
    """处理未处理的消息"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        processor = ProcessorFactory.create_processor('message')
        processed_count = processor.process_unprocessed_messages(limit=limit)
        
        return jsonify({
            'success': True,
            'data': {
                'processed_count': processed_count
            },
            'message': f'Processed {processed_count} unprocessed messages'
        })
    
    except Exception as e:
        logger.error(f"Error processing unprocessed messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing unprocessed messages'
        }), 500

@processors_bp.route('/processors/message/collector/<int:collector_id>', methods=['POST'])
def process_collector_messages(collector_id):
    """处理特定收集器的消息"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        processor = ProcessorFactory.create_processor('message')
        processed_count = processor.process_collector_messages(collector_id=collector_id, limit=limit)
        
        return jsonify({
            'success': True,
            'data': {
                'processed_count': processed_count,
                'collector_id': collector_id
            },
            'message': f'Processed {processed_count} messages from collector {collector_id}'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Error processing collector messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing collector messages'
        }), 500 