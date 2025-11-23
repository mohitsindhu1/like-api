import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Vercel environment flag BEFORE any imports
os.environ['VERCEL'] = '1'
os.environ['SERVERLESS'] = '1'

# Disable background schedulers for serverless
os.environ['DISABLE_TOKEN_GENERATOR'] = '1'
os.environ['DISABLE_DISCORD_LOGGER'] = '1'

# Import Flask for error handling
from flask import Flask, jsonify, request

# Create fallback app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "FreeFire API - Serverless Mode",
        "environment": "Vercel",
        "endpoints_available": [
            "/like?uid=XXX",
            "/send_requests?uid=XXX&count=50",
            "/bio (POST)",
            "/generate_token (POST)",
            "/info?uid=XXX",
            "/check_ban/XXX",
            "/records",
            "/rotation-stats",
            "/daily-usage-stats"
        ]
    })

@app.route('/health')
def health():
    """Simple health endpoint"""
    return jsonify({"status": "healthy", "mode": "serverless"})

# Try to import main app
try:
    # Patch real_token_generator to disable scheduler
    import real_token_generator
    
    # Disable automatic start
    original_start = real_token_generator.start_token_generation
    def disabled_start(*args, **kwargs):
        """Disabled for serverless"""
        pass
    real_token_generator.start_token_generation = disabled_start
    
    # Import discord logger and disable it
    try:
        import discord_logger
        discord_logger.DISCORD_WEBHOOK_ENABLED = False
    except:
        pass
    
    # Now import main app
    from main import app as main_app
    
    # Replace app with main app
    app = main_app
    
    # Add serverless indicator
    @app.before_request
    def add_serverless_header():
        """Add serverless mode indicator"""
        pass
    
except Exception as e:
    # If import fails, keep fallback app
    error_message = str(e)
    
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def error_handler(path=''):
        """Error handler for import failures"""
        return jsonify({
            "error": "Serverless initialization failed",
            "message": error_message,
            "path": path,
            "method": request.method,
            "help": "Check Vercel function logs for details",
            "status": "error"
        }), 500

# Export handler for Vercel
handler = app

# For local testing
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
