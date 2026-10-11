import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from database import init_db
from views import api

def create_app():
    # Frontend directory path
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Frontend'))

    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fitfinder-nlp-secret-key-2026')
    app.config['JSON_SORT_KEYS'] = False

    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize Database Tables
    init_db()

    # Register API Blueprint
    app.register_blueprint(api, url_prefix='/api')

    # Frontend Route Handlers
    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        if os.path.exists(os.path.join(frontend_dir, filename)):
            return send_from_directory(frontend_dir, filename)
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/api/health/')
    def health_check():
        return jsonify({"status": "healthy", "service": "FitFinder API Engine"}), 200

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"FitFinder Server running on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
