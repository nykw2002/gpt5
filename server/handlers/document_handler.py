import os
from flask import jsonify
from server.utils.response import get_file_size

def load_document(rag_system, system_status, document_path):
    if not document_path:
        return jsonify({
            'success': False,
            'error': 'Document path is required'
        }), 400

    if not os.path.exists(document_path):
        return jsonify({
            'success': False,
            'error': f'Document not found: {document_path}'
        }), 404

    success = rag_system.load_and_process_document(document_path)

    if success:
        system_status['document_loaded'] = True
        system_status['current_document'] = document_path
        system_status['error'] = None

        return jsonify({
            'success': True,
            'data': {
                'document_path': document_path,
                'chunks_count': len(rag_system.chunks),
                'document_size': get_file_size(document_path)
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to load document'
        }), 500

def get_status(rag_system, system_status):
    response_data = {
        'system_ready': system_status['initialized'] and system_status['document_loaded'],
        'initialized': system_status['initialized'],
        'document_loaded': system_status['document_loaded'],
        'current_document': system_status['current_document'],
        'error': system_status['error']
    }

    if rag_system and system_status['document_loaded']:
        response_data.update({
            'chunks_count': len(rag_system.chunks),
            'document_size': get_file_size(system_status['current_document']) if system_status['current_document'] else 0
        })

    return jsonify({
        'success': True,
        'data': response_data
    })