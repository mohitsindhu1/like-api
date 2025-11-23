"""
Smart Token Rotation System
Professional rotation system that ensures all tokens are used equally
"""
import json
import os
import random
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SmartTokenRotation:
    """Professional token rotation system with equal distribution"""
    
    def __init__(self):
        self.rotation_dir = "data/rotation"
        self.ensure_rotation_directory()
        self.rotation_data = {}
    
    def ensure_rotation_directory(self):
        """Ensure rotation tracking directory exists"""
        os.makedirs(self.rotation_dir, exist_ok=True)
        logger.info(f"✅ Token rotation tracking ready: {self.rotation_dir}")
    
    def get_rotation_file_path(self, server_name: str) -> str:
        """Get rotation tracking file path for server"""
        return os.path.join(self.rotation_dir, f"{server_name.lower()}_rotation.json")
    
    def load_rotation_state(self, server_name: str) -> Dict:
        """Load rotation state for a server"""
        try:
            file_path = self.get_rotation_file_path(server_name)
            
            if not os.path.exists(file_path):
                # Initialize new rotation state
                return {
                    "used_tokens": [],
                    "available_tokens": [],
                    "total_tokens": 0,
                    "rotation_cycle": 0
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load rotation state: {str(e)}")
            return {
                "used_tokens": [],
                "available_tokens": [],
                "total_tokens": 0,
                "rotation_cycle": 0
            }
    
    def save_rotation_state(self, server_name: str, state: Dict):
        """Save rotation state for a server"""
        try:
            file_path = self.get_rotation_file_path(server_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save rotation state: {str(e)}")
    
    def get_smart_tokens(self, server_name: str, request_count: int = 110) -> List[Dict]:
        """
        Get smart rotated tokens for like requests with daily usage limit
        
        Args:
            server_name: Server to get tokens from (IND, PK, etc.)
            request_count: Number of tokens needed (default 110)
        
        Returns:
            List of selected tokens with rotation tracking and daily limit enforcement
        """
        try:
            from internal_storage import storage
            from token_daily_limit import daily_limit_manager
            
            # Load all available tokens for this server
            all_tokens = storage.load_tokens(server_name.upper())
            
            if not all_tokens:
                logger.warning(f"⚠️ No tokens available for server {server_name}")
                return []
            
            # Filter tokens based on daily usage limit (max 20 uses per day)
            all_tokens = daily_limit_manager.filter_available_tokens(server_name, all_tokens)
            
            if not all_tokens:
                logger.warning(f"⚠️ All tokens have reached their daily limit (20 uses) for {server_name}")
                return []
            
            if len(all_tokens) < request_count:
                logger.warning(f"⚠️ Only {len(all_tokens)} tokens available after daily limit filter, using all")
                request_count = len(all_tokens)
            
            # Load rotation state
            rotation_state = self.load_rotation_state(server_name)
            
            # If this is a fresh start or tokens changed, reset rotation
            if (rotation_state["total_tokens"] != len(all_tokens) or
                len(rotation_state["available_tokens"]) == 0):
                
                # Create fresh token index list for rotation
                token_indices = list(range(len(all_tokens)))
                random.shuffle(token_indices)  # Randomize initial order
                
                rotation_state = {
                    "used_tokens": [],
                    "available_tokens": token_indices,
                    "total_tokens": len(all_tokens),
                    "rotation_cycle": rotation_state.get("rotation_cycle", 0)
                }
                
                logger.info(f"🔄 Started new rotation cycle {rotation_state['rotation_cycle']} for {server_name} with {len(all_tokens)} tokens")
            
            # Select tokens for this request
            selected_indices = []
            tokens_needed = min(request_count, len(rotation_state["available_tokens"]))
            
            # Take tokens from available list
            for _ in range(tokens_needed):
                if rotation_state["available_tokens"]:
                    index = rotation_state["available_tokens"].pop(0)
                    selected_indices.append(index)
                    rotation_state["used_tokens"].append(index)
            
            # If we need more tokens and available list is empty, start new cycle
            if tokens_needed < request_count and not rotation_state["available_tokens"]:
                # Reset for new rotation cycle
                remaining_needed = request_count - tokens_needed
                unused_indices = [i for i in range(len(all_tokens)) if i not in selected_indices]
                random.shuffle(unused_indices)
                
                # Take additional tokens from new cycle
                additional_tokens = unused_indices[:remaining_needed]
                selected_indices.extend(additional_tokens)
                
                # Update rotation state for new cycle
                rotation_state["used_tokens"] = additional_tokens
                rotation_state["available_tokens"] = unused_indices[remaining_needed:]
                rotation_state["rotation_cycle"] += 1
                
                logger.info(f"🔄 Started rotation cycle {rotation_state['rotation_cycle']} for {server_name}")
            
            # Convert indices to actual tokens
            selected_tokens = [all_tokens[i] for i in selected_indices]
            
            # Save updated rotation state
            self.save_rotation_state(server_name, rotation_state)
            
            logger.info(f"🎯 Selected {len(selected_tokens)} rotated tokens for {server_name} (cycle {rotation_state['rotation_cycle']})")
            logger.info(f"📊 Remaining in rotation: {len(rotation_state['available_tokens'])}/{rotation_state['total_tokens']} tokens")
            
            return selected_tokens
            
        except Exception as e:
            logger.error(f"Smart token selection error: {str(e)}")
            # Fallback to regular token loading
            try:
                from internal_storage import storage
                tokens = storage.load_tokens(server_name.upper())
                return tokens[:request_count] if tokens else []
            except:
                return []
    
    def get_rotation_stats(self, server_name: str) -> Dict:
        """Get rotation statistics for a server"""
        try:
            state = self.load_rotation_state(server_name)
            return {
                "server": server_name.upper(),
                "cycle": state.get("rotation_cycle", 0),
                "total_tokens": state.get("total_tokens", 0),
                "used_in_cycle": len(state.get("used_tokens", [])),
                "remaining_in_cycle": len(state.get("available_tokens", [])),
                "progress_percent": round((len(state.get("used_tokens", [])) / max(state.get("total_tokens", 1), 1)) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Failed to get rotation stats: {str(e)}")
            return {"error": str(e)}
    
    def reset_rotation(self, server_name: str):
        """Reset rotation for a server"""
        try:
            file_path = self.get_rotation_file_path(server_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.info(f"✅ Reset rotation for server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to reset rotation: {str(e)}")

# Global rotation manager
rotation_manager = SmartTokenRotation()