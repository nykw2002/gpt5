#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from server.app import create_app, initialize_rag_system

if __name__ == '__main__':
    print("Starting General Purpose RAG Web Interface (Modular Version)...")
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