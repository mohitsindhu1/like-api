"""
High-performance caching system for API optimization
"""
import time
import threading
from typing import Any, Optional, Dict
import json

class PerformanceCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry['expires_at']:
                    return entry['value']
                else:
                    # Expired, remove it
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set cached value with TTL in seconds (default 5 minutes)"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
    
    def delete(self, key: str) -> None:
        """Delete cached value"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if current_time >= entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
                
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values() 
                if current_time >= entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'memory_usage_estimate': len(str(self._cache))
            }

# Global cache instances for different data types
player_cache = PerformanceCache()
token_cache = PerformanceCache()  
server_cache = PerformanceCache()
config_cache = PerformanceCache()

def cached_player_info(uid: str, server: str):
    """Decorator for caching player info"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"player:{uid}:{server}"
            cached_result = player_cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Cache successful results for 10 minutes
            if result is not None:
                player_cache.set(cache_key, result, ttl=600)
            
            return result
        return wrapper
    return decorator

def cached_token_validation(token: str, server: str):
    """Cache token validation results"""
    cache_key = f"token_valid:{token}:{server}"
    cached_result = token_cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    # If not in cache, assume it needs validation
    return None

def cache_token_validation(token: str, server: str, is_valid: bool, ttl: int = 1800):
    """Cache token validation result (30 minutes default)"""
    cache_key = f"token_valid:{token}:{server}"
    token_cache.set(cache_key, is_valid, ttl=ttl)

def cached_server_detection(uid: str):
    """Cache server detection results"""
    cache_key = f"server_detect:{uid}"
    return server_cache.get(cache_key)

def cache_server_detection(uid: str, server: str, ttl: int = 3600):
    """Cache server detection result (1 hour default)"""
    cache_key = f"server_detect:{uid}"
    server_cache.set(cache_key, server, ttl=ttl)

def get_all_cache_stats():
    """Get stats for all caches"""
    return {
        'player_cache': player_cache.get_stats(),
        'token_cache': token_cache.get_stats(), 
        'server_cache': server_cache.get_stats(),
        'config_cache': config_cache.get_stats()
    }

def cleanup_all_caches():
    """Cleanup expired entries in all caches"""
    total_removed = 0
    total_removed += player_cache.cleanup_expired()
    total_removed += token_cache.cleanup_expired()
    total_removed += server_cache.cleanup_expired()
    total_removed += config_cache.cleanup_expired()
    return total_removed