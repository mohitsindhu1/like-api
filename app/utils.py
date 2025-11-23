import json
import os
import random


def load_tokens_smart(server_name, count=110):
    """Load tokens using smart rotation system - ensures all tokens are used equally"""
    try:
        from smart_token_rotation import rotation_manager
        smart_tokens = rotation_manager.get_smart_tokens(server_name, count)
        if smart_tokens:
            token_list = []
            for token_data in smart_tokens:
                token_list.append({
                    "token": token_data.get('token', ''),
                    "uid": token_data.get('uid', 'unknown'),
                    "server": server_name.upper()
                })
            print(f"🔄 Loaded {len(token_list)} smart-rotated tokens for {server_name.upper()} server")
            return token_list
    except Exception as e:
        print(f"Smart rotation failed, falling back: {e}")
    
    # Fallback to regular loading
    return load_tokens(server_name, count)


def load_tokens(server_name, count=None):
    """Load tokens from region-based storage with expiration filtering"""
    from datetime import datetime
    
    try:
        server_name = server_name.upper()
        token_file = f"data/tokens/{server_name}/generated_tokens.json"
        
        # Check if region-based token file exists
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                
                tokens_data = data.get('tokens', [])
                
                if tokens_data:
                    token_list = []
                    now = datetime.utcnow()
                    
                    for token_data in tokens_data:
                        # Check if token has expired
                        expires_at = token_data.get('expires_at')
                        if expires_at:
                            try:
                                expiry_time = datetime.fromisoformat(expires_at)
                                if expiry_time <= now:
                                    continue  # Skip expired tokens
                            except:
                                pass
                        
                        token_list.append({
                            "token": token_data.get('token', ''),
                            "uid": token_data.get('uid', 'unknown'),
                            "server": server_name
                        })
                    
                    # If count specified, limit tokens
                    if count:
                        token_list = token_list[:count]
                    
                    # Shuffle tokens randomly for each request
                    random.shuffle(token_list)
                    print(f"📊 Loaded {len(token_list)} valid tokens from {server_name}/generated_tokens.json (expired tokens filtered)")
                    return token_list
                else:
                    print(f"⚠️ No tokens found in {token_file}")
                    return []
                    
            except Exception as e:
                print(f"❌ Error reading {token_file}: {e}")
                return []
        else:
            print(f"⚠️ Token file not found: {token_file}")
            return []
            
    except Exception as e:
        print(f"❌ Token loading error: {e}")
        return []
