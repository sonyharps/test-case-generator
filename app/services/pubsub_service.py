import redis
import redis.asyncio as aioredis
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PubSubService:
    """
    Redis Pub/Sub service for real-time notifications

    Channels:
    - user:{user_id}:documents - Document processing updates
    - user:{user_id}:orchestrator - Test case generation updates
    """

    def __init__(self):
        """Initialize Redis connection for Pub/Sub"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis Pub/Sub connected successfully")
        except Exception as e:
            logger.error(f"Redis Pub/Sub connection failed: {e}")
            self.redis_client = None

    def publish_document_update(
        self,
        user_id: int,
        document_id: int,
        status: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        Publish document processing update

        Args:
            user_id: User ID
            document_id: Document ID
            status: Processing status (processing, completed, failed)
            data: Additional data to include

        Returns:
            True if published successfully
        """
        if not self.redis_client:
            return False

        try:
            channel = f"user:{user_id}:documents"
            message = {
                "type": "document_update",
                "document_id": document_id,
                "status": status,
                "timestamp": asyncio.get_event_loop().time(),
                **(data or {})
            }

            self.redis_client.publish(channel, json.dumps(message))
            logger.info(
                f"Published document update",
                user_id=user_id,
                document_id=document_id,
                status=status
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish document update: {e}")
            return False

    def publish_orchestrator_update(
        self,
        user_id: int,
        session_id: str,
        status: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        Publish test case generation update

        Args:
            user_id: User ID
            session_id: Session ID
            status: Generation status (started, completed, failed)
            data: Additional data

        Returns:
            True if published successfully
        """
        if not self.redis_client:
            return False

        try:
            channel = f"user:{user_id}:orchestrator"
            message = {
                "type": "orchestrator_update",
                "session_id": session_id,
                "status": status,
                "timestamp": asyncio.get_event_loop().time(),
                **(data or {})
            }

            self.redis_client.publish(channel, json.dumps(message))
            logger.info(
                f"Published orchestrator update",
                user_id=user_id,
                session_id=session_id,
                status=status
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish orchestrator update: {e}")
            return False

    async def subscribe_to_user_events(
        self,
        user_id: int
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to all user events (SSE stream)

        Args:
            user_id: User ID to subscribe to

        Yields:
            SSE-formatted event strings
        """
        if not self.redis_client:
            logger.error("Redis not available for subscriptions")
            return

        # Create async Redis connection for subscription
        async_redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

        pubsub = async_redis.pubsub()

        try:
            # Subscribe to user's channels
            channels = [
                f"user:{user_id}:documents",
                f"user:{user_id}:orchestrator"
            ]
            await pubsub.subscribe(*channels)

            logger.info(f"User {user_id} subscribed to real-time events")

            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"

            # Listen for messages asynchronously
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    # Format as SSE event
                    yield f"data: {message['data']}\n\n"

        except Exception as e:
            logger.error(f"Subscription error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        finally:
            await pubsub.unsubscribe()
            await pubsub.close()
            await async_redis.close()
            logger.info(f"User {user_id} unsubscribed from events")


# Singleton instance
pubsub_service = PubSubService()
