import json
import os
import threading
import time
import requests
import binascii
import jwt as pyjwt
from datetime import datetime, timedelta
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def encrypt_message_local(plaintext):
    """Local encrypt_message function for JWT generation"""
    try:
        key = b"Yg&tc%DEuh6%Zc^8"
        iv = b"6oyZDr22E3ychjM%"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        encrypted_message = cipher.encrypt(padded_message)
        return encrypted_message
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return None

ACCESS_TOKENS_DIR = "data/access_tokens"
TOKENS_DIR = "data/tokens"
JWT_REGENERATION_HOURS = 7

os.makedirs(ACCESS_TOKENS_DIR, exist_ok=True)

class AccessTokenManager:
    def __init__(self):
        self.scheduler_running = False
        self.scheduler_thread = None
        self.last_regeneration = {}
        
    def get_access_token_file(self, region):
        return os.path.join(ACCESS_TOKENS_DIR, f"{region.lower()}_access_tokens.json")
    
    def get_jwt_token_file(self, region):
        return os.path.join(TOKENS_DIR, f"{region.lower()}_tokens.json")
    
    def save_access_token(self, region, access_token, open_id, account_id=None, account_name=None):
        region = region.upper()
        file_path = self.get_access_token_file(region)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "region": region,
                    "access_tokens": [],
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            existing_tokens = {t.get('access_token'): i for i, t in enumerate(data.get('access_tokens', []))}
            
            token_entry = {
                "access_token": access_token,
                "open_id": open_id,
                "account_id": account_id,
                "account_name": account_name,
                "added_at": datetime.utcnow().isoformat(),
                "last_jwt_generated": None,
                "jwt_generation_count": 0
            }
            
            if access_token in existing_tokens:
                idx = existing_tokens[access_token]
                old_entry = data['access_tokens'][idx]
                token_entry['jwt_generation_count'] = old_entry.get('jwt_generation_count', 0)
                token_entry['last_jwt_generated'] = old_entry.get('last_jwt_generated')
                data['access_tokens'][idx] = token_entry
                logger.info(f"Updated existing access token for {region}: {account_name or 'Unknown'}")
            else:
                data['access_tokens'].append(token_entry)
                logger.info(f"Added new access token for {region}: {account_name or 'Unknown'}")
            
            data['last_updated'] = datetime.utcnow().isoformat()
            data['total_tokens'] = len(data['access_tokens'])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved access token for {region}. Total tokens: {len(data['access_tokens'])}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save access token for {region}: {e}")
            return False
    
    def load_access_tokens(self, region):
        region = region.upper()
        file_path = self.get_access_token_file(region)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('access_tokens', [])
        except Exception as e:
            logger.error(f"Failed to load access tokens for {region}: {e}")
        
        return []
    
    def generate_jwt_from_access_token(self, access_token, open_id, region):
        import my_pb2
        import output_pb2
        
        platforms = [8, 3, 4, 6]
        
        for platform_type in platforms:
            try:
                game_data = my_pb2.GameData()
                game_data.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
                encrypted_data = encrypt_message_local(serialized_data)
                if encrypted_data is None:
                    continue
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
                            decoded_token = pyjwt.decode(token_value, options={"verify_signature": False})
                        except Exception:
                            decoded_token = {}

                        return {
                            "success": True,
                            "token": token_value,
                            "account_id": decoded_token.get("account_id"),
                            "account_name": decoded_token.get("nickname"),
                            "region": region
                        }
            except Exception as e:
                logger.error(f"Error generating JWT with platform {platform_type}: {e}")
                continue
        
        return {"success": False, "error": "Failed to generate JWT with all platforms"}
    
    def save_jwt_to_token_file(self, region, jwt_result):
        region = region.upper()
        file_path = self.get_jwt_token_file(region)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "server_name": region,
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_tokens": 0,
                    "tokens": []
                }
            
            existing_uids = {str(t.get('uid')): i for i, t in enumerate(data.get('tokens', []))}
            
            token_entry = {
                "token": jwt_result['token'],
                "uid": str(jwt_result.get('account_id', '')),
                "server": region,
                "account_name": jwt_result.get('account_name', ''),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            uid_str = str(jwt_result.get('account_id', ''))
            if uid_str and uid_str in existing_uids:
                data['tokens'][existing_uids[uid_str]] = token_entry
                logger.info(f"🔄 Updated JWT for {region}: {jwt_result.get('account_name', 'Unknown')}")
            else:
                data['tokens'].append(token_entry)
                logger.info(f"➕ Added new JWT for {region}: {jwt_result.get('account_name', 'Unknown')}")
            
            data['generated_at'] = datetime.utcnow().isoformat()
            data['total_tokens'] = len(data['tokens'])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save JWT to token file for {region}: {e}")
            return False
    
    def update_access_token_jwt_status(self, region, access_token):
        region = region.upper()
        file_path = self.get_access_token_file(region)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for token_entry in data.get('access_tokens', []):
                    if token_entry.get('access_token') == access_token:
                        token_entry['last_jwt_generated'] = datetime.utcnow().isoformat()
                        token_entry['jwt_generation_count'] = token_entry.get('jwt_generation_count', 0) + 1
                        break
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            logger.error(f"Failed to update access token JWT status: {e}")
    
    def regenerate_all_jwts(self, region=None):
        regions = [region.upper()] if region else ['IND', 'AG', 'NX', 'BD', 'PK']
        results = {
            "success": 0,
            "failed": 0,
            "regions_processed": [],
            "details": []
        }
        
        for reg in regions:
            access_tokens = self.load_access_tokens(reg)
            
            if not access_tokens:
                logger.info(f"No access tokens found for {reg}")
                continue
            
            logger.info(f"🔄 Regenerating JWTs for {reg}: {len(access_tokens)} access tokens")
            results["regions_processed"].append(reg)
            
            for token_data in access_tokens:
                access_token = token_data.get('access_token')
                open_id = token_data.get('open_id')
                
                if not access_token or not open_id:
                    continue
                
                try:
                    jwt_result = self.generate_jwt_from_access_token(access_token, open_id, reg)
                    
                    if jwt_result.get('success'):
                        self.save_jwt_to_token_file(reg, jwt_result)
                        self.update_access_token_jwt_status(reg, access_token)
                        results["success"] += 1
                        results["details"].append({
                            "region": reg,
                            "account_name": jwt_result.get('account_name'),
                            "status": "success"
                        })
                        logger.info(f"✅ JWT regenerated for {reg}: {jwt_result.get('account_name')}")
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "region": reg,
                            "access_token": access_token[:20] + "...",
                            "status": "failed",
                            "error": jwt_result.get('error')
                        })
                        
                except Exception as e:
                    results["failed"] += 1
                    logger.error(f"❌ Failed to regenerate JWT: {e}")
                
                time.sleep(0.5)
        
        results["completed_at"] = datetime.utcnow().isoformat()
        self.last_regeneration = results
        return results
    
    def start_auto_regeneration(self):
        if self.scheduler_running:
            logger.info("Auto JWT regeneration already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._regeneration_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info(f"🚀 Started auto JWT regeneration (every {JWT_REGENERATION_HOURS} hours)")
    
    def stop_auto_regeneration(self):
        self.scheduler_running = False
        logger.info("🛑 Stopped auto JWT regeneration")
    
    def _regeneration_loop(self):
        interval_seconds = JWT_REGENERATION_HOURS * 60 * 60
        
        while self.scheduler_running:
            try:
                logger.info(f"⏰ Starting scheduled JWT regeneration at {datetime.utcnow().isoformat()}")
                results = self.regenerate_all_jwts()
                logger.info(f"✅ Scheduled regeneration complete: {results['success']} success, {results['failed']} failed")
            except Exception as e:
                logger.error(f"❌ Error in scheduled regeneration: {e}")
            
            for _ in range(int(interval_seconds)):
                if not self.scheduler_running:
                    break
                time.sleep(1)
    
    def get_status(self):
        status = {
            "scheduler_running": self.scheduler_running,
            "regeneration_interval_hours": JWT_REGENERATION_HOURS,
            "last_regeneration": self.last_regeneration,
            "regions": {}
        }
        
        for region in ['IND', 'AG', 'NX', 'BD', 'PK']:
            access_tokens = self.load_access_tokens(region)
            status["regions"][region] = {
                "access_tokens_count": len(access_tokens),
                "file_path": self.get_access_token_file(region)
            }
        
        return status
    
    def get_access_tokens_for_region(self, region):
        region = region.upper()
        access_tokens = self.load_access_tokens(region)
        return {
            "region": region,
            "total_tokens": len(access_tokens),
            "tokens": access_tokens
        }

access_token_manager = AccessTokenManager()
