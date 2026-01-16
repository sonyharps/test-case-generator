"""
Capacity Tracking Service

Tracks active users and system capacity using Redis.
With batching (1 API call per generation), the system can support 7-30 concurrent users.
"""
import time
import uuid
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Capacity configuration based on batching optimization
# With 1 API call per generation (batched mode) vs 8 calls before:
# - Groq free tier: ~15 requests/min safe limit = ~15 concurrent users
# - GLM free tier: ~20 requests/min safe limit = ~20 concurrent users
# - Combined/Local: Much higher capacity
MAX_CONCURRENT_USERS = 20  # Conservative limit for free tier providers
USER_SESSION_TIMEOUT = 300  # 5 minutes - users are considered inactive after this


class CapacityService:
    """
    Track active users and system capacity using Redis.

    Uses a sorted set to track active user sessions with timestamps.
    """

    def __init__(self, redis_client=None):
        """Initialize capacity tracker with Redis client"""
        self.redis_client = redis_client
        self.enabled = redis_client is not None

    def _ensure_enabled(self):
        """Ensure Redis client is available by getting from cache_service"""
        if not self.enabled:
            try:
                from app.services.cache_service import cache_service
                if cache_service.redis_client:
                    self.redis_client = cache_service.redis_client
                    self.enabled = True
            except Exception:
                pass

    def start_user_session(self, user_id: int) -> str:
        """
        Start a new user session for capacity tracking.

        Args:
            user_id: The user's ID

        Returns:
            Session ID for this request
        """
        self._ensure_enabled()
        if not self.enabled:
            return str(uuid.uuid4())

        try:
            session_id = str(uuid.uuid4())
            key = f"capacity:user:{user_id}"
            now = time.time()

            # Store session with timestamp
            self.redis_client.hset(
                f"capacity:session:{session_id}",
                mapping={
                    "user_id": user_id,
                    "started_at": now,
                    "last_active": now
                }
            )
            # Set session timeout
            self.redis_client.expire(f"capacity:session:{session_id}", USER_SESSION_TIMEOUT)

            # Add to active sessions
            self.redis_client.zadd("capacity:active_sessions", {session_id: now})

            # Clean up old sessions first
            self._cleanup_old_sessions()

            active_count = self.get_active_user_count()
            logger.info(
                "user_session_started",
                user_id=user_id,
                session_id=session_id,
                active_users=active_count,
                capacity_percent=round(active_count / MAX_CONCURRENT_USERS * 100, 1)
            )

            return session_id

        except Exception as e:
            logger.error(f"capacity_service_error: {e}")
            return str(uuid.uuid4())

    def update_session_activity(self, session_id: str) -> None:
        """
        Update session activity timestamp.

        Args:
            session_id: The session ID to update
        """
        self._ensure_enabled()
        if not self.enabled:
            return

        try:
            now = time.time()
            self.redis_client.hset(
                f"capacity:session:{session_id}",
                "last_active",
                now
            )
            self.redis_client.zadd("capacity:active_sessions", {session_id: now})
        except Exception as e:
            logger.error(f"capacity_update_error: {e}")

    def end_user_session(self, session_id: str) -> None:
        """
        End a user session.

        Args:
            session_id: The session ID to end
        """
        self._ensure_enabled()
        if not self.enabled:
            return

        try:
            # Remove from active sessions
            self.redis_client.zrem("capacity:active_sessions", session_id)
            # Delete session data
            self.redis_client.delete(f"capacity:session:{session_id}")
        except Exception as e:
            logger.error(f"capacity_end_error: {e}")

    def get_active_user_count(self) -> int:
        """
        Get count of active users in the last timeout period.

        Returns:
            Number of active users
        """
        self._ensure_enabled()
        if not self.enabled:
            return 1  # Assume only current user if Redis is not available

        try:
            self._cleanup_old_sessions()
            return self.redis_client.zcard("capacity:active_sessions")
        except Exception as e:
            logger.error(f"capacity_count_error: {e}")
            return 1

    def get_capacity_stats(self) -> Dict[str, Any]:
        """
        Get current capacity statistics.

        Returns:
            Dictionary with capacity stats
        """
        self._ensure_enabled()
        active_count = self.get_active_user_count()
        capacity_percent = min(100, round(active_count / MAX_CONCURRENT_USERS * 100, 1))

        return {
            "active_users": active_count,
            "max_concurrent_users": MAX_CONCURRENT_USERS,
            "capacity_percent": capacity_percent,
            "available_slots": max(0, MAX_CONCURRENT_USERS - active_count),
            "status": "healthy" if capacity_percent < 80 else "busy" if capacity_percent < 95 else "full",
            "batching_enabled": True,
            "api_calls_per_generation": 1,  # Batching reduced from 8 to 1
            "optimization_note": "With batched mode (1 API call), system supports 7-30 concurrent users"
        }

    def _cleanup_old_sessions(self) -> None:
        """Remove sessions that have timed out"""
        if not self.enabled:
            return

        try:
            now = time.time()
            cutoff = now - USER_SESSION_TIMEOUT

            # Remove old sessions from sorted set
            old_sessions = self.redis_client.zrangebyscore(
                "capacity:active_sessions",
                0,
                cutoff
            )

            if old_sessions:
                for session_id in old_sessions:
                    self.redis_client.delete(f"capacity:session:{session_id}")

                self.redis_client.zremrangebyscore("capacity:active_sessions", 0, cutoff)

                if old_sessions:
                    logger.debug(f"cleaned_up_sessions", count=len(old_sessions))

        except Exception as e:
            logger.error(f"capacity_cleanup_error: {e}")


# Global instance (will get Redis client from cache_service when needed)
capacity_service = CapacityService(redis_client=None)
