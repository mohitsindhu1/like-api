"""
Experimental JWT Generation WITHOUT Open ID
============================================
Testing different approaches to generate JWT without knowing open_id
"""

import httpx
import json
import base64
import asyncio
from google.protobuf import json_format
from Crypto.Cipher import AES
from ff_proto import freefire_pb2

# Constants
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
RELEASEVERSION = "OB51"

def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def decode_protobuf(encoded_data: bytes, message_type):
    message_instance = message_type()
    message_instance.ParseFromString(encoded_data)
    return message_instance

# ===== EXPERIMENTAL APPROACHES =====

async def approach_1_empty_openid(access_token: str):
    """
    Approach 1: Try with empty open_id
    Result: Will likely FAIL - open_id is required
    """
    print("\n🧪 Approach 1: Empty Open ID")
    try:
        json_data = json.dumps({
            "open_id": "",  # Empty
            "open_id_type": "4",
            "login_token": access_token,
            "orign_platform_type": "4"
        })
        
        proto_msg = freefire_pb2.LoginReq()
        json_format.ParseDict(json.loads(json_data), proto_msg)
        payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_msg.SerializeToString())
        
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
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
                print(f"✅ SUCCESS! Token: {message.get('token')[:50]}...")
                return message.get("token")
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


async def approach_2_uid_as_openid(access_token: str, uid: str):
    """
    Approach 2: Use UID as open_id
    Result: Might work if open_id == UID
    """
    print(f"\n🧪 Approach 2: Using UID as Open ID ({uid})")
    try:
        json_data = json.dumps({
            "open_id": str(uid),  # Use UID
            "open_id_type": "4",
            "login_token": access_token,
            "orign_platform_type": "4"
        })
        
        proto_msg = freefire_pb2.LoginReq()
        json_format.ParseDict(json.loads(json_data), proto_msg)
        payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_msg.SerializeToString())
        
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
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
                print(f"✅ SUCCESS! Token: {message.get('token')[:50]}...")
                return message.get("token")
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


async def approach_3_default_openid(access_token: str):
    """
    Approach 3: Try common default open_id values
    Result: Very low chance of success
    """
    print("\n🧪 Approach 3: Trying Default Open IDs")
    
    # Common defaults to try
    default_ids = ["0", "1", "guest", "default"]
    
    for default_id in default_ids:
        print(f"  Trying: {default_id}")
        try:
            json_data = json.dumps({
                "open_id": default_id,
                "open_id_type": "4",
                "login_token": access_token,
                "orign_platform_type": "4"
            })
            
            proto_msg = freefire_pb2.LoginReq()
            json_format.ParseDict(json.loads(json_data), proto_msg)
            payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_msg.SerializeToString())
            
            url = "https://loginbp.ggblueshark.com/MajorLogin"
            headers = {
                'User-Agent': USERAGENT,
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/octet-stream",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': RELEASEVERSION
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=payload, headers=headers)
                
                if response.status_code == 200:
                    message = json.loads(json_format.MessageToJson(
                        decode_protobuf(response.content, freefire_pb2.LoginRes)
                    ))
                    print(f"  ✅ SUCCESS with '{default_id}'!")
                    return message.get("token")
        except Exception:
            continue
    
    print("  ❌ All defaults failed")
    return None


# ===== TEST FUNCTION =====

async def test_all_approaches(access_token: str, uid: str = None):
    """Test all experimental approaches"""
    print("=" * 60)
    print("🔬 Experimental JWT Generation (Without Open ID)")
    print("=" * 60)
    
    # Approach 1: Empty
    result1 = await approach_1_empty_openid(access_token)
    
    # Approach 2: UID as open_id (if UID provided)
    result2 = None
    if uid:
        result2 = await approach_2_uid_as_openid(access_token, uid)
    
    # Approach 3: Default values
    result3 = await approach_3_default_openid(access_token)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    print(f"  Approach 1 (Empty): {'✅ SUCCESS' if result1 else '❌ FAILED'}")
    print(f"  Approach 2 (UID): {'✅ SUCCESS' if result2 else '❌ FAILED'}")
    print(f"  Approach 3 (Defaults): {'✅ SUCCESS' if result3 else '❌ FAILED'}")
    print("=" * 60)
    
    return result1 or result2 or result3


if __name__ == "__main__":
    print("\n⚠️  This is EXPERIMENTAL!")
    print("💡 Usage:")
    print("   from experimental_jwt import test_all_approaches")
    print("   token = asyncio.run(test_all_approaches(access_token, uid))")
    print()
