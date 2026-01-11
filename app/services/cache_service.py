import redis
import json
import hashlib
from typing import Optional, Any, Dict
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service for LLM responses

    Caches expensive operations like:
    - Test case generation
    - Requirement extraction
    - Document embeddings
    """

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,  # Auto-decode bytes to strings
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = settings.CACHE_ENABLED
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
            self.enabled = False

    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key from parameters

        Args:
            prefix: Key namespace (e.g., 'orchestrator', 'embedding')
            params: Dictionary of parameters to hash

        Returns:
            Cache key like 'orchestrator:a3f5b2c1...'
        """
        # Sort params for consistent hashing
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True)

        # Create hash
        hash_obj = hashlib.sha256(param_str.encode())
        hash_hex = hash_obj.hexdigest()[:16]  # First 16 chars

        return f"{prefix}:{hash_hex}"

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Get cached value

        Args:
            prefix: Cache namespace
            params: Parameters to generate key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(prefix, params)
            cached = self.redis_client.get(cache_key)

            if cached:
                logger.info(f"Cache HIT: {cache_key}")
                return json.loads(cached)
            else:
                logger.info(f"Cache MISS: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        prefix: str,
        params: Dict[str, Any],
        value: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value with TTL

        Args:
            prefix: Cache namespace
            params: Parameters to generate key
            value: Value to cache
            ttl: Time-to-live in seconds (default: from settings)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(prefix, params)
            ttl = ttl or settings.CACHE_TTL_SECONDS

            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(value)
            )

            logger.info(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, prefix: str, params: Dict[str, Any]) -> bool:
        """Delete cached value"""
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(prefix, params)
            result = self.redis_client.delete(cache_key)
            logger.info(f"Cache DELETE: {cache_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Redis key pattern (e.g., 'orchestrator:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}

        try:
            info = self.redis_client.info('stats')
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses

            return {
                "enabled": True,
                "total_keys": self.redis_client.dbsize(),
                "hits": hits,
                "misses": misses,
                "hit_rate": round((hits / total * 100) if total > 0 else 0.0, 2)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}


# Singleton instance
cache_service = CacheService()
