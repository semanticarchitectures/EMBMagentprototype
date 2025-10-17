"""
Tests for LLM Response Caching.
"""

import pytest
import time
from llm_abstraction.cache import LRUCache, configure_global_cache, get_global_cache, clear_global_cache
from llm_abstraction.provider import Message, MessageRole


def test_cache_initialization():
    """Test cache initialization."""
    cache = LRUCache(max_size=10, default_ttl_seconds=60)
    assert cache.max_size == 10
    assert cache.default_ttl_seconds == 60
    stats = cache.get_stats()
    assert stats["size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0


def test_cache_put_and_get():
    """Test storing and retrieving from cache."""
    cache = LRUCache(max_size=10)

    messages = [{"role": "user", "content": "test"}]
    response = {"content": "response"}

    # Store in cache
    cache.put(
        messages=messages,
        response=response,
        temperature=0.7,
        model="claude-3"
    )

    # Retrieve from cache
    cached_response = cache.get(
        messages=messages,
        temperature=0.7,
        model="claude-3"
    )

    assert cached_response == response


def test_cache_miss():
    """Test cache miss on non-existent key."""
    cache = LRUCache()

    messages = [{"role": "user", "content": "test"}]

    result = cache.get(
        messages=messages,
        temperature=0.7,
        model="claude-3"
    )

    assert result is None
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0


def test_cache_key_generation():
    """Test that different contexts generate different keys."""
    cache = LRUCache()

    messages1 = [{"role": "user", "content": "hello"}]
    messages2 = [{"role": "user", "content": "goodbye"}]
    response = {"content": "response"}

    # Store with first messages
    cache.put(messages=messages1, response=response, model="model1")

    # Try to get with different messages (should miss)
    result = cache.get(messages=messages2, model="model1")
    assert result is None

    # Try to get with same messages but different model (should miss)
    result = cache.get(messages=messages1, model="model2")
    assert result is None

    # Try to get with same messages and model (should hit)
    result = cache.get(messages=messages1, model="model1")
    assert result == response


def test_cache_with_tools():
    """Test cache with tool definitions."""
    cache = LRUCache()

    messages = [{"role": "user", "content": "test"}]
    tools = [{"name": "tool1", "description": "A tool"}]
    response = {"content": "response"}

    # Store with tools
    cache.put(messages=messages, response=response, tools=tools, model="model")

    # Get with tools (should hit)
    result = cache.get(messages=messages, tools=tools, model="model")
    assert result == response

    # Get without tools (should miss)
    result = cache.get(messages=messages, model="model")
    assert result is None


def test_cache_with_system_prompt():
    """Test cache with system prompt."""
    cache = LRUCache()

    messages = [{"role": "user", "content": "test"}]
    system = "You are a helpful assistant"
    response = {"content": "response"}

    # Store with system prompt
    cache.put(messages=messages, response=response, system=system, model="model")

    # Get with system prompt (should hit)
    result = cache.get(messages=messages, system=system, model="model")
    assert result == response

    # Get with different system prompt (should miss)
    result = cache.get(messages=messages, system="Different prompt", model="model")
    assert result is None


def test_cache_lru_eviction():
    """Test LRU eviction when cache is full."""
    cache = LRUCache(max_size=3)

    # Fill cache
    for i in range(3):
        cache.put(
            messages=[{"role": "user", "content": f"msg{i}"}],
            response={"content": f"response{i}"},
            model="model"
        )

    stats = cache.get_stats()
    assert stats["size"] == 3
    assert stats["evictions"] == 0

    # Add one more (should evict oldest)
    cache.put(
        messages=[{"role": "user", "content": "msg3"}],
        response={"content": "response3"},
        model="model"
    )

    stats = cache.get_stats()
    assert stats["size"] == 3
    assert stats["evictions"] == 1

    # First entry should be evicted
    result = cache.get(
        messages=[{"role": "user", "content": "msg0"}],
        model="model"
    )
    assert result is None


def test_cache_ttl_expiration():
    """Test TTL expiration."""
    cache = LRUCache(default_ttl_seconds=1)  # 1 second TTL

    messages = [{"role": "user", "content": "test"}]
    response = {"content": "response"}

    # Store in cache
    cache.put(messages=messages, response=response, model="model")

    # Immediately retrieve (should hit)
    result = cache.get(messages=messages, model="model")
    assert result == response

    # Wait for TTL to expire
    time.sleep(1.1)

    # Try to retrieve (should be expired)
    result = cache.get(messages=messages, model="model")
    assert result is None

    stats = cache.get_stats()
    assert stats["expirations"] == 1


def test_cache_custom_ttl():
    """Test custom TTL per entry."""
    cache = LRUCache(default_ttl_seconds=10)

    messages = [{"role": "user", "content": "test"}]
    response = {"content": "response"}

    # Store with custom short TTL
    cache.put(
        messages=messages,
        response=response,
        model="model",
        ttl_seconds=1
    )

    # Wait for custom TTL to expire
    time.sleep(1.1)

    # Should be expired
    result = cache.get(messages=messages, model="model")
    assert result is None


def test_cache_hit_tracking():
    """Test hit count tracking."""
    cache = LRUCache()

    messages = [{"role": "user", "content": "test"}]
    response = {"content": "response"}

    cache.put(messages=messages, response=response, model="model")

    # Get multiple times
    for _ in range(3):
        cache.get(messages=messages, model="model")

    stats = cache.get_stats()
    assert stats["hits"] == 3
    assert stats["misses"] == 0


def test_cache_hit_rate():
    """Test hit rate calculation."""
    cache = LRUCache()

    messages1 = [{"role": "user", "content": "test1"}]
    messages2 = [{"role": "user", "content": "test2"}]
    response = {"content": "response"}

    # Store one entry
    cache.put(messages=messages1, response=response, model="model")

    # 2 hits on stored entry
    cache.get(messages=messages1, model="model")
    cache.get(messages=messages1, model="model")

    # 2 misses on non-existent entry
    cache.get(messages=messages2, model="model")
    cache.get(messages=messages2, model="model")

    stats = cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 2
    assert stats["hit_rate_percent"] == 50.0


def test_cache_cleanup_expired():
    """Test manual cleanup of expired entries."""
    cache = LRUCache(default_ttl_seconds=1)

    # Add multiple entries
    for i in range(3):
        cache.put(
            messages=[{"role": "user", "content": f"msg{i}"}],
            response={"content": f"response{i}"},
            model="model"
        )

    assert cache.get_stats()["size"] == 3

    # Wait for expiration
    time.sleep(1.1)

    # Cleanup expired
    removed = cache.cleanup_expired()
    assert removed == 3
    assert cache.get_stats()["size"] == 0


def test_cache_clear():
    """Test clearing all cache entries."""
    cache = LRUCache()

    # Add entries
    for i in range(5):
        cache.put(
            messages=[{"role": "user", "content": f"msg{i}"}],
            response={"content": f"response{i}"},
            model="model"
        )

    assert cache.get_stats()["size"] == 5

    # Clear cache
    cache.clear()
    assert cache.get_stats()["size"] == 0


def test_global_cache():
    """Test global cache instance."""
    # Configure global cache
    configure_global_cache(max_size=50, default_ttl_seconds=300)

    # Get global cache
    cache1 = get_global_cache()
    cache2 = get_global_cache()

    # Should be same instance
    assert cache1 is cache2
    assert cache1.max_size == 50

    # Clear global cache
    clear_global_cache()
    assert cache1.get_stats()["size"] == 0


def test_temperature_rounding():
    """Test that temperature rounding works correctly."""
    cache = LRUCache()

    messages = [{"role": "user", "content": "test"}]
    response = {"content": "response"}

    # Store with temperature 0.7
    cache.put(messages=messages, response=response, temperature=0.7, model="model")

    # Get with slightly different temperature (should still match due to rounding)
    result = cache.get(messages=messages, temperature=0.700001, model="model")
    assert result == response


def test_cache_statistics_accuracy():
    """Test that cache statistics are accurate."""
    cache = LRUCache(max_size=5)

    messages_base = [{"role": "user", "content": "test"}]

    # Scenario: 3 unique entries, various accesses
    for i in range(3):
        cache.put(
            messages=[{"role": "user", "content": f"msg{i}"}],
            response={"content": f"response{i}"},
            model="model"
        )

    # 2 hits on entry 0
    cache.get(messages=[{"role": "user", "content": "msg0"}], model="model")
    cache.get(messages=[{"role": "user", "content": "msg0"}], model="model")

    # 3 misses on non-existent entry
    for _ in range(3):
        cache.get(messages=[{"role": "user", "content": "nonexistent"}], model="model")

    stats = cache.get_stats()
    assert stats["size"] == 3
    assert stats["hits"] == 2
    assert stats["misses"] == 3
    assert stats["total_requests"] == 5
    assert stats["hit_rate_percent"] == 40.0
