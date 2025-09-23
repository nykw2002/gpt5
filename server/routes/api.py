from flask import request, jsonify
from server.handlers.document_handler import get_status, load_document
from server.handlers.query_handler import process_query, process_query_stream

def register_api_routes(app, rag_system, system_status):
    @app.route('/api/status')
    def api_status():
        return get_status(rag_system, system_status)

    @app.route('/api/load-document', methods=['POST'])
    def api_load_document():
        data = request.get_json()
        document_path = data.get('document_path')
        return load_document(rag_system, system_status, document_path)

    @app.route('/api/query', methods=['POST'])
    def api_query():
        data = request.get_json()
        question = data.get('question')
        return process_query(rag_system, system_status, question)

    @app.route('/api/query-stream', methods=['POST'])
    def api_query_stream():
        data = request.get_json()
        question = data.get('question')
        return process_query_stream(rag_system, system_status, question)

    @app.route('/api/examples')
    def api_examples():
        examples = [
            {
                'text': 'How many complaints are from Israel?',
                'type': 'counting',
                'description': 'Count specific items in the data'
            },
            {
                'text': 'Analyze the distribution of complaints by country',
                'type': 'analysis',
                'description': 'Perform analytical review of data patterns'
            },
            {
                'text': 'Find all entries with QE- batch codes',
                'type': 'search',
                'description': 'Search for specific patterns or entries'
            },
            {
                'text': 'What are the most common complaint types?',
                'type': 'analysis',
                'description': 'Identify trends and common patterns'
            },
            {
                'text': 'List all substantiated complaints',
                'type': 'search',
                'description': 'Find entries matching specific criteria'
            }
        ]

        return jsonify({
            'success': True,
            'data': examples
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500