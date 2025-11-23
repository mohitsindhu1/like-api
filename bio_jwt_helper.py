"""
Bio Update & JWT Helper Functions
==================================
Helper functions for bio update and JWT token generation
"""

import httpx
import json
import base64
import asyncio
from typing import Tuple, Optional
from google.protobuf import json_format
from Crypto.Cipher import AES
from ff_proto import freefire_pb2

# Encryption constants
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
RELEASEVERSION = "OB51"

# Region server URLs
REGION_SERVER_URLS = {
    "IND": "https://client.ind.freefiremobile.com",
    "BR": "https://client.us.freefiremobile.com",
    "US": "https://client.us.freefiremobile.com",
    "BD": "https://clientbp.ggblueshark.com",
    "SG": "https://client.sg.freefiremobile.com",
    "PK": "https://clientbp.ggblueshark.com",
    "RU": "https://clientbp.ggblueshark.com",
    "ID": "https://clientbp.ggblueshark.com",
    "TW": "https://clientbp.ggblueshark.com",
    "VN": "https://clientbp.ggblueshark.com",
    "TH": "https://clientbp.ggblueshark.com",
    "ME": "https://clientbp.ggblueshark.com",
    "CIS": "https://clientbp.ggblueshark.com"
}

def pad(text: bytes) -> bytes:
    """PKCS7 Padding"""
    padding_length = AES.block_size - (len(text) % AES.block_size)
    padding = bytes([padding_length] * padding_length)
    return text + padding

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """AES-CBC encryption"""
    aes = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = pad(plaintext)
    return aes.encrypt(padded_plaintext)

def decode_protobuf(encoded_data: bytes, message_type):
    """Decode protobuf message"""
    message_instance = message_type()
    message_instance.ParseFromString(encoded_data)
    return message_instance

async def json_to_proto(json_data: str, proto_message) -> bytes:
    """Convert JSON to Protobuf bytes"""
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def get_region_server_url(region: str) -> str:
    """Get server URL for region"""
    return REGION_SERVER_URLS.get(region.upper(), "https://clientbp.ggblueshark.com")

def parse_jwt_token(jwt_token: str) -> dict:
    """Parse JWT token to extract user info"""
    try:
        parts = jwt_token.split('.')
        if len(parts) >= 2:
            payload = parts[1]
            # Add padding if needed
            missing_padding = len(payload) % 4
            if missing_padding:
                payload += '=' * (4 - missing_padding)
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
    except Exception:
        return {}

# ===== ACCESS TOKEN FUNCTIONS =====

async def get_access_token_and_open_id(uid: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """Get access token and open_id from UID and password"""
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = f"uid={uid}&password={password}&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    
    headers = {
        'User-Agent': USERAGENT,
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            data = response.json()
            return data.get("access_token"), data.get("open_id")
    except Exception:
        return None, None

# ===== JWT GENERATION FUNCTIONS =====

async def create_jwt_from_uid_password(uid: str, password: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Create JWT from UID and password"""
    # Step 1: Get access token
    access_token, open_id = await get_access_token_and_open_id(uid, password)
    
    if not access_token or not open_id:
        return None, None, None
    
    # Step 2: Create JWT from access token
    return await create_jwt_from_access_token(access_token, open_id)

async def create_jwt_from_access_token(access_token: str, open_id: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Create JWT from access token and open_id"""
    try:
        json_data = json.dumps({
            "open_id": open_id,
            "open_id_type": "4",
            "login_token": access_token,
            "orign_platform_type": "4"
        })
        
        proto_msg = freefire_pb2.LoginReq()
        json_format.ParseDict(json.loads(json_data), proto_msg)
        encoded_result = proto_msg.SerializeToString()
        payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, encoded_result)
        
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                message = json.loads(json_format.MessageToJson(
                    decode_protobuf(response.content, freefire_pb2.LoginRes)
                ))
                
                return message.get("token"), message.get("lockRegion"), message.get("serverUrl")
        
        return None, None, None
    except Exception:
        return None, None, None

# ===== BIO UPDATE FUNCTIONS =====

def encrypt_bio_protobuf(bio_text: str) -> bytes:
    """Encrypt bio text for API request"""
    try:
        # Import the bio update protobuf
        from ff_proto import bio_update_pb2
        
        # Create protobuf message
        bio_msg = bio_update_pb2.UpdateSocialBasicInfo()
        bio_msg.signature = bio_text
        
        # Serialize and encrypt
        serialized = bio_msg.SerializeToString()
        encrypted = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, serialized)
        
        return encrypted
    except Exception as e:
        # Fallback: create a simple protobuf structure
        # Field 1 = signature (string)
        bio_bytes = bio_text.encode('utf-8')
        # Simple protobuf encoding: field 1, wire type 2 (length-delimited)
        length = len(bio_bytes)
        protobuf_data = bytes([0x0a]) + bytes([length]) + bio_bytes
        return aes_cbc_encrypt(MAIN_KEY, MAIN_IV, protobuf_data)

async def update_bio_endpoint(uid: str, password: str, custom_bio: str) -> dict:
    """Update bio using UID, password and custom bio text"""
    
    # Step 1: Get access token and open_id
    access_token, open_id = await get_access_token_and_open_id(uid, password)
    
    if not access_token or not open_id:
        return {
            "success": False,
            "error": "Failed to get access token/open_id",
            "message": "Please check your UID and password"
        }
    
    # Step 2: Create JWT
    jwt_token, region, server_url = await create_jwt_from_access_token(access_token, open_id)
    
    if not jwt_token:
        return {
            "success": False,
            "error": "Failed to create JWT token"
        }
    
    # Step 3: Parse JWT to get user info
    parsed = parse_jwt_token(jwt_token)
    user_uid = parsed.get('uid', uid)
    nickname = parsed.get('nickname', f'Player_{uid}')
    
    # Step 4: Encrypt bio
    encrypted_bio = encrypt_bio_protobuf(custom_bio)
    update_url = f"{get_region_server_url(region or 'IND')}/UpdateSocialBasicInfo"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": USERAGENT
    }
    
    # Step 5: Send update request
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(update_url, headers=headers, content=encrypted_bio)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Bio updated successfully!",
                    "data": {
                        "uid": user_uid,
                        "nickname": nickname,
                        "region": region,
                        "new_bio": custom_bio
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "response": response.text[:200]
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
