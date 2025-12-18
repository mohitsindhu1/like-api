from flask import Flask, request, Response, render_template_string, jsonify
import asyncio
import json
import os
import requests
from datetime import datetime
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
from real_token_generator import real_token_generator, start_token_generation, stop_token_generation, get_generator_status, generate_tokens_now, generate_single_token
from nickname_processor import nickname_processor
from access_token_manager import access_token_manager
import visit_count_pb2
import aiohttp
import logging
from byte import Encrypt_ID, encrypt_api
import random
import jwt
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import my_pb2
import output_pb2

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure Flask to properly handle Unicode in JSON responses - ENHANCED
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
try:
    app.json.ensure_ascii = False
    app.json.sort_keys = False
except AttributeError:
    # Fallback for older Flask versions
    pass

# Custom JSON encoder to ensure proper Unicode display
import json
from flask.json.provider import DefaultJSONProvider

class UnicodeJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('separators', (',', ':'))
        return json.dumps(obj, **kwargs)

app.json = UnicodeJSONProvider(app)

# Load configuration from config.json
def load_config():
    """Load API configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Failed to load config.json: {e}")
        return {
            "api_urls": {
                "player_info": "http://raw.thug4ff.com/info?uid={uid}",
                "ban_check": "http://raw.thug4ff.com/check_ban/{uid}",
                "gen_profile": "http://profile.thug4ff.com/api/profile?uid={uid}"
            },
            "settings": {
                "request_timeout": 10,
                "max_retries": 3
            }
        }

# Load config at startup
config = load_config()

# Helper function to make API requests using config
def make_api_request(api_key, uid):
    """Make API request using config file"""
    try:
        api_url = config["api_urls"].get(api_key)
        if not api_url:
            return {
                "status": "error",
                "error": f"API key '{api_key}' not found in config"
            }, 404

        # Format URL with UID
        formatted_url = api_url.format(uid=uid)
        timeout = config["settings"].get("request_timeout", 10)

        app.logger.info(f"Making request to {api_key} API for UID: {uid}")

        response = requests.get(formatted_url, timeout=timeout)

        if response.status_code == 200:
            try:
                # Try to parse as JSON
                response_data = response.json()
                return {
                    "status": "success",
                    "uid": uid,
                    "data": response_data
                }, 200
            except json.JSONDecodeError:
                # If not JSON, return raw text
                return {
                    "status": "success",
                    "uid": uid,
                    "data": response.text
                }, 200
        else:
            return {
                "status": "error",
                "uid": uid,
                "error": f"API returned status code {response.status_code}",
                "message": response.text
            }, response.status_code

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "uid": uid,
            "error": "Request timeout - API took too long to respond"
        }, 408
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "uid": uid,
            "error": f"Request failed: {str(e)}"
        }, 500
    except Exception as e:
        return {
            "status": "error",
            "uid": uid,
            "error": str(e)
        }, 500

# Special function for image API requests
def make_image_api_request(api_key, uid):
    """Make API request for image responses using config file"""
    try:
        api_url = config["api_urls"].get(api_key)
        if not api_url:
            app.logger.error(f"API key '{api_key}' not found in config")
            return None, "API key not found in config", 404

        # Format URL with UID
        formatted_url = api_url.format(uid=uid)
        timeout = config["settings"].get("request_timeout", 30)  # Longer timeout for images

        app.logger.info(f"Making request to {api_key} API for UID: {uid}, URL: {formatted_url}")

        response = requests.get(formatted_url, timeout=timeout, stream=True)
        app.logger.info(f"Response received: status={response.status_code}, headers={dict(response.headers)}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'application/octet-stream')
            app.logger.info(f"Content type detected: {content_type}")

            # Get the response content
            content = response.content
            app.logger.info(f"Content received: {len(content)} bytes")

            # Check if it's an image
            if content_type.startswith('image/'):
                return content, content_type, 200
            else:
                # If not an image, try to handle as JSON/text
                try:
                    response_data = response.json()
                    return response_data, 'application/json', 200
                except json.JSONDecodeError:
                    return response.text, 'text/plain', 200
        else:
            error_msg = f"API returned status code {response.status_code}: {response.text[:200]}"
            app.logger.error(f"API error for UID {uid}: {error_msg}")
            return None, error_msg, response.status_code

    except requests.exceptions.Timeout as e:
        error_msg = "Request timeout - API took too long to respond"
        app.logger.error(f"Timeout error for UID {uid}: {str(e)}")
        return None, error_msg, 408
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        app.logger.error(f"Request error for UID {uid}: {error_msg}")
        return None, error_msg, 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        app.logger.error(f"Unexpected error for UID {uid}: {error_msg}")
        return None, error_msg, 500

# Custom jsonify function for proper Unicode display
def unicode_jsonify(data, status_code=200):
    """Custom jsonify that properly handles Unicode characters"""
    response_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    response = Response(
        response_data,
        status=status_code,
        mimetype='application/json; charset=utf-8'
    )
    return response

# Internal storage for player records
player_records = {}

def save_player_record(uid, nickname, server_name, likes_count):
    """Save player record to internal storage"""
    try:
        player_records[f"{uid}_{server_name}"] = {
            "uid": str(uid),
            "nickname": nickname,
            "server_name": server_name,
            "likes_count": likes_count,
            "last_updated": datetime.utcnow().isoformat()
        }
        app.logger.info(f"📝 Saved record: UID {uid}: {nickname}")
        return True
    except Exception as e:
        app.logger.error(f"❌ Storage error for UID {uid}: {e}")
        return False


@app.route("/records", methods=["GET"])
def get_records():
    """Get all player records from internal storage"""
    try:
        records_list = list(player_records.values())
        records_list.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        return unicode_jsonify({
            "total_records": len(records_list),
            "records": records_list[:100],
            "message": "Internal storage"
        })
    except Exception as e:
        app.logger.error(f"Storage query error: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


@app.route('/rotation-stats', methods=['GET'])
def get_rotation_stats():
    """Get smart token rotation statistics"""
    try:
        from smart_token_rotation import rotation_manager

        # Get stats for all servers
        servers = ["IND", "NX", "AG"]
        rotation_stats = {}

        for server in servers:
            stats = rotation_manager.get_rotation_stats(server)
            if "error" not in stats:
                rotation_stats[server] = stats

        return unicode_jsonify({
            "status": "success",
            "message": "Smart token rotation statistics",
            "rotation_stats": rotation_stats,
            "system_info": {
                "tokens_per_request": 110,
                "rotation_enabled": True,
                "equal_distribution": "All tokens are used equally before repeating"
            }
        })

    except Exception as e:
        app.logger.error(f"Error getting rotation stats: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


@app.route('/daily-usage-stats', methods=['GET'])
def get_daily_usage_stats():
    """Get daily token usage statistics"""
    try:
        from token_daily_limit import daily_limit_manager

        # Get stats for all servers
        servers = ["IND", "NX", "AG"]
        usage_stats = {}

        for server in servers:
            stats = daily_limit_manager.get_usage_stats(server)
            if "error" not in stats:
                usage_stats[server] = stats

        return unicode_jsonify({
            "status": "success",
            "message": "Daily token usage statistics",
            "daily_usage_stats": usage_stats,
            "system_info": {
                "daily_limit_per_token": 20,
                "automatic_reset": "Resets every day at midnight",
                "purpose": "Ensures each token is used maximum 20 times per day for fair distribution"
            }
        })

    except Exception as e:
        app.logger.error(f"Error getting daily usage stats: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


@app.route("/generate_token", methods=["POST", "GET"])
def manual_token_generation():
    """Manual token generation endpoint for testing"""
    if request.method == "GET":
        # Show simple form for testing
        return """
        <html>
        <head><title>Manual Token Generation</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Manual JWT Token Generation</h2>
            <form method="POST">
                <p><label>UID (10 digits):</label><br>
                <input type="text" name="uid" placeholder="4059499797" style="width: 200px; padding: 5px;"></p>

                <p><label>Password (64 char hex):</label><br> 
                <input type="text" name="password" placeholder="90692811391BDC1BCAB416B78DB4293300A797E38CA8A3FD4526E538FECFAC39" style="width: 500px; padding: 5px;"></p>

                <p><input type="submit" value="Generate Token" style="padding: 10px 20px; background: #007cba; color: white; border: none;"></p>
            </form>
        </body>
        </html>
        """

    # Handle POST request
    uid = request.form.get("uid") or request.json.get("uid") if request.is_json else None
    password = request.form.get("password") or request.json.get("password") if request.is_json else None

    if not uid or not password:
        return unicode_jsonify({"error": "UID and password are required"}, 400)

    try:
        app.logger.info(f"Manual token generation requested for UID: {uid}")
        token_result = generate_single_token(uid, password)

        if token_result:
            return unicode_jsonify({
                "success": True,
                "uid": uid,
                "token": token_result["token"],
                "message": "JWT token generated successfully"
            })
        else:
            return unicode_jsonify({
                "success": False,
                "uid": uid,
                "error": "Failed to generate token - check UID/password format and validity"
            }, 400)

    except Exception as e:
        app.logger.error(f"Manual token generation error: {str(e)}")
        return unicode_jsonify({
            "success": False,
            "error": f"Generation failed: {str(e)}"
        }, 500)

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from byte import Encrypt_ID, encrypt_api

# Headers function for friend requests (same as app.py)
def get_headers(token: str):
    """Generate headers for friend request API calls"""
    return {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB51",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

# Helper function for friend requests
def get_server_url_friend(server_name):
    """Get the appropriate server URL for friend requests"""
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/RequestAddingFriend"
    elif server_name == "NX":
        return "https://client.us.freefiremobile.com/RequestAddingFriend"
    elif server_name == "AG":
        return "https://clientbp.ggblueshark.com/RequestAddingFriend"
    else:
        return "https://client.ind.freefiremobile.com/RequestAddingFriend"

def send_friend_request_main(uid, token, results, results_lock, server_name="IND"):
    """Send friend request using main app's token system"""
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = get_server_url_friend(server_name)
    headers = get_headers(token)

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), verify=True, timeout=10)
        app.logger.info(f"Friend request response for UID {uid} on {server_name}: Status {response.status_code}")

        with results_lock:
            if response.status_code == 200:
                results["success"] += 1
                app.logger.info(f"SUCCESS: Friend request sent to UID {uid} on {server_name}")
            else:
                results["failed"] += 1
                app.logger.warning(f"FAILED: Friend request to UID {uid} on {server_name}, Status: {response.status_code}")
                if response.content:
                    app.logger.info(f"Response: {response.content[:100]}")
    except Exception as e:
        with results_lock:
            results["failed"] += 1
        app.logger.error(f"Request error for UID {uid} on {server_name}: {e}")

