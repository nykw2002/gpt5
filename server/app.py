import os
import sys
from flask import Flask
from flask_cors import CORS

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from enhanced.orchestrator import EnhancedRAG

rag_system = None
system_status = {
    'initialized': False,
    'document_loaded': False,
    'current_document': None,
    'error': None
}

def initialize_rag_system():
    global rag_system, system_status

    try:
        print("Initializing RAG system...")
        rag_system = EnhancedRAG()
        system_status['initialized'] = True
        system_status['error'] = None

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

def create_app():
    app = Flask(__name__)
    CORS(app)

    from server.routes.static import register_static_routes
    from server.routes.api import register_api_routes

    register_static_routes(app)
    register_api_routes(app, rag_system, system_status)

    return app

if __name__ == '__main__':
    print("Starting General Purpose RAG Web Interface...")
    print("=" * 50)

    if initialize_rag_system():
        print("RAG system initialized successfully!")
    else:
        print("Warning: RAG system initialization failed")
        print("You can still access the interface, but functionality will be limited")

    print("\nStarting web server...")
    print("Access the interface at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )