import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['VERCEL'] = '1'

try:
    from main import app
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=5000, debug=False)
except ImportError as e:
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/<path:path>')
    def error_handler(path=''):
        return jsonify({
            "error": "Import failed",
            "message": str(e),
            "details": "Check dependencies and file structure",
            "status": "error"
        }), 500
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=5000, debug=False)

handler = app
