"""Cache management"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from cachetools import TTLCache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    created_at: datetime
    hit_count: int = 0
    
    def increment_hits(self) -> None:
        """Increment hit counter"""
        self.hit_count += 1


class CacheManager:
    """Manage forecast cache with TTL and statistics"""
    
    def __init__(self):
        self.cache: TTLCache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL_SECONDS
        )
        self.stale_cache: Dict[str, CacheEntry] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
        }
        logger.info(
            f"Cache initialized: max_size={settings.CACHE_MAX_SIZE}, "
            f"ttl={settings.CACHE_TTL_SECONDS}s"
        )
    
    def generate_key(self, lat: float, lon: float) -> str:
        """Generate cache key from coordinates"""
        return f"forecast:{lat:.4f}:{lon:.4f}"
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get item from cache"""
        if key in self.cache:
            entry = self.cache[key]
            entry.increment_hits()
            self.stats["hits"] += 1
            logger.debug(f"Cache hit: {key}")
            return entry
        
        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {key}")
        return None
    
    def get_stale(self, key: str) -> Optional[CacheEntry]:
        """Get stale data if available (expired cache)"""
        if key in self.stale_cache:
            entry = self.stale_cache[key]
            logger.info(f"Serving stale cache: {key}")
            return entry
        return None
    
    def set(self, key: str, data: Any) -> None:
        """Set item in cache"""
        entry = CacheEntry(
            data=data,
            created_at=datetime.utcnow()
        )
        
        # Save to stale cache before setting new entry
        if key in self.cache:
            self.stale_cache[key] = self.cache[key]
        
        self.cache[key] = entry
        logger.debug(f"Cache set: {key}")
    
    def get_size(self) -> int:
        """Get current cache size"""
        return len(self.cache)
    
    def get_hit_rate(self) -> Optional[float]:
        """Calculate cache hit rate percentage"""
        total = self.stats["hits"] + self.stats["misses"]
        if total == 0:
            return None
        return (self.stats["hits"] / total) * 100
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": self.get_size(),
            "max_size": settings.CACHE_MAX_SIZE,
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": self.get_hit_rate(),
        }


# Global cache instance
cache_manager = CacheManager()
