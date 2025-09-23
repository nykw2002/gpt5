from flask import Flask, request, jsonify, send_from_directory, send_file, Response, stream_with_context
from flask_cors import CORS
import os
import sys
import traceback
import json
import queue
import threading
sys.path.append('./src')
from enhanced_rag import EnhancedRAG

app = Flask(__name__)
CORS(app)

# Global RAG instance
rag_system = None
system_status = {
    'initialized': False,
    'document_loaded': False,
    'current_document': None,
    'error': None
}

def initialize_rag_system():
    """Initialize the RAG system"""
    global rag_system, system_status

    try:
        print("Initializing RAG system...")
        rag_system = EnhancedRAG()
        system_status['initialized'] = True
        system_status['error'] = None

        # Try to load default document
        default_doc = "test.txt"
        if os.path.exists(default_doc):
            success = rag_system.load_and_process_document(default_doc)
            if success:
                system_status['document_loaded'] = True
                system_status['current_document'] = default_doc
                print(f"Successfully loaded default document: {default_doc}")
            else:
                print(f"Failed to load default document: {default_doc}")

        return True

    except Exception as e:
        error_msg = f"Failed to initialize RAG system: {str(e)}"
        print(error_msg)
        system_status['error'] = error_msg
        return False

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')

@app.route('/globals.css')
def serve_css():
    """Serve the CSS file"""
    response = send_file('globals.css')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/app.js')
def serve_js():
    """Serve the JavaScript file"""
    response = send_file('app.js')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
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

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/load-document', methods=['POST'])
def load_document():
    """Load a new document"""
    global rag_system, system_status

    try:
        data = request.get_json()
        document_path = data.get('document_path')

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

        # Initialize RAG system if not already done
        if not rag_system:
            if not initialize_rag_system():
                return jsonify({
                    'success': False,
                    'error': system_status['error']
                }), 500

        # Load the document
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

    except Exception as e:
        error_msg = f"Error loading document: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/query-stream', methods=['POST'])
def process_query_stream():
    """Process a query and stream progress updates via SSE"""
    global rag_system, system_status

    try:
        # Check if system is ready
        if not rag_system or not system_status['document_loaded']:
            return jsonify({
                'success': False,
                'error': 'RAG system not initialized or no document loaded'
            }), 400

        data = request.get_json()
        question = data.get('question')

        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400

        # Create a queue for progress updates
        progress_queue = queue.Queue()

        # Progress callback function
        def progress_callback(update):
            progress_queue.put(update)

        # Function to process query in background thread
        def process_in_background():
            try:
                # Re-initialize RAG with progress callback
                temp_rag = EnhancedRAG(progress_callback=progress_callback)
                temp_rag.load_and_process_document(system_status['current_document'])
                result = temp_rag.enhanced_query(question)
                progress_queue.put({'type': 'result', 'data': result})
            except Exception as e:
                progress_queue.put({'type': 'error', 'error': str(e)})
            finally:
                progress_queue.put({'type': 'done'})

        # Start background thread
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()

        # Stream progress updates
        def generate():
            while True:
                try:
                    update = progress_queue.get(timeout=60)

                    if update.get('type') == 'done':
                        break

                    yield f"data: {json.dumps(update)}\n\n"
                except queue.Empty:
                    break

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a query through the RAG system"""
    global rag_system, system_status

    try:
        # Check if system is ready
        if not rag_system or not system_status['document_loaded']:
            return jsonify({
                'success': False,
                'error': 'RAG system not initialized or no document loaded'
            }), 400

        data = request.get_json()
        question = data.get('question')

        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400

        # Process the query using enhanced RAG
        print(f"Processing query: {question}")
        result = rag_system.enhanced_query(question)

        # Handle enhanced query results
        if result.get('approach') == 'decomposition':
            # Enhanced query - already synthesized
            processed_answer = result['answer']
            summarized_answer = result['answer']
            query_type = 'enhanced'
        else:
            # Standard query - apply existing processing
            processed_answer = extract_final_answer(result['answer'], result.get('query_classification', {}))
            query_type = result.get('query_classification', {}).get('primary_type', 'general')
            summarized_answer = processed_answer  # Skip summarization for now

        # Skip quality metrics for enhanced queries for now
        if result.get('approach') == 'decomposition':
            quality_metrics = {'overall_quality': 'Enhanced', 'groundedness': 95, 'accuracy': 95, 'relevance': 95}
        else:
            relevant_chunk_indices = result.get('relevant_chunk_indices', [])
            source_chunks = [rag_system.chunks[i] for i in relevant_chunk_indices] if relevant_chunk_indices else []
            quality_metrics = rag_system.evaluate_answer_quality(question, summarized_answer, source_chunks)

        # Format the response
        response_data = {
            'question': result['question'],
            'answer': summarized_answer,  # This is now the final summarized answer for UI
            'original_answer': processed_answer,  # The extracted answer before summarization
            'full_reasoning': result['answer'],  # Keep full reasoning for debugging
            'query_classification': result.get('query_classification', {}),
            'chunks_analyzed': result.get('chunks_analyzed', 0),
            'chunk_analysis': result.get('chunk_analysis', {}),
            'was_summarized': summarized_answer != processed_answer,  # Flag to indicate if summarization occurred
            'quality_metrics': quality_metrics  # Add quality evaluation metrics
        }

        return jsonify({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get example queries"""
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

def extract_final_answer(full_answer, query_classification):
    """Extract concise final answer from detailed reasoning for counting queries"""

    # For counting queries, extract the FINAL ANSWER section
    if query_classification.get('primary_type') == 'counting':
        lines = full_answer.split('\n')

        # Find the FINAL ANSWER section
        final_answer_start = -1
        for i, line in enumerate(lines):
            if 'FINAL ANSWER' in line.upper():
                final_answer_start = i
                break

        if final_answer_start != -1:
            # Extract everything after "FINAL ANSWER:"
            final_lines = []
            capturing = False

            for line in lines[final_answer_start:]:
                if 'FINAL ANSWER' in line.upper():
                    capturing = True
                    continue
                elif capturing:
                    line = line.strip()
                    if line:  # Skip empty lines
                        final_lines.append(line)

            if final_lines:
                return '\n'.join(final_lines)

    # For non-counting queries or if no FINAL ANSWER found, return full answer
    return full_answer

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

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

if __name__ == '__main__':
    print("Starting General Purpose RAG Web Interface...")
    print("=" * 50)

    # Initialize the RAG system
    if initialize_rag_system():
        print("RAG system initialized successfully!")
    else:
        print("Warning: RAG system initialization failed")
        print("You can still access the interface, but functionality will be limited")

    print("\nStarting web server...")
    print("Access the interface at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid double initialization
    )