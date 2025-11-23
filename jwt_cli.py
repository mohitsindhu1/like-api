#!/usr/bin/env python3
"""
FreeFire JWT Generator - CLI Version
====================================
Command line se direct JWT generate karo

Usage:
    python jwt_cli.py <UID> <PASSWORD>
    
Example:
    python jwt_cli.py 1234567890 abc123def456789
"""

import httpx
import asyncio
import json
import base64
import sys
from typing import Tuple
from google.protobuf import json_format, message
from Crypto.Cipher import AES
from ff_proto import freefire_pb2

MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB51"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"

async def json_to_proto(json_data: str, proto_message: message.Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    message_instance = message_type()
    message_instance.ParseFromString(encoded_data)
    return message_instance

async def get_access_token(uid: str, password: str) -> Tuple[str, str]:
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = f"uid={uid}&password={password}&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    
    headers = {
        'User-Agent': USERAGENT,
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload, headers=headers)
        data = response.json()
        return data.get("access_token", "0"), data.get("open_id", "0")

async def generate_jwt(uid: str, password: str) -> Tuple[str, str, str]:
    access_token, open_id = await get_access_token(uid, password)
    
    if access_token == "0":
        raise ValueError("Failed to obtain access token")
    
    json_data = json.dumps({
        "open_id": open_id,
        "open_id_type": "4",
        "login_token": access_token,
        "orign_platform_type": "4"
    })
    
    encoded_result = await json_to_proto(json_data, freefire_pb2.LoginReq())
    encrypted_payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, encoded_result)
    
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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=encrypted_payload, headers=headers)
        message = json.loads(json_format.MessageToJson(
            decode_protobuf(response.content, freefire_pb2.LoginRes)
        ))
        
        jwt_token = message.get("token", "0")
        region = message.get("lockRegion", "0")
        server_url = message.get("serverUrl", "0")
        
        if jwt_token == "0":
            raise ValueError("Failed to generate JWT")
        
        return jwt_token, region, server_url

async def main():
    if len(sys.argv) != 3:
        print("Usage: python jwt_cli.py <UID> <PASSWORD>")
        print("\nExample:")
        print("  python jwt_cli.py 1234567890 abc123def456789")
        sys.exit(1)
    
    uid = sys.argv[1]
    password = sys.argv[2]
    
    try:
        jwt_token, region, server_url = await generate_jwt(uid, password)
        
        result = {
            "success": True,
            "jwt_token": jwt_token,
            "region": region,
            "server_url": server_url,
            "uid": uid
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