@app.route("/send_requests", methods=["GET"])
def send_requests():
    """Friend request endpoint using same token system as like functionality"""
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    count = request.args.get("count")

    if not uid:
        return unicode_jsonify({"error": "uid parameter is required"}, 400)

    # Auto-detect server if not provided (same logic as like system)
    if not server_name:
        app.logger.info(f"Auto-detecting server for UID {uid}")
        servers_to_try = ["IND", "NX", "AG"]
        for test_server in servers_to_try:
            with app.app_context():
                tokens = load_tokens(test_server)
                if tokens and len(tokens) > 0:
                    encrypted_uid = enc(uid)
                    if encrypted_uid:
                        result = make_request(encrypted_uid, test_server, tokens[0]["token"])
                        if result is not None:
                            server_name = test_server
                            app.logger.info(f"✓ Found UID {uid} on server {test_server}")
                            break

        if not server_name:
            return unicode_jsonify({"error": f"UID {uid} not found on any available server"}, 404)

    # Load tokens using same system as like functionality
    with app.app_context():
        tokens = load_tokens(server_name)
        if tokens is None or len(tokens) == 0:
            return unicode_jsonify({"error": f"No valid tokens found for server {server_name}"}, 500)

    total_available_tokens = len(tokens)
    
    # Handle count parameter - randomly select tokens if count is specified
    if count:
        try:
            count = int(count)
            if count <= 0:
                return unicode_jsonify({"error": "count must be a positive integer"}, 400)
            
            # Make sure count doesn't exceed available tokens
            if count > total_available_tokens:
                app.logger.warning(f"Requested count {count} exceeds available tokens {total_available_tokens}, using all available tokens")
                count = total_available_tokens
            
            # Randomly select 'count' number of tokens
            tokens = random.sample(tokens, count)
            app.logger.info(f"🎲 Randomly selected {len(tokens)} tokens from {total_available_tokens} available tokens")
        except ValueError:
            return unicode_jsonify({"error": "count must be a valid integer"}, 400)

    app.logger.info(f"🚀 Starting friend requests for UID {uid} on server {server_name} with {len(tokens)} tokens (Total available: {total_available_tokens})")

    # Try to get player name using same approach as like system
    player_name = f"Player_{uid}"
    try:
        for token_data in tokens[:3]:  # Try first 3 tokens
            token = token_data["token"]
            encrypted_uid = enc(uid)
            player_info = make_request(encrypted_uid, server_name, token)
            if player_info and hasattr(player_info, 'AccountInfo') and hasattr(player_info.AccountInfo, 'PlayerNickname'):
                player_name = player_info.AccountInfo.PlayerNickname
                break
    except Exception as e:
        app.logger.warning(f"Could not get player name for UID {uid}: {e}")

    # Send friend requests using selected tokens
    results = {"success": 0, "failed": 0}
    results_lock = threading.Lock()
    threads = []

    for token_data in tokens:
        token = token_data["token"]
        thread = threading.Thread(target=send_friend_request_main, args=(uid, token, results, results_lock, server_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_requests = results["success"] + results["failed"]
    status = 1 if results["success"] > 0 else 2

    return unicode_jsonify({
        "player_name": player_name,
        "server_name": server_name,
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "total_available_tokens": total_available_tokens,
        "tokens_used": len(tokens),
        "total_requests_sent": total_requests,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/like", methods=["GET"])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()

    # Allow auto-detection if server_name is not provided
    if not uid:
        return unicode_jsonify({"error": "UID is required"}, 400)

    # If no server specified, try to auto-detect the correct server
    if not server_name:
        app.logger.info(f"Auto-detecting server fy({
            "status": "success",
            "message": "Daily token usage statistics",
            "daily_usage_stats": usage_stats,
            "system_info": {
                "daily_limit_per_token": 20,
                "automatic_reset": "Resets every day at midnight",
                "purpose": "Ensures each token is used maximum 20 times per day for fair distribution"
            }
        })

    except Exception as e:
        app.logger.error(f"Error getting daily usage stats: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


@app.route("/generate_token", methods=["POST", "GET"])
def manual_token_generation():
    """Manual token generation endpoint for testing"""
    if request.method == "GET":
        # Show simple form for testing
        return """
        <html>
        <head><title>Manual Token Generation</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Manual JWT Token Generation</h2>
            <form method="POST">
                <p><label>UID (10 digits):</label><br>
                <input type="text" name="uid" placeholder="4059499797" style="width: 200px; padding: 5px;"></p>

                <p><label>Password (64 char hex):</label><br> 
                <input type="text" name="password" placeholder="90692811391BDC1BCAB416B78DB4293300A797E38CA8A3FD4526E538FECFAC39" style="width: 500px; padding: 5px;"></p>

                <p><input type="submit" value="Generate Token" style="padding: 10px 20px; background: #007cba; color: white; border: none;"></p>
            </form>
        </body>
        </html>
        """

    # Handle POST request
    uid = request.form.get("uid") or request.json.get("uid") if request.is_json else None
    password = request.form.get("password") or request.json.get("password") if request.is_json else None

    if not uid or not password:
        return unicode_jsonify({"error": "UID and password are required"}, 400)

    try:
        app.logger.info(f"Manual token generation requested for UID: {uid}")
        token_result = generate_single_token(uid, password)

        if token_result:
            return unicode_jsonify({
                "success": True,
                "uid": uid,
                "token": token_result["token"],
                "message": "JWT token generated successfully"
            })
        else:
            return unicode_jsonify({
                "success": False,
                "uid": uid,
                "error": "Failed to generate token - check UID/password format and validity"
            }, 400)

    except Exception as e:
        app.logger.error(f"Manual token generation error: {str(e)}")
        return unicode_jsonify({
            "success": False,
            "error": f"Generation failed: {str(e)}"
        }, 500)

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from byte import Encrypt_ID, encrypt_api

# Headers function for friend requests (same as app.py)
def get_headers(token: str):
    """Generate headers for friend request API calls"""
    return {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB51",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

# Helper function for friend requests
def get_server_url_friend(server_name):
    """Get the appropriate server URL for friend requests"""
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/RequestAddingFriend"
    elif server_name == "NX":
        return "https://client.us.freefiremobile.com/RequestAddingFriend"
    elif server_name == "AG":
        return "https://clientbp.ggblueshark.com/RequestAddingFriend"
    else:
        return "https://client.ind.freefiremobile.com/RequestAddingFriend"

def send_friend_request_main(uid, token, results, results_lock, server_name="IND"):
    """Send friend request using main app's token system"""
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = get_server_url_friend(server_name)
    headers = get_headers(token)

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), verify=True, timeout=10)
        app.logger.info(f"Friend request response for UID {uid} on {server_name}: Status {response.status_code}")

        with results_lock:
            if response.status_code == 200:
                results["success"] += 1
                app.logger.info(f"SUCCESS: Friend request sent to UID {uid} on {server_name}")
            else:
                results["failed"] += 1
                app.logger.warning(f"FAILED: Friend request to UID {uid} on {server_name}, Status: {response.status_code}")
                if response.content:
                    app.logger.info(f"Response: {response.content[:100]}")
    except Exception as e:
        with results_lock:
            results["failed"] += 1
        app.logger.error(f"Request error for UID {uid} on {server_name}: {e}")

@app.route("/send_requests", methods=["GET"])
def send_requests():
    """Friend request endpoint using same token system as like functionality"""
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    count = request.args.get("count")

    if not uid:
        return unicode_jsonify({"error": "uid parameter is required"}, 400)

    # Auto-detect server if not provided (same logic as like system)
    if not server_name:
        app.logger.info(f"Auto-detecting server for UID {uid}")
        servers_to_try = ["IND", "NX", "AG"]
        for test_server in servers_to_try:
            with app.app_context():
                tokens = load_tokens(test_server)
                if tokens and len(tokens) > 0:
                    encrypted_uid = enc(uid)
                    if encrypted_uid:
                        result = make_request(encrypted_uid, test_server, tokens[0]["token"])
                        if result is not None:
                            server_name = test_server
                            app.logger.info(f"✓ Found UID {uid} on server {test_server}")
                            break

        if not server_name:
            return unicode_jsonify({"error": f"UID {uid} not found on any available server"}, 404)

    # Load tokens using same system as like functionality
    with app.app_context():
        tokens = load_tokens(server_name)
        if tokens is None or len(tokens) == 0:
            return unicode_jsonify({"error": f"No valid tokens found for server {server_name}"}, 500)

    total_available_tokens = len(tokens)
    
    # Handle count parameter - randomly select tokens if count is specified
    if count:
        try:
            count = int(count)
            if count <= 0:
                return unicode_jsonify({"error": "count must be a positive integer"}, 400)
            
            # Make sure count doesn't exceed available tokens
            if count > total_available_tokens:
                app.logger.warning(f"Requested count {count} exceeds available tokens {total_available_tokens}, using all available tokens")
                count = total_available_tokens
            
            # Randomly select 'count' number of tokens
            tokens = random.sample(tokens, count)
            app.logger.info(f"🎲 Randomly selected {len(tokens)} tokens from {total_available_tokens} available tokens")
        except ValueError:
            return unicode_jsonify({"error": "count must be a valid integer"}, 400)

    app.logger.info(f"🚀 Starting friend requests for UID {uid} on server {server_name} with {len(tokens)} tokens (Total available: {total_available_tokens})")

    # Try to get player name using same approach as like system
    player_name = f"Player_{uid}"
    try:
        for token_data in tokens[:3]:  # Try first 3 tokens
            token = token_data["token"]
            encrypted_uid = enc(uid)
            player_info = make_request(encrypted_uid, server_name, token)
            if player_info and hasattr(player_info, 'AccountInfo') and hasattr(player_info.AccountInfo, 'PlayerNickname'):
                player_name = player_info.AccountInfo.PlayerNickname
                break
    except Exception as e:
        app.logger.warning(f"Could not get player name for UID {uid}: {e}")

    # Send friend requests using selected tokens
    results = {"success": 0, "failed": 0}
    results_lock = threading.Lock()
    threads = []

    for token_data in tokens:
        token = token_data["token"]
        thread = threading.Thread(target=send_friend_request_main, args=(uid, token, results, results_lock, server_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_requests = results["success"] + results["failed"]
    status = 1 if results["success"] > 0 else 2

    return unicode_jsonify({
        "player_name": player_name,
        "server_name": server_name,
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status,
        "total_available_tokens": total_available_tokens,
        "tokens_used": len(tokens),
        "total_requests_sent": total_requests,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/like", methods=["GET"])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()

    # Allow auto-detection if server_name is not provided
    if not uid:
        return unicode_jsonify({"error": "UID is required"}, 400)

    # If no server specified, try to auto-detect the correct server
    if not server_name:
        app.logger.info(f"Auto-detecting server for UID {uid}")
        # Try servers in order of likelihood
        servers_to_try = ["IND", "NX", "AG"]
        for test_server in servers_to_try:
            with app.app_context():
                tokens = load_tokens(test_server)
                if tokens and len(tokens) > 0:
                    encrypted_uid = enc(uid)
                    if encrypted_uid:
                        # Try with first token to test if UID exists on this server
                        result = make_request(encrypted_uid, test_server, tokens[0]["token"])
                        if result is not None:
                            server_name = test_server
                            app.logger.info(f"✓ Found UID {uid} on server {test_server}")
                            break

        if not server_name:
            return unicode_jsonify({"error": f"UID {uid} not found on any available server"}, 404)

    try:
        async def process_request_async():
            with app.app_context():
                tokens = load_tokens(server_name)
                if tokens is None or len(tokens) == 0:
                    raise Exception("Failed to load tokens.")

            # Try multiple tokens if first one fails - use ALL available tokens
            token_used = None
            before = None
            encrypted_uid = None
            total_available_tokens = len(tokens)
            
            app.logger.info(f"🎯 /like endpoint - Total tokens available: {total_available_tokens}")

            for i, token_data in enumerate(tokens):  # Use ALL available tokens
                token = token_data["token"]
                encrypted_uid = enc(uid)

                app.logger.info(f"Trying token {i+1}/{total_available_tokens} for UID {uid}")
                before = make_request(encrypted_uid, server_name, token)

                if before is not None:
                    token_used = token
                    app.logger.info(f"✅ Successfully got player info with token {i+1}/{total_available_tokens}")
                    break
                else:
                    app.logger.warning(f"Token {i+1}/{total_available_tokens} failed for UID {uid}")

            if before is None:
                raise Exception(f"Failed to retrieve initial player info with all {total_available_tokens} available tokens. Server: {server_name}, UID: {uid}")

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))

            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name == "NX":
                url = "https://client.us.freefiremobile.com/LikeProfile"
            elif server_name == "AG":
                url = "https://clientbp.ggblueshark.com/LikeProfile"
            else:
                url = "https://client.ind.freefiremobile.com/LikeProfile"

            # Send likes with improved rate limiting handling - ASYNC with TIMEOUT
            try:
                with app.app_context():
                    # Add timeout to prevent infinite loops - max 30 seconds
                    likes_sent = await asyncio.wait_for(
                        send_multiple_requests(uid, server_name, url), 
                        timeout=30
                    )
                app.logger.info(f"💫 Attempted to send likes for UID {uid}, successful requests: {likes_sent if likes_sent else 0}")
            except asyncio.TimeoutError:
                app.logger.warning(f"⏱️ Like sending timeout after 30 seconds for UID {uid}")
                likes_sent = 0

            # Use the same working token for final check
            after = make_request(encrypted_uid, server_name, token_used)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            player_level = int(data_after.get("AccountInfo", {}).get("level", 0))  # Fixed: lowercase 'level'
            release_version = data_after.get("AccountInfo", {}).get("ReleaseVersion", "OB51")

            # ADVANCED NICKNAME PROCESSING - Get raw data from protobuf
            try:
                # Extract raw nickname data directly from protobuf (before JSON conversion)
                raw_nickname_data = after.AccountInfo.PlayerNickname if hasattr(after.AccountInfo, 'PlayerNickname') else ""

                # Use advanced nickname processor for perfect Unicode handling
                player_name = nickname_processor.process_raw_nickname(raw_nickname_data, player_uid)

                # Get detailed debug info
                debug_info = nickname_processor.get_display_info(player_name)
                app.logger.info(f"🎮 UID {player_uid} | Raw: {repr(raw_nickname_data)} | Final: {repr(player_name)}")
                app.logger.info(f"📊 Nickname Info: Length={debug_info['length']}, Categories={debug_info['unicode_categories']}")

                # RECORD TO DATABASE FIRST (before response)
                save_success = save_player_record(
                    uid=player_uid,
                    nickname=player_name,
                    server_name=server_name,
                    likes_count=after_like
                )

                if save_success:
                    app.logger.info(f"💾 Database: Successfully recorded UID {player_uid} nickname: {player_name}")
                else:
                    app.logger.error(f"💾 Database: Failed to record UID {player_uid}")

            except Exception as e:
                app.logger.error(f"❌ Critical nickname processing error for UID {player_uid}: {e}")
                # Emergency fallback
                player_name = f"Player_{player_uid}"
            like_given = after_like - before_like

            # Improved status logic
            if like_given > 0:
                status = 1
            elif likes_sent and likes_sent > 0:
                status = 3  # Likes sent but not reflected (server processing delay)
            else:
                status = 2

            # Response format matching user specification
            response_data = {
                "Level": player_level,
                "LikesGivenByAPI": like_given,
                "LikesafterCommand": after_like,
                "LikesbeforeCommand": before_like,
                "PlayerNickname": player_name,
                "Region": server_name,
                "ReleaseVersion": release_version,
                "UID": player_uid,
                "status": status,
                "total_available_tokens": total_available_tokens,
                "token_used_for_validation": "Yes" if token_used else "No"
            }
            return response_data

        # Run async function in thread pool for Flask compatibility  
        def run_async():
            return asyncio.run(process_request_async())

        with ThreadPoolExecutor() as executor:
            result = executor.submit(run_async).result()

        return unicode_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


# Simple status endpoint (no web interface)
@app.route('/')
def status():
    """API Service Landing Page"""
    # Get token generation status
    try:
        gen_status = get_generator_status()
        next_generation = gen_status.get('next_run', 'Not scheduled')
    except:
        next_generation = 'Not available'

    return unicode_jsonify({
        "service": "Free Fire Token Generator API",
        "status": "running",
        "version": "2.0",
        "region_folders": ["IND", "AG", "NX", "BD", "PK"],
        "token_generation": f"Every 6 hours per region | Next: {str(next_generation)}",
        "api_endpoints": {
            "/access-jwt": {
                "description": "Convert access token to JWT token",
                "method": "GET",
                "params": {
                    "access_token": "required - Free Fire access token",
                    "region": "required - IND/AG/NX/BD/PK"
                },
                "response": "JWT token + account details + 8-hour expiration"
            },
            "/like": {
                "description": "Send likes to player using generated tokens",
                "method": "GET",
                "params": {
                    "uid": "required - Player UID",
                    "server_name": "optional - IND/AG/NX (auto-detect if not provided)"
                },
                "response": "Player info + likes sent status"
            },
            "/token": {
                "description": "Generate JWT token from UID & password (OAuth guest)",
                "method": "GET",
                "params": {
                    "uid": "required - Player UID",
                    "password": "required - Player password"
                },
                "response": "JWT token for OAuth guest authentication"
            },
            "/get-tokens": {
                "description": "View tokens from region-specific folders (data/tokens/)",
                "method": "GET",
                "params": {
                    "region": "optional - IND/AG/NX/BD/PK (all if not specified)"
                },
                "response": "Tokens grouped by region with account details + expiration"
            },
            "/webhook/receive": {
                "description": "Receive webhook notifications (token generated, etc.)",
                "method": "POST",
                "params": {
                    "event_type": "required - token_generated, token_used, etc.",
                    "region": "region code",
                    "account_name": "account name",
                    "uid": "user ID"
                },
                "response": "Webhook acknowledged + saved to data/webhooks/"
            },
            "/api/token-generator-status": {
                "description": "Check automatic token generator status",
                "method": "GET",
                "response": "Scheduler status + next generation time + region details"
            }
        }
    })

@app.route('/tokens')
def view_tokens():
    """View generated tokens from internal file storage"""
    try:
        from internal_storage import storage

        region = request.args.get("region", "").upper()
        tokens_data = {}

        # Get tokens from internal file storage
        if region == "IND" or not region:
            ind_stats = storage.get_token_stats("IND")
            ind_tokens = storage.load_tokens("IND")[:10]  # Get first 10 tokens
            tokens_data["india"] = {
                "total": ind_stats["total"],
                "generated_at": ind_stats["generated_at"],
                "tokens": [{"token": t.get("token", ""), "uid": t.get("uid", "")} for t in ind_tokens]
            }

        if region == "NX" or not region:
            nx_stats = storage.get_token_stats("NX")
            nx_tokens = storage.load_tokens("NX")[:10]  # Get first 10 tokens
            tokens_data["nx"] = {
                "total": nx_stats["total"],
                "generated_at": nx_stats["generated_at"],
                "tokens": [{"token": t.get("token", ""), "uid": t.get("uid", "")} for t in nx_tokens]
            }

        if region == "AG" or not region:
            ag_stats = storage.get_token_stats("AG")
            ag_tokens = storage.load_tokens("AG")[:10]  # Get first 10 tokens
            tokens_data["ag"] = {
                "total": ag_stats["total"],
                "generated_at": ag_stats["generated_at"],
                "tokens": [{"token": t.get("token", ""), "uid": t.get("uid", "")} for t in ag_tokens]
            }

        if tokens_data:
            total_ind = tokens_data.get('india', {}).get('total', 0)
            total_nx = tokens_data.get('nx', {}).get('total', 0)
            total_ag = tokens_data.get('ag', {}).get('total', 0)
            app.logger.info(f"✅ Retrieved tokens from internal storage: {total_ind} IND + {total_nx} NX + {total_ag} AG")
            return unicode_jsonify({
                "status": "success",
                "message": "Retrieved from internal file storage",
                "source": "internal_storage",
                "data": tokens_data
            })

        # No tokens found
        return unicode_jsonify({
            "status": "info",
            "message": "No tokens found in internal storage",
            "source": "internal_storage",
            "data": {"india": {"total": 0, "tokens": []}, "nx": {"total": 0, "tokens": []}, "ag": {"total": 0, "tokens": []}}
        })

    except Exception as e:
        return unicode_jsonify({"error": f"Failed to retrieve tokens: {str(e)}"}, 500)


@app.route('/api/token-generator-status')
def token_generator_status():
    """Check automatic token generator status"""
    try:
        from datetime import datetime
        import json
        
        # Get scheduler status
        status = get_generator_status()
        
        # Load last generation times
        last_gen_times = {}
        try:
            with open('data/last_generation.json', 'r') as f:
                last_gen_times = json.load(f)
        except:
            pass
        
        # Calculate time until next generation for each region
        current_time = datetime.utcnow()
        region_status = {}
        
        for region in ['IND', 'NX', 'AG']:
            if region in last_gen_times:
                last_gen = datetime.fromisoformat(last_gen_times[region])
                hours_passed = (current_time - last_gen).total_seconds() / 3600
                hours_remaining = max(0, 6 - hours_passed)
                
                region_status[region] = {
                    "last_generated": last_gen_times[region],
                    "hours_since_generation": round(hours_passed, 2),
                    "hours_until_next": round(hours_remaining, 2),
                    "needs_regeneration": hours_passed >= 6
                }
            else:
                region_status[region] = {
                    "last_generated": None,
                    "hours_since_generation": None,
                    "hours_until_next": 0,
                    "needs_regeneration": True
                }
        
        return unicode_jsonify({
            "status": "success",
            "scheduler": {
                "is_running": status["is_running"],
                "next_scheduled_run": status["next_run"],
                "active_jobs": status["jobs_count"],
                "check_interval": "Every 1 minute",
                "generation_interval": "Every 6 hours per region"
            },
            "regions": region_status,
            "current_time_utc": current_time.isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error getting token generator status: {e}")
        return unicode_jsonify({
            "status": "error",
            "error": str(e)
        }, 500)


@app.route('/get-tokens', methods=['GET'])
def get_tokens_from_folders():
    """Get all tokens from region-specific folders (data/tokens/{REGION}/generated_tokens.json)
    Optional: ?send_webhook=true to send tokens to webhook"""
    import os
    from datetime import datetime
    
    try:
        region = request.args.get('region', '').upper()
        send_webhook = request.args.get('send_webhook', 'false').lower() == 'true'
        regions = ['IND', 'AG', 'NX', 'BD', 'PK']
        
        # Filter regions if specific region requested
        if region and region in regions:
            regions = [region]
        elif region and region not in regions:
            return unicode_jsonify({"error": "Invalid region. Must be IND, AG, NX, BD, or PK"}, 400)
        
        all_tokens = {}
        total_available = 0
        
        for reg in regions:
            token_file = f"data/tokens/{reg}/generated_tokens.json"
            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        data = json.load(f)
                        # Filter expired tokens
                        now = datetime.utcnow()
                        valid_tokens = [t for t in data.get('tokens', []) 
                                      if datetime.fromisoformat(t.get('expires_at', '')) > now]
                        
                        # Show FULL token details
                        token_list = []
                        for t in valid_tokens:
                            token_list.append({
                                "token": t.get("token"),  # Full JWT token
                                "account_id": t.get("account_id"), 
                                "account_name": t.get("account_name"),
                                "uid": t.get("uid"),
                                "server": t.get("server"),
                                "generated_at": t.get("generated_at"),
                                "expires_at": t.get("expires_at")
                            })
                        
                        all_tokens[reg] = {
                            "total": len(valid_tokens),
                            "server_name": data.get('server_name'),
                            "generated_at": data.get('generated_at'),
                            "tokens": token_list
                        }
                        total_available += len(valid_tokens)
                except Exception as e:
                    app.logger.error(f"Error reading {reg} tokens: {e}")
                    all_tokens[reg] = {"total": 0, "tokens": [], "error": str(e)}
            else:
                all_tokens[reg] = {"total": 0, "tokens": []}
        
        response = {
            "status": "success",
            "source": "region_folders",
            "timestamp": datetime.utcnow().isoformat(),
            "total_available_tokens": total_available,
            "data": all_tokens
        }
        
        # Send webhook if requested
        if send_webhook:
            webhook_url = os.getenv('WEBHOOK_URL', '')
            if webhook_url:
                try:
                    webhook_data = {
                        "event_type": "tokens_fetched",
                        "timestamp": datetime.utcnow().isoformat(),
                        "total_available_tokens": total_available,
                        "regions_data": all_tokens
                    }
                    requests.post(webhook_url, json=webhook_data, timeout=5)
                    response["webhook_sent"] = True
                    response["webhook_url"] = webhook_url
                    app.logger.info(f"✅ Tokens sent to webhook: {webhook_url} ({total_available} tokens)")
                except Exception as e:
                    response["webhook_sent"] = False
                    response["webhook_error"] = str(e)
                    app.logger.error(f"Webhook send failed: {e}")
            else:
                response["webhook_sent"] = False
                response["webhook_note"] = "WEBHOOK_URL environment variable not set"
        
        return unicode_jsonify(response)
    
    except Exception as e:
        app.logger.error(f"Error getting tokens: {e}")
        return unicode_jsonify({"error": str(e), "status": "error"}, 500)


@app.route('/webhook/receive', methods=['POST'])
def webhook_receive():
    """Receive webhook data (token notifications, etc.)"""
    try:
        data = request.get_json()
        
        if not data:
            return unicode_jsonify({"status": "error", "message": "No data received"}, 400)
        
        # Log webhook received
        app.logger.info(f"📨 Webhook received: {data.get('event_type', 'unknown')} from {request.remote_addr}")
        
        # Store webhook data for debugging
        webhook_file = f"data/webhooks/received_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('data/webhooks', exist_ok=True)
        with open(webhook_file, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": request.remote_addr,
                "data": data
            }, f, indent=2)
        
        # Process webhook based on event type
        event_type = data.get('event_type')
        
        if event_type == 'token_generated':
            app.logger.info(f"✅ Token generated webhook: {data.get('region')} - {data.get('account_name')}")
        elif event_type == 'token_used':
            app.logger.info(f"📊 Token used webhook: {data.get('region')} - UID: {data.get('uid')}")
        
        return unicode_jsonify({
            "status": "success",
            "message": "Webhook received and processed",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        }, 200)
    
    except Exception as e:
        app.logger.error(f"Webhook receive error: {e}")
        return unicode_jsonify({"status": "error", "message": str(e)}, 500)


@app.route('/api/generate-tokens', methods=['GET', 'POST'])
def api_generate_tokens():
    """
    On-demand token generation endpoint
    This can be called manually or by Vercel Cron Jobs
    """
    try:
        app.logger.info("🔄 Starting on-demand token generation...")
        
        # Generate tokens for all regions
        result = generate_tokens_now()
        
        if result:
            return unicode_jsonify({
                "success": True,
                "message": "Token generation completed successfully",
                "result": result,
                "timestamp": result.get('timestamp') if isinstance(result, dict) else None
            })
        else:
            return unicode_jsonify({
                "success": False,
                "message": "Token generation failed or returned empty result",
                "error": "No result returned from generation process"
            }, 500)
            
    except Exception as e:
        app.logger.error(f"Token generation error: {e}")
        return unicode_jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate tokens"
        }, 500)


@app.route('/info', methods=['GET'])
def get_player_info():
    """Get player info using tokens (no API key required)"""
    uid = request.args.get('uid')
    server_name = request.args.get('server_name', '').upper()
    
    if not uid:
        return unicode_jsonify({"error": "UID parameter is required"}, 400)
    
    try:
        # If no server specified, auto-detect
        if not server_name:
            servers_to_try = ["IND", "NX", "AG"]
            for test_server in servers_to_try:
                with app.app_context():
                    tokens = load_tokens(test_server)
                    if tokens and len(tokens) > 0:
                        encrypted_uid = enc(uid)
                        if encrypted_uid:
                            result = make_request(encrypted_uid, test_server, tokens[0]["token"])
                            if result is not None:
                                server_name = test_server
                                break
            
            if not server_name:
                return unicode_jsonify({"success": False, "error": f"UID {uid} not found on any server"}, 404)
        
        # Get player info
        with app.app_context():
            tokens = load_tokens(server_name)
            if not tokens or len(tokens) == 0:
                return unicode_jsonify({"error": f"No tokens available for {server_name}"}, 500)
            
            encrypted_uid = enc(uid)
            if not encrypted_uid:
                return unicode_jsonify({"error": "Failed to encrypt UID"}, 500)
            
            # Try tokens until one works
            player_info = None
            for token_data in tokens:
                player_info = make_request(encrypted_uid, server_name, token_data["token"])
                if player_info:
                    break
            
            if not player_info:
                return unicode_jsonify({"success": False, "error": f"UID {uid} not found"}, 404)
            
            data = json.loads(MessageToJson(player_info))
            account_info = data.get("AccountInfo", {})
            
            return unicode_jsonify({
                "success": True,
                "uid": uid,
                "server": server_name,
                "player_nickname": account_info.get("PlayerNickname", "Unknown"),
                "likes": account_info.get("Likes", 0),
                "level": account_info.get("level", 0),
                "release_version": account_info.get("ReleaseVersion", ""),
                "data": account_info
            })
    
    except Exception as e:
        app.logger.error(f"Error getting player info: {e}")
        return unicode_jsonify({"success": False, "error": str(e)}, 500)


@app.route('/check-uid', methods=['GET'])
@app.route('/check_uid', methods=['GET'])
def check_uid_all_regions():
    """Check UID across all regions (no API key required)"""
    uid = request.args.get('uid')
    
    if not uid:
        return unicode_jsonify({"error": "UID parameter is required"}, 400)
    
    try:
        regions_to_check = ["IND", "NX", "AG", "BD", "PK"]
        found_regions = []
        regions_data = {}
        
        with app.app_context():
            for region in regions_to_check:
                try:
                    tokens = load_tokens(region)
                    if not tokens or len(tokens) == 0:
                        regions_data[region] = {"found": False, "error": "No tokens available for this region"}
                        continue
                    
                    encrypted_uid = enc(uid)
                    if not encrypted_uid:
                        regions_data[region] = {"found": False, "error": "Failed to encrypt UID"}
                        continue
                    
                    # Try tokens until one works
                    player_info = None
                    for token_data in tokens:
                        player_info = make_request(encrypted_uid, region, token_data["token"])
                        if player_info:
                            break
                    
                    if player_info:
                        data = json.loads(MessageToJson(player_info))
                        account_info = data.get("AccountInfo", {})
                        found_regions.append(region)
                        regions_data[region] = {
                            "found": True,
                            "player_nickname": account_info.get("PlayerNickname", "Unknown"),
                            "likes": account_info.get("Likes", 0),
                            "level": account_info.get("level", 0),
                            "uid": uid
                        }
                    else:
                        regions_data[region] = {"found": False, "error": "Player not found in this region"}
                
                except Exception as e:
                    regions_data[region] = {"found": False, "error": str(e)}
        
        return unicode_jsonify({
            "success": True if found_regions else False,
            "uid": uid,
            "found_in_regions": found_regions,
            "total_regions_found": len(found_regions),
            "regions_data": regions_data
        })
    
    except Exception as e:
        app.logger.error(f"Error checking UID: {e}")
        return unicode_jsonify({"success": False, "error": str(e)}, 500)


@app.route('/check_ban', methods=['GET'])
@app.route('/check_ban/<uid>', methods=['GET'])
def check_player_ban(uid=None):
    """Check if player is banned using external API from config"""
    if uid is None:
        uid = request.args.get('uid')

    if not uid:
        return unicode_jsonify({"error": "UID parameter is required"}, 400)

    response_data, status_code = make_api_request('ban_check', uid)
    return unicode_jsonify(response_data, status_code)


@app.route('/genpro', methods=['GET'])
@app.route('/genpro/<uid>', methods=['GET'])
def get_gen_profile(uid=None):
    """Get generated profile from external API using config (handles images)"""
    if uid is None:
        uid = request.args.get('uid')

    if not uid:
        return unicode_jsonify({"error": "UID parameter is required"}, 400)

    try:
        # Use image-specific API request handler
        content, content_type, status_code = make_image_api_request('gen_profile', uid)

        app.logger.info(f"Gen profile API response for UID {uid}: status_code={status_code}, content_type={content_type}, content_size={len(content) if isinstance(content, (bytes, str)) else 'N/A'}")

        if status_code != 200:
            app.logger.error(f"Gen profile API error for UID {uid}: {content}")
            return unicode_jsonify({
                "status": "error",
                "uid": uid,
                "error": str(content) if content else "Unknown error occurred"
            }, status_code)

        # If it's an image, return the image directly
        if isinstance(content, bytes) and content_type and content_type.startswith('image/'):
            app.logger.info(f"Returning image for UID {uid}: {len(content)} bytes, type: {content_type}")
            response = Response(content, mimetype=content_type)
            response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            response.headers['Content-Length'] = len(content)
            return response

        # If it's JSON/text data, return as JSON
        else:
            return unicode_jsonify({
                "status": "success",
                "uid": uid,
                "data": content,
                "content_type": content_type
            })

    except Exception as e:
        app.logger.error(f"Unexpected error in gen profile endpoint for UID {uid}: {str(e)}")
        return unicode_jsonify({
            "status": "error",
            "uid": uid,
            "error": f"Server error: {str(e)}"
        }, 500)


# ===== BIO & JWT ENDPOINTS =====

@app.route('/bio', methods=['GET', 'POST'])
def update_bio():
    """
    Update player bio using UID, password and custom bio text

    Parameters:
        uid: Player UID
        password: Account password
        bio: Custom bio text to set

    Example:
        GET /bio?uid=1234567890&password=abc123&bio=Pro%20Gamer
    """
    from bio_jwt_helper import update_bio_endpoint
    from concurrent.futures import ThreadPoolExecutor

    # Get parameters from both GET and POST
    if request.method == 'POST':
        data = request.get_json() or {}
        uid = data.get('uid') or request.args.get('uid')
        password = data.get('password') or request.args.get('password')
        custom_bio = data.get('bio') or request.args.get('bio')
    else:
        uid = request.args.get('uid')
        password = request.args.get('password')
        custom_bio = request.args.get('bio')

    # Validate parameters
    if not uid:
        return unicode_jsonify({"success": False, "error": "UID parameter is required"}, 400)
    if not password:
        return unicode_jsonify({"success": False, "error": "Password parameter is required"}, 400)
    if not custom_bio:
        return unicode_jsonify({"success": False, "error": "Bio parameter is required"}, 400)

    try:
        # Run async function in thread pool
        def run_async():
            return asyncio.run(update_bio_endpoint(uid, password, custom_bio))

        with ThreadPoolExecutor() as executor:
            result = executor.submit(run_async).result()

        status_code = 200 if result.get('success') else 400
        return unicode_jsonify(result, status_code)

    except Exception as e:
        app.logger.error(f"Bio update error: {e}")
        return unicode_jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, 500)


@app.route('/token', methods=['GET', 'POST'])
def generate_jwt_token():
    """
    Generate JWT token from UID and password

    Parameters:
        uid: Player UID
        password: Account password

    Example:
        GET /token?uid=1234567890&password=abc123def456
    """
    from bio_jwt_helper import create_jwt_from_uid_password
    from concurrent.futures import ThreadPoolExecutor

    # Get parameters from both GET and POST
    if request.method == 'POST':
        data = request.get_json() or {}
        uid = data.get('uid') or request.args.get('uid')
        password = data.get('password') or request.args.get('password')
    else:
        uid = request.args.get('uid')
        password = request.args.get('password')

    # Validate parameters
    if not uid:
        return unicode_jsonify({"success": False, "error": "UID parameter is required"}, 400)
    if not password:
        return unicode_jsonify({"success": False, "error": "Password parameter is required"}, 400)

    try:
        # Run async function in thread pool
        def run_async():
            return asyncio.run(create_jwt_from_uid_password(uid, password))

        with ThreadPoolExecutor() as executor:
            jwt_token, region, server_url = executor.submit(run_async).result()

        if jwt_token:
            return unicode_jsonify({
                "success": True,
                "jwt_token": jwt_token,
                "region": region,
                "server_url": server_url,
                "uid": uid
            })
        else:
            return unicode_jsonify({
                "success": False,
                "error": "Failed to generate JWT token",
                "message": "Please check your UID and password"
            }, 400)

    except Exception as e:
        app.logger.error(f"JWT generation error: {e}")
        return unicode_jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, 500)


@app.route('/accesstok', methods=['GET', 'POST'])
def generate_jwt_from_access_token():
    """
    Generate JWT token from access_token and open_id

    Parameters:
        access_token: Access token obtained from Garena OAuth
        open_id: Open ID from Garena OAuth (optional - will be extracted if not provided)

    Example:
        GET /accesstok?access_token=your_access_token&open_id=your_open_id
    """
    from bio_jwt_helper import create_jwt_from_access_token
    from concurrent.futures import ThreadPoolExecutor

    # Get parameters from both GET and POST
    if request.method == 'POST':
        data = request.get_json() or {}
        access_token = data.get('access_token') or request.args.get('access_token')
        open_id = data.get('open_id') or request.args.get('open_id')
    else:
        access_token = request.args.get('access_token')
        open_id = request.args.get('open_id')

    # Validate parameters
    if not access_token:
        return unicode_jsonify({
            "success": False,
            "error": "access_token parameter is required"
        }, 400)

    # If open_id not provided, try to extract from access token or use a default
    if not open_id:
        # For some cases, open_id might be embedded in the access token
        # For now, we'll require it to be provided
        return unicode_jsonify({
            "success": False,
            "error": "open_id parameter is required along with access_token"
        }, 400)

    try:
        # Run async function in thread pool
        def run_async():
            return asyncio.run(create_jwt_from_access_token(access_token, open_id))

        with ThreadPoolExecutor() as executor:
            jwt_token, region, server_url = executor.submit(run_async).result()

        if jwt_token:
            return unicode_jsonify({
                "success": True,
                "jwt_token": jwt_token,
                "region": region,
                "server_url": server_url
            })
        else:
            return unicode_jsonify({
                "success": False,
                "error": "Failed to generate JWT token from access_token",
                "message": "Please check your access_token and open_id"
            }, 400)

    except Exception as e:
        app.logger.error(f"JWT from access_token error: {e}")
        return unicode_jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, 500)


@app.route('/experimental-jwt', methods=['GET', 'POST'])
def experimental_jwt_generation():
    """
    🧪 EXPERIMENTAL: Generate JWT without open_id (Testing Different Approaches)
    
    This endpoint tries multiple experimental methods to generate JWT using only access_token.
    ⚠️ Success rate is very low - open_id is required by the API
    
    Parameters:
        access_token: Access token from OAuth (required)
        uid: User UID (optional, helps in approach 2)
    
    Example:
        GET /experimental-jwt?access_token=YOUR_TOKEN&uid=123456789
    """
    from experimental_jwt import test_all_approaches
    from concurrent.futures import ThreadPoolExecutor
    
    if request.method == 'POST':
        data = request.get_json() or {}
        access_token = data.get('access_token') or request.args.get('access_token')
        uid = data.get('uid') or request.args.get('uid')
    else:
        access_token = request.args.get('access_token')
        uid = request.args.get('uid')
    
    if not access_token:
        return unicode_jsonify({
            "success": False,
            "error": "access_token parameter is required",
            "note": "⚠️ This is experimental - success rate is very low"
        }), 400
    
    try:
        def run_async():
            return asyncio.run(test_all_approaches(access_token, uid))
        
        with ThreadPoolExecutor() as executor:
            jwt_token = executor.submit(run_async).result()
        
        if jwt_token:
            return unicode_jsonify({
                "success": True,
                "jwt_token": jwt_token,
                "message": "✅ Experimental approach succeeded!",
                "note": "This is rare - usually open_id is required"
            })
        else:
            return unicode_jsonify({
                "success": False,
                "error": "All experimental approaches failed",
                "message": "❌ open_id is required for JWT generation",
                "recommendation": "Use /accesstok with both access_token and open_id"
            }), 400
    
    except Exception as e:
        app.logger.error(f"Experimental JWT error: {e}")
        return unicode_jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


# ========== VISIT PROFILE ENDPOINT ==========

def load_visit_tokens(server_name):
    """Load tokens from OLD path: data/tokens/{old_filename}.json"""
    try:
        server_map = {
            "IND": "ind_tokens.json",
            "AG": "ag_tokens.json",
            "NX": "nx_tokens.json",
            "BD": "bd_tokens.json",
            "PK": "pk_tokens.json"
        }
        
        token_file = server_map.get(server_name.upper(), "ind_tokens.json")
        file_path = f"data/tokens/{token_file}"
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "tokens" in data:
            tokens = [item["token"] for item in data["tokens"] if "token" in item and item["token"]]
        elif isinstance(data, list):
            tokens = [item["token"] for item in data if "token" in item and item["token"]]
        else:
            tokens = []
            
        app.logger.info(f"✓ Loaded {len(tokens)} tokens for {server_name} server from {file_path}")
        return tokens
    except Exception as e:
        app.logger.error(f"❌ Error loading tokens for {server_name}: {e}")
        return []

def get_visit_url(server_name):
    """Get server URL for visit profile based on server name"""
    urls = {
        "IND": "https://client.ind.freefiremobile.com/GetPlayerPersonalShow",
        "AG": "https://clientbp.ggblueshark.com/GetPlayerPersonalShow",
        "NX": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "BD": "https://clientbp.ggblueshark.com/GetPlayerPersonalShow",
        "PK": "https://clientbp.ggblueshark.com/GetPlayerPersonalShow",
        "BR": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "US": "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    }
    return urls.get(server_name.upper(), "https://client.ind.freefiremobile.com/GetPlayerPersonalShow")

def parse_visit_protobuf_response(response_data):
    """Parse protobuf response to extract player data"""
    try:
        info = visit_count_pb2.Info()
        info.ParseFromString(response_data)
        
        player_data = {
            "uid": info.AccountInfo.UID if info.AccountInfo.UID else 0,
            "nickname": info.AccountInfo.PlayerNickname if info.AccountInfo.PlayerNickname else "",
            "likes": info.AccountInfo.Likes if info.AccountInfo.Likes else 0,
            "region": info.AccountInfo.PlayerRegion if info.AccountInfo.PlayerRegion else "",
            "level": info.AccountInfo.Levels if info.AccountInfo.Levels else 0
        }
        return player_data
    except Exception as e:
        app.logger.error(f"❌ Protobuf parsing error: {e}")
        return None

async def send_single_visit(session, url, token, uid, data):
    """Send a single visit request"""
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB51"
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.post(url, headers=headers, data=data, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                response_data = await resp.read()
                return True, response_data, None
            else:
                error_text = await resp.text()
                return False, None, f"HTTP {resp.status}: {error_text[:100]}"
    except asyncio.TimeoutError:
        return False, None, "Timeout"
    except Exception as e:
        return False, None, str(e)[:100]

async def send_visits_async(tokens, uid, server_name, target_success=1000):
    """Send visits asynchronously until target is reached"""
    url = get_visit_url(server_name)
    connector = aiohttp.TCPConnector(limit=100, ssl=False)
    total_success = 0
    total_sent = 0
    first_success_response = None
    player_info = None
    max_attempts = target_success * 3
    error_samples = []

    async with aiohttp.ClientSession(connector=connector) as session:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        data = bytes.fromhex(encrypted)

        while total_success < target_success and total_sent < max_attempts and len(tokens) > 0:
            batch_size = min(target_success - total_success, 100)
            tasks = [
                asyncio.create_task(send_single_visit(session, url, tokens[(total_sent + i) % len(tokens)], uid, data))
                for i in range(batch_size)
            ]
            results = await asyncio.gather(*tasks)
            
            if first_success_response is None:
                for success, response, error in results:
                    if success and response is not None:
                        first_success_response = response
                        player_info = parse_visit_protobuf_response(response)
                        break
                    elif error and len(error_samples) < 3:
                        error_samples.append(error)
            
            batch_success = sum(1 for r, _, _ in results if r)
            total_success += batch_success
            total_sent += batch_size

            if batch_success > 0:
                app.logger.info(f"Batch sent: {batch_size}, Success: {batch_success}, Total: {total_success}/{target_success}")
            
            if batch_success == 0 and total_sent >= 100:
                app.logger.warning(f"No successful visits after {total_sent} attempts, stopping")
                if error_samples:
                    app.logger.error(f"Sample errors: {error_samples[:3]}")
                break

    return total_success, total_sent, player_info, error_samples

@app.route('/visit/<string:server>/<int:uid>', methods=['GET'])
def visit_profile(server, uid):
    """
    Send profile visits to a Free Fire account using ALL available tokens
    Usage: GET /visit/{SERVER}/{UID}
    Example: GET /visit/IND/123456789
    Supported servers: IND, AG, NX, BD, PK
    """
    server = server.upper()
    
    tokens = load_visit_tokens(server)
    
    if not tokens:
        return unicode_jsonify({
            "error": f"❌ No valid tokens found for {server} server",
            "server": server,
            "uid": uid
        }), 500

    # Use ALL available tokens - no count parameter needed!
    target_success = len(tokens)
    
    app.logger.info(f"🚀 Sending visits to UID {uid} on {server} server using ALL {len(tokens)} tokens")

    total_success, total_sent, player_info, error_samples = asyncio.run(send_visits_async(
        tokens, uid, server, target_success=target_success
    ))

    if total_success > 0:
        response = {
            "success": True,
            "server": server,
            "uid": player_info.get("uid", uid) if player_info else uid,
            "nickname": player_info.get("nickname", "") if player_info else "",
            "region": player_info.get("region", "") if player_info else "",
            "level": player_info.get("level", 0) if player_info else 0,
            "likes": player_info.get("likes", 0) if player_info else 0,
            "visits_sent": total_success,
            "visits_failed": target_success - total_success,
            "total_attempts": total_sent,
            "tokens_used": len(tokens)
        }
        if not player_info:
            response["warning"] = "Visits sent but could not decode player information"
        return unicode_jsonify(response), 200
    else:
        error_msg = "No visits sent successfully"
        if error_samples:
            error_msg += f". Sample errors: {', '.join(error_samples[:2])}"
        
        return unicode_jsonify({
            "success": False,
            "error": error_msg,
            "server": server,
            "uid": uid,
            "visits_sent": 0,
            "visits_failed": total_sent,
            "error_details": error_samples[:3] if error_samples else []
        }), 500


AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

def encrypt_message(plaintext):
    """Encrypt message using AES-CBC"""
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)

def fetch_open_id(access_token):
    try:
        uid_url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        uid_headers = {
            "authority": "prod-api.reward.ff.garena.com",
            "method": "GET",
            "path": "/redemption/api/auth/inspect_token/",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        uid_res = requests.get(uid_url, headers=uid_headers, verify=False)
        uid_data = uid_res.json()
        uid = uid_data.get("uid")

        if not uid:
            return None, "Failed to extract UID"

        openid_url = "https://shop2game.com/api/auth/player_id_login"
        openid_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ar-MA,ar;q=0.9,en-US;q=0.8,en;q=0.7,ar-AE;q=0.6,fr-FR;q=0.5,fr;q=0.4",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Cookie": "source=mb; region=MA; mspid2=ca21e6ccc341648eea845c7f94b92a3c; language=ar; _ga=GA1.1.1955196983.1741710601; datadome=WY~zod4Q8I3~v~GnMd68u1t1ralV5xERfftUC78yUftDKZ3jIcyy1dtl6kdWx9QvK9PpeM~A_qxq3LV3zzKNs64F_TgsB5s7CgWuJ98sjdoCqAxZRPWpa8dkyfO~YBgr; session_key=v0tmwcmf1xqkp7697hhsno0di1smy3dm; _ga_0NY2JETSPJ=GS1.1.1741710601.1.1.1741710899.0.0.0",
            "Origin": "https://shop2game.com",
            "Referer": "https://shop2game.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"'
        }
        payload = {
            "app_id": 100067,
            "login_id": str(uid)
        }

        openid_res = requests.post(openid_url, headers=openid_headers, json=payload, verify=False, timeout=10)
        openid_data = openid_res.json()
        open_id = openid_data.get("open_id")

        if not open_id:
            return None, f"Failed to extract open_id - Response: {openid_data}"

        return open_id, None

    except Exception as e:
        return None, f"Exception occurred: {str(e)}"

def save_generated_token(region, token_data):
    """Save generated token to region-specific file with 8-hour expiration + send webhook"""
    import os
    from datetime import datetime, timedelta
    
    region = region.upper()
    token_dir = f"data/tokens/{region}"
    os.makedirs(token_dir, exist_ok=True)
    
    token_file = os.path.join(token_dir, "generated_tokens.json")
    
    token_entry = {
        "token": token_data["token"],
        "account_id": token_data["account_id"],
        "account_name": token_data["account_name"],
        "uid": token_data["account_id"],
        "server": region,
        "generated_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=8)).isoformat()
    }
    
    tokens_list = []
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                tokens_list = data.get("tokens", [])
        except:
            tokens_list = []
    
    # Remove expired tokens
    now = datetime.utcnow()
    tokens_list = [t for t in tokens_list if datetime.fromisoformat(t.get("expires_at", "")) > now]
    
    # Remove duplicate tokens with same UID (keep new one, remove old)
    uid_to_remove = token_entry["uid"]
    old_count = len(tokens_list)
    tokens_list = [t for t in tokens_list if t.get("uid") != uid_to_remove]
    if old_count > len(tokens_list):
        app.logger.info(f"🗑️ Removed {old_count - len(tokens_list)} duplicate token(s) for UID {uid_to_remove} from {region}")
    
    tokens_list.append(token_entry)
    
    token_data_to_save = {
        "server_name": region,
        "generated_at": datetime.utcnow().isoformat(),
        "total_tokens": len(tokens_list),
        "tokens": tokens_list
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data_to_save, f, indent=2)
    
    # Send webhook notification
    try:
        webhook_url = os.getenv('WEBHOOK_URL', '')
        if webhook_url:
            webhook_data = {
                "event_type": "token_generated",
                "region": region,
                "account_id": token_entry["account_id"],
                "account_name": token_entry["account_name"],
                "uid": token_entry["uid"],
                "generated_at": token_entry["generated_at"],
                "expires_at": token_entry["expires_at"],
                "total_tokens_in_region": len(tokens_list)
            }
            requests.post(webhook_url, json=webhook_data, timeout=5)
            app.logger.info(f"🔔 Webhook sent to {webhook_url} for {region}")
    except Exception as e:
        app.logger.debug(f"Webhook send skipped: {e}")
    
    app.logger.info(f"✅ Saved generated token for {region}: {token_entry['account_name']} (UID: {uid_to_remove})")

@app.route('/access-jwt', methods=['GET'])
def majorlogin_jwt():
    """Convert access token to JWT token with region support and save it"""
    access_token = request.args.get('access_token')
    provided_open_id = request.args.get('open_id')
    region = request.args.get('region', '').upper()

    if not access_token:
        return jsonify({"message": "missing access_token"}), 400
    
    if not region:
        return jsonify({"message": "missing region. Must provide one of: IND, AG, NX, BD, or PK"}), 400

    if region not in ['IND', 'AG', 'NX', 'BD', 'PK']:
        return jsonify({"message": "Invalid region. Must be IND, AG, NX, BD, or PK"}), 400

    # Try to get open_id from external API first
    open_id = provided_open_id
    if not open_id:
        try:
            external_api_url = "https://access-token-tau.vercel.app/access-jwt"
            params = {'access_token': access_token}
            ext_response = requests.get(external_api_url, params=params, timeout=10)
            
            if ext_response.status_code == 200:
                try:
                    ext_data = ext_response.json()
                    open_id = ext_data.get('open_id')
                except:
                    pass
        except:
            pass
        
        # If external API didn't work, try fetch_open_id
        if not open_id:
            open_id, error = fetch_open_id(access_token)
            if error:
                return jsonify({"message": error}), 400

    platforms = [8, 3, 4, 6]

    for platform_type in platforms:
        try:
            game_data = my_pb2.GameData()
            game_data.timestamp = "2024-12-05 18:15:32"
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.108.3"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = 1280
            game_data.screen_height = 960
            game_data.dpi = "240"
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = 5951
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game_data.ip_address = "172.190.111.97"
            game_data.language = "en"
            game_data.open_id = open_id
            game_data.access_token = access_token
            game_data.platform_type = platform_type
            game_data.field_99 = str(platform_type)
            game_data.field_100 = str(platform_type)

            serialized_data = game_data.SerializeToString()
            encrypted_data = encrypt_message(serialized_data)
            hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

            url = "https://loginbp.ggblueshark.com/MajorLogin"
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/octet-stream",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB51"
            }
            edata = bytes.fromhex(hex_encrypted_data)

            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)

            if response.status_code == 200:
                data_dict = None
                try:
                    example_msg = output_pb2.Garena_420()
                    example_msg.ParseFromString(response.content)
                    data_dict = {field.name: getattr(example_msg, field.name)
                                 for field in example_msg.DESCRIPTOR.fields
                                 if field.name not in ["binary", "binary_data", "Garena420"]}
                except Exception:
                    try:
                        data_dict = response.json()
                    except ValueError:
                        continue

                if data_dict and "token" in data_dict:
                    token_value = data_dict["token"]
                    try:
                        decoded_token = jwt.decode(token_value, options={"verify_signature": False})
                    except Exception as e:
                        decoded_token = {}

                    result = {
                        "account_id": decoded_token.get("account_id"),
                        "account_name": decoded_token.get("nickname"),
                        "open_id": open_id,
                        "access_token": access_token,
                        "platform": decoded_token.get("external_type"),
                        "region": region,
                        "status": "success",
                        "token": token_value
                    }
                    
                    # Save access token for future JWT regeneration (every 7 hours)
                    try:
                        access_token_manager.save_access_token(
                            region=region,
                            access_token=access_token,
                            open_id=open_id,
                            account_id=decoded_token.get("account_id"),
                            account_name=decoded_token.get("nickname")
                        )
                        app.logger.info(f"✅ Access token saved for {region}: {decoded_token.get('nickname')}")
                    except Exception as e:
                        app.logger.error(f"Failed to save access token: {e}")
                    
                    # Save JWT token to region-specific file for like functionality
                    try:
                        jwt_data = {
                            "success": True,
                            "token": token_value,
                            "account_id": decoded_token.get("account_id"),
                            "account_name": decoded_token.get("nickname"),
                            "region": region
                        }
                        access_token_manager.save_jwt_to_token_file(region, jwt_data)
                        save_generated_token(region, result)
                    except Exception as e:
                        app.logger.error(f"Failed to save token: {e}")
                    
                    return jsonify(result), 200
        except requests.RequestException:
            continue

    return jsonify({"message": "No valid platform found"}), 400

