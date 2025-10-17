"""
LLM Response Caching.

Provides caching for LLM responses to improve performance and reduce costs.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import structlog
from collections import OrderedDict


logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """Cache entry for an LLM response."""
    key: str
    response: Any
    timestamp: datetime
    ttl_seconds: int
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > self.ttl_seconds

    def is_valid(self) -> bool:
        """Check if cache entry is valid (not expired)."""
        return not self.is_expired()


class LRUCache:
    """
    LRU (Least Recently Used) cache for LLM responses.

    Features:
    - Size-based eviction (LRU)
    - TTL (time-to-live) for entries
    - Hit/miss tracking
    - Cache statistics
    """

    def __init__(self, max_size: int = 100, default_ttl_seconds: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries
            default_ttl_seconds: Default TTL for cache entries (1 hour)
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }

        logger.info(
            "llm_cache_initialized",
            max_size=max_size,
            default_ttl=default_ttl_seconds
        )

    def _generate_cache_key(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        model: str = ""
    ) -> str:
        """
        Generate a cache key from request parameters.

        Args:
            messages: Conversation messages
            tools: Tool definitions
            system: System prompt
            temperature: Temperature setting
            model: Model name

        Returns:
            Cache key (hash)
        """
        # Create a deterministic representation
        key_data = {
            "messages": messages,
            "tools": tools if tools else [],
            "system": system if system else "",
            "temperature": round(temperature, 2),  # Round to avoid float precision issues
            "model": model
        }

        # Sort keys for consistency
        key_json = json.dumps(key_data, sort_keys=True)

        # Generate SHA256 hash
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()

        return key_hash

    def get(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        model: str = ""
    ) -> Optional[Any]:
        """
        Get a cached response.

        Args:
            messages: Conversation messages
            tools: Tool definitions
            system: System prompt
            temperature: Temperature setting
            model: Model name

        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_cache_key(messages, tools, system, temperature, model)

        if key not in self._cache:
            self._stats["misses"] += 1
            logger.debug("cache_miss", key=key[:8])
            return None

        entry = self._cache[key]

        # Check if expired
        if entry.is_expired():
            self._stats["expirations"] += 1
            del self._cache[key]
            logger.debug("cache_expired", key=key[:8])
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        # Update hit count
        entry.hits += 1
        self._stats["hits"] += 1

        logger.info(
            "cache_hit",
            key=key[:8],
            hits=entry.hits,
            age_seconds=int((datetime.now(timezone.utc) - entry.timestamp).total_seconds())
        )

        return entry.response

    def put(
        self,
        messages: List[Dict[str, Any]],
        response: Any,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        model: str = "",
        ttl_seconds: Optional[int] = None
    ):
        """
        Store a response in the cache.

        Args:
            messages: Conversation messages
            response: LLM response to cache
            tools: Tool definitions
            system: System prompt
            temperature: Temperature setting
            model: Model name
            ttl_seconds: Optional custom TTL (uses default if not provided)
        """
        key = self._generate_cache_key(messages, tools, system, temperature, model)

        # Evict LRU entry if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            evicted_key, evicted_entry = self._cache.popitem(last=False)
            self._stats["evictions"] += 1
            logger.debug(
                "cache_eviction",
                evicted_key=evicted_key[:8],
                evicted_hits=evicted_entry.hits
            )

        # Create cache entry
        entry = CacheEntry(
            key=key,
            response=response,
            timestamp=datetime.now(timezone.utc),
            ttl_seconds=ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds,
            hits=0
        )

        self._cache[key] = entry

        logger.debug("cache_store", key=key[:8], ttl=entry.ttl_seconds)

    def clear(self):
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("cache_cleared", entries_cleared=count)

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        if expired_keys:
            logger.info("cache_cleanup", expired_count=len(expired_keys))

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0 else 0
        )

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "total_requests": total_requests
        }

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific cache entry.

        Args:
            key: Cache key

        Returns:
            Entry information or None if not found
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        age = (datetime.now(timezone.utc) - entry.timestamp).total_seconds()

        return {
            "key": key,
            "hits": entry.hits,
            "age_seconds": int(age),
            "ttl_seconds": entry.ttl_seconds,
            "expires_in_seconds": int(entry.ttl_seconds - age),
            "is_valid": entry.is_valid()
        }


# Global cache instance (can be configured per provider if needed)
_global_cache: Optional[LRUCache] = None


def get_global_cache() -> LRUCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = LRUCache(max_size=100, default_ttl_seconds=3600)
    return _global_cache


def configure_global_cache(max_size: int = 100, default_ttl_seconds: int = 3600):
    """
    Configure the global cache.

    Args:
        max_size: Maximum number of entries
        default_ttl_seconds: Default TTL for cache entries
    """
    global _global_cache
    _global_cache = LRUCache(max_size=max_size, default_ttl_seconds=default_ttl_seconds)
    logger.info("global_cache_configured", max_size=max_size, ttl=default_ttl_seconds)


def clear_global_cache():
    """Clear the global cache."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
