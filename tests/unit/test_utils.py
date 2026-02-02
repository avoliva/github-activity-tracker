import time

from app.utils.cache import TTLCache


class TestTTLCache:
    """Unit tests for TTLCache."""

    def test_cache_get_set(self) -> None:
        """Test basic cache get/set operations."""
        cache = TTLCache(ttl_seconds=60, max_size=100)

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_cache_get_missing_key(self) -> None:
        """Test getting a non-existent key returns None."""
        cache = TTLCache(ttl_seconds=60, max_size=100)

        result = cache.get("nonexistent")

        assert result is None

    def test_cache_expiration(self) -> None:
        """Test cache TTL expiration."""
        cache = TTLCache(ttl_seconds=1, max_size=100)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(1.1)
        result = cache.get("key1")

        assert result is None

    def test_cache_max_size(self) -> None:
        """Test cache size limit enforcement."""
        cache = TTLCache(ttl_seconds=60, max_size=2)

        cache.set("key1", "value1")
        time.sleep(0.01)  # Small delay to ensure different expiry times
        cache.set("key2", "value2")
        time.sleep(0.01)
        cache.set("key3", "value3")

        # key1 should be evicted (oldest expiry time)
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_clear(self) -> None:
        """Test cache clearing."""
        cache = TTLCache(ttl_seconds=60, max_size=100)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_overwrite_existing_key(self) -> None:
        """Test overwriting an existing key updates the value."""
        cache = TTLCache(ttl_seconds=60, max_size=100)

        cache.set("key1", "value1")
        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"
