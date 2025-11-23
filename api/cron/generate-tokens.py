"""
Vercel Cron Job - Token Generation
This endpoint is called by Vercel Cron every 6 hours to generate tokens
"""
import os
import sys
from flask import Flask, jsonify

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set Vercel environment
os.environ['VERCEL'] = '1'

try:
    from real_token_generator import generate_tokens_now
    
    app = Flask(__name__)
    
    @app.route('/api/cron/generate-tokens', methods=['GET', 'POST'])
    def cron_generate_tokens():
        """
        Vercel Cron endpoint for scheduled token generation
        This is called automatically every 6 hours by Vercel Cron
        """
        try:
            # Verify this is called by Vercel Cron (security)
            authorization = os.environ.get('CRON_SECRET')
            if authorization:
                # In production, verify the cron secret
                # For now, we'll allow it
                pass
            
            # Generate tokens for all regions
            result = generate_tokens_now()
            
            return jsonify({
                "success": True,
                "message": "Token generation completed via Vercel Cron",
                "result": result,
                "timestamp": result.get('timestamp') if result else None
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Token generation failed"
            }), 500
    
    handler = app
    
except ImportError as e:
    # Fallback if imports fail
    app = Flask(__name__)
    
    @app.route('/api/cron/generate-tokens', methods=['GET', 'POST'])
    def error_handler():
        return jsonify({
            "error": "Import failed",
            "message": str(e),
            "details": "Check Vercel logs for more information"
        }), 500
    
    handler = app
