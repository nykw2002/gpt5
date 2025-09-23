import os
from flask import send_file

def register_static_routes(app):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    @app.route('/')
    def index():
        return send_file(os.path.join(project_root, 'index.html'))

    @app.route('/globals.css')
    def serve_css():
        response = send_file(os.path.join(project_root, 'globals.css'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/app.js')
    def serve_js():
        response = send_file(os.path.join(project_root, 'app.js'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response