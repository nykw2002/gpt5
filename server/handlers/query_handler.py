import json
import queue
import threading
from flask import jsonify, Response, stream_with_context
from server.utils.response import extract_final_answer

def process_query(rag_system, system_status, question):
    if not rag_system or not system_status['document_loaded']:
        return jsonify({
            'success': False,
            'error': 'RAG system not initialized or no document loaded'
        }), 400

    if not question:
        return jsonify({
            'success': False,
            'error': 'Question is required'
        }), 400

    print(f"Processing query: {question}")
    result = rag_system.enhanced_query(question)

    if result.get('approach') == 'decomposition':
        processed_answer = result['answer']
        summarized_answer = result['answer']
        query_type = 'enhanced'
    else:
        processed_answer = extract_final_answer(result['answer'], result.get('query_classification', {}))
        query_type = result.get('query_classification', {}).get('primary_type', 'general')
        summarized_answer = processed_answer

    quality_metrics = result.get('quality_metrics', {})

    response_data = {
        'question': result['question'],
        'answer': summarized_answer,
        'original_answer': processed_answer,
        'full_reasoning': result['answer'],
        'query_classification': result.get('query_classification', {}),
        'chunks_analyzed': result.get('chunks_analyzed', 0),
        'chunk_analysis': result.get('chunk_analysis', {}),
        'was_summarized': summarized_answer != processed_answer,
        'quality_metrics': quality_metrics
    }

    return jsonify({
        'success': True,
        'data': response_data
    })

def process_query_stream(rag_system, system_status, question):
    if not rag_system or not system_status['document_loaded']:
        return jsonify({
            'success': False,
            'error': 'RAG system not initialized or no document loaded'
        }), 400

    if not question:
        return jsonify({
            'success': False,
            'error': 'Question is required'
        }), 400

    progress_queue = queue.Queue()

    def progress_callback(update):
        progress_queue.put(update)

    def process_in_background():
        try:
            from enhanced.orchestrator import EnhancedRAG
            temp_rag = EnhancedRAG(progress_callback=progress_callback, use_decomposition=False)
            temp_rag.load_and_process_document(system_status['current_document'])
            result = temp_rag.enhanced_query(question)
            progress_queue.put({'type': 'result', 'data': result})
        except Exception as e:
            progress_queue.put({'type': 'error', 'error': str(e)})
        finally:
            progress_queue.put({'type': 'done'})

    thread = threading.Thread(target=process_in_background)
    thread.daemon = True
    thread.start()

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