@app.route('/token', methods=['GET'])
def oauth_guest():
    """OAuth guest token endpoint"""
    uid = request.args.get('uid')
    password = request.args.get('password')
    if not uid or not password:
        return jsonify({"message": "Missing uid or password"}), 400

    oauth_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }

    try:
        oauth_response = requests.post(oauth_url, data=payload, headers=headers, timeout=10)
    except requests.RequestException as e:
        return jsonify({"message": str(e)}), 500

    if oauth_response.status_code != 200:
        try:
            return jsonify(oauth_response.json()), oauth_response.status_code
        except ValueError:
            return jsonify({"message": oauth_response.text}), oauth_response.status_code

    try:
        oauth_data = oauth_response.json()
    except ValueError:
        return jsonify({"message": "Invalid JSON response from OAuth service"}), 500

    if 'access_token' not in oauth_data or 'open_id' not in oauth_data:
        return jsonify({"message": "OAuth response missing access_token or open_id"}), 500

    params = {
        'access_token': oauth_data['access_token'],
        'open_id': oauth_data['open_id']
    }
    
    with app.test_request_context('/access-jwt', query_string=params):
        return majorlogin_jwt()

@app.route('/access-tokens', methods=['GET'])
def get_access_tokens():
    """Get all saved access tokens for a region"""
    region = request.args.get('region', '').upper()
    
    if region and region not in ['IND', 'AG', 'NX', 'BD', 'PK']:
        return jsonify({"error": "Invalid region. Must be IND, AG, NX, BD, or PK"}), 400
    
    if region:
        data = access_token_manager.get_access_tokens_for_region(region)
        return jsonify(data), 200
    else:
        all_regions = {}
        for reg in ['IND', 'AG', 'NX', 'BD', 'PK']:
            all_regions[reg] = access_token_manager.get_access_tokens_for_region(reg)
        return jsonify({"regions": all_regions}), 200

