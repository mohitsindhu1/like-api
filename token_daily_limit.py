"""
Daily Usage Limit System for Tokens
Ensures each token is used maximum 20 times per day
Automatically resets daily
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TokenDailyLimit:
    """Track and enforce daily usage limits for tokens"""
    
    def __init__(self):
        self.limit_dir = "data/daily_limits"
        self.daily_limit = 1000  # Maximum uses per token per day (effectively unlimited)
        self.ensure_limit_directory()
    
    def ensure_limit_directory(self):
        """Ensure daily limit tracking directory exists"""
        os.makedirs(self.limit_dir, exist_ok=True)
        logger.info(f"✅ Daily limit tracking ready: {self.limit_dir}")
    
    def get_limit_file_path(self, server_name: str) -> str:
        """Get daily limit file path for server"""
        return os.path.join(self.limit_dir, f"{server_name.lower()}_daily_usage.json")
    
    def get_today_date(self) -> str:
        """Get today's date as string (YYYY-MM-DD format)"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def load_daily_usage(self, server_name: str) -> Dict:
        """Load daily usage data for a server"""
        try:
            file_path = self.get_limit_file_path(server_name)
            
            if not os.path.exists(file_path):
                return {
                    "date": self.get_today_date(),
                    "usage": {}  # uid: usage_count
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if data is from today, if not reset
            if data.get("date") != self.get_today_date():
                logger.info(f"🔄 New day detected for {server_name}, resetting usage counts")
                return {
                    "date": self.get_today_date(),
                    "usage": {}
                }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load daily usage: {str(e)}")
            return {
                "date": self.get_today_date(),
                "usage": {}
            }
    
    def save_daily_usage(self, server_name: str, usage_data: Dict):
        """Save daily usage data for a server"""
        try:
            file_path = self.get_limit_file_path(server_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save daily usage: {str(e)}")
    
    def get_token_usage_count(self, server_name: str, token_uid: str) -> int:
        """Get current usage count for a token today"""
        usage_data = self.load_daily_usage(server_name)
        return usage_data.get("usage", {}).get(str(token_uid), 0)
    
    def is_token_available(self, server_name: str, token_uid: str) -> bool:
        """Check if token is available for use (hasn't exceeded daily limit)"""
        usage_count = self.get_token_usage_count(server_name, token_uid)
        available = usage_count < self.daily_limit
        
        if not available:
            logger.debug(f"Token {token_uid} reached daily limit ({usage_count}/{self.daily_limit})")
        
        return available
    
    def mark_token_used(self, server_name: str, token_uid: str):
        """Mark a token as used (increment usage count)"""
        usage_data = self.load_daily_usage(server_name)
        
        uid_str = str(token_uid)
        current_count = usage_data.get("usage", {}).get(uid_str, 0)
        
        if "usage" not in usage_data:
            usage_data["usage"] = {}
        
        usage_data["usage"][uid_str] = current_count + 1
        
        self.save_daily_usage(server_name, usage_data)
        
        logger.debug(f"Token {token_uid} used: {usage_data['usage'][uid_str]}/{self.daily_limit} today")
    
    def filter_available_tokens(self, server_name: str, tokens: List[Dict]) -> List[Dict]:
        """
        Filter tokens to only include those that haven't exceeded daily limit
        
        Args:
            server_name: Server name (IND, NX, AG)
            tokens: List of token dictionaries with 'uid' field
        
        Returns:
            List of tokens that are still available for use today
        """
        if not tokens:
            return []
        
        usage_data = self.load_daily_usage(server_name)
        available_tokens = []
        
        for token in tokens:
            token_uid = str(token.get("uid", "unknown"))
            usage_count = usage_data.get("usage", {}).get(token_uid, 0)
            
            if usage_count < self.daily_limit:
                available_tokens.append(token)
        
        filtered_count = len(tokens) - len(available_tokens)
        if filtered_count > 0:
            logger.info(f"🚫 Filtered out {filtered_count} tokens that reached daily limit for {server_name}")
        
        logger.info(f"✅ {len(available_tokens)}/{len(tokens)} tokens available for use today on {server_name}")
        
        return available_tokens
    
    def get_usage_stats(self, server_name: str) -> Dict:
        """Get usage statistics for a server"""
        try:
            usage_data = self.load_daily_usage(server_name)
            usage = usage_data.get("usage", {})
            
            total_tokens = len(usage)
            tokens_at_limit = sum(1 for count in usage.values() if count >= self.daily_limit)
            total_requests_today = sum(usage.values())
            
            return {
                "server": server_name.upper(),
                "date": usage_data.get("date", self.get_today_date()),
                "daily_limit_per_token": self.daily_limit,
                "total_tokens_used_today": total_tokens,
                "tokens_at_daily_limit": tokens_at_limit,
                "tokens_still_available": total_tokens - tokens_at_limit,
                "total_requests_sent_today": total_requests_today,
                "average_usage_per_token": round(total_requests_today / max(total_tokens, 1), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return {"error": str(e)}
    
    def reset_daily_usage(self, server_name: str):
        """Manually reset daily usage for a server (for testing or manual reset)"""
        try:
            usage_data = {
                "date": self.get_today_date(),
                "usage": {}
            }
            self.save_daily_usage(server_name, usage_data)
            logger.info(f"✅ Reset daily usage for {server_name}")
        except Exception as e:
            logger.error(f"Failed to reset daily usage: {str(e)}")

# Global daily limit manager
daily_limit_manager = TokenDailyLimit()
