"""Time-to-live cache implementation with size limits."""

import time
from typing import Dict, Generic, Optional, Tuple, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Time-to-live cache implementation."""

    def __init__(self, ttl_seconds: int, max_size: int) -> None:
        """Initialize cache with TTL and size limits.

        Args:
            ttl_seconds: Time-to-live in seconds
            max_size: Maximum number of cache entries

        """
        self._cache: Dict[str, Tuple[T, float]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size

    def get(self, key: str) -> Optional[T]:
        """Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing

        """
        self._evict_expired()
        if key in self._cache:
            value, expiry_time = self._cache[key]
            if time.time() < expiry_time:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: T) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache

        """
        self._evict_expired()
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_oldest()
        expiry_time = time.time() + self.ttl_seconds
        self._cache[key] = (value, expiry_time)

    def _evict_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._cache.items() if current_time >= expiry_time
        ]
        for key in expired_keys:
            del self._cache[key]

    def _evict_oldest(self) -> None:
        """Remove oldest entry when cache is full."""
        if self._cache:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
