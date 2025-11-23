"""
Internal File Storage System for Free Fire Tokens
Professional file-based storage that works like a database
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class InternalTokenStorage:
    """Professional internal token storage system using JSON files"""
    
    def __init__(self):
        self.storage_dir = "data/tokens"
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"✅ Internal storage ready: {self.storage_dir}")
    
    def get_token_file_path(self, server_name: str) -> str:
        """Get file path for server tokens"""
        return os.path.join(self.storage_dir, f"{server_name.lower()}_tokens.json")
    
    def save_tokens(self, server_name: str, tokens: List[Dict]) -> bool:
        """Save tokens to internal file storage"""
        try:
            file_path = self.get_token_file_path(server_name)
            
            # Prepare token data with metadata
            token_data = {
                "server_name": server_name.upper(),
                "generated_at": datetime.utcnow().isoformat(),
                "total_tokens": len(tokens),
                "tokens": tokens
            }
            
            # Write to file with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved {len(tokens)} tokens to internal file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save tokens to file: {str(e)}")
            return False
    
    def load_tokens(self, server_name: str) -> List[Dict]:
        """Load tokens from internal file storage"""
        try:
            file_path = self.get_token_file_path(server_name)
            
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ Token file not found: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            tokens = token_data.get('tokens', [])
            logger.info(f"📊 Loaded {len(tokens)} tokens from internal file: {file_path}")
            return tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to load tokens from file: {str(e)}")
            return []
    
    def get_token_stats(self, server_name: str) -> Dict:
        """Get token statistics from internal storage"""
        try:
            file_path = self.get_token_file_path(server_name)
            
            if not os.path.exists(file_path):
                return {"total": 0, "generated_at": None}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            return {
                "total": token_data.get('total_tokens', 0),
                "generated_at": token_data.get('generated_at'),
                "server_name": token_data.get('server_name')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get token stats: {str(e)}")
            return {"total": 0, "generated_at": None}
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all servers"""
        stats = {}
        servers = ['IND', 'NX', 'AG']
        
        for server in servers:
            stats[server] = self.get_token_stats(server)
        
        return stats
    
    def clear_tokens(self, server_name: str) -> bool:
        """Clear tokens for a specific server"""
        try:
            file_path = self.get_token_file_path(server_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"✅ Cleared tokens for server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear tokens: {str(e)}")
            return False

# Global instance
storage = InternalTokenStorage()