@app.route('/regenerate-jwts', methods=['GET', 'POST'])
def regenerate_jwts():
    """Manually trigger JWT regeneration from saved access tokens"""
    region = request.args.get('region', '').upper() if request.method == 'GET' else request.json.get('region', '').upper() if request.is_json else ''
    
    if region and region not in ['IND', 'AG', 'NX', 'BD', 'PK']:
        return jsonify({"error": "Invalid region. Must be IND, AG, NX, BD, or PK"}), 400
    
    app.logger.info(f"🔄 Manual JWT regeneration triggered for: {region or 'ALL regions'}")
    
    try:
        results = access_token_manager.regenerate_all_jwts(region if region else None)
        return jsonify({
            "status": "success",
            "message": f"JWT regeneration completed for {region or 'all regions'}",
            "results": results
        }), 200
    except Exception as e:
        app.logger.error(f"JWT regeneration failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/access-token-status', methods=['GET'])
def access_token_status():
    """Get status of access token manager and auto-regeneration"""
    try:
        status = access_token_manager.get_status()
        return jsonify({
            "status": "success",
            "access_token_manager": status
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start-auto-regeneration', methods=['POST', 'GET'])
def start_auto_regen():
    """Start automatic JWT regeneration (every 7 hours)"""
    try:
        access_token_manager.start_auto_regeneration()
        return jsonify({
            "status": "success",
            "message": "Auto JWT regeneration started (every 7 hours)"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop-auto-regeneration', methods=['POST', 'GET'])
def stop_auto_regen():
    """Stop automatic JWT regeneration"""
    try:
        access_token_manager.stop_auto_regeneration()
        return jsonify({
            "status": "success",
            "message": "Auto JWT regeneration stopped"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialize token generation when app starts (only if not on Vercel)
def initialize_token_generator():
    """Initialize token generator when app starts"""
    try:
        # Skip token generation on Vercel to avoid timeouts
        if not os.environ.get('VERCEL'):
            print("=" * 60)
            print("🚀 Initializing Automatic Token Generator...")
            print("=" * 60)
            start_token_generation()
            print("✅ Token generator initialization complete")
            print("=" * 60)
            
            # Verify it started
            import time
            time.sleep(2)  # Give scheduler time to start
            status = get_generator_status()
            if status['is_running']:
                print(f"✅ CONFIRMED: Scheduler is running with {status['jobs_count']} active jobs")
                print(f"📅 Next scheduled run: {status['next_run']}")
            else:
                print("⚠️ WARNING: Scheduler may not have started properly")
                print(f"Status: {status}")
            
            # Start auto JWT regeneration from access tokens (every 7 hours)
            print("=" * 60)
            print("🔄 Starting Auto JWT Regeneration (every 7 hours)...")
            print("=" * 60)
            access_token_manager.start_auto_regeneration()
            print("✅ Auto JWT regeneration started")
            print("=" * 60)
        else:
            print("Running on Vercel - skipping automatic token generation")
    except Exception as e:
        print(f"❌ Failed to start token generator: {e}")
        import traceback
        traceback.print_exc()

# Start the token generator (only in non-Vercel environments)
initialize_token_generator()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
