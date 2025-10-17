"""
Message Broker for Multi-Agent Communication.

Provides pub/sub messaging between agents, enabling:
- Agent-to-agent communication
- Broadcast messages
- Request-response patterns
- Message persistence and replay
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio
import uuid
import structlog


logger = structlog.get_logger()


class MessageType(str, Enum):
    """Type of message."""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"


@dataclass
class Message:
    """Message sent between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.BROADCAST
    topic: str = ""
    sender: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None  # For request-response patterns
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """Subscription to a topic."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    subscriber: str = ""
    callback: Optional[Callable] = None
    filter_func: Optional[Callable[[Message], bool]] = None


class MessageBroker:
    """
    Async message broker for agent-to-agent communication.

    Features:
    - Topic-based pub/sub
    - Message filtering
    - Request-response patterns
    - Message history
    - Async message delivery
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize the message broker.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._message_history: List[Message] = []
        self._max_history = max_history
        self._pending_responses: Dict[str, asyncio.Future] = {}

        logger.info("message_broker_initialized", max_history=max_history)

    async def publish(
        self,
        topic: str,
        content: Dict[str, Any],
        sender: str,
        message_type: MessageType = MessageType.BROADCAST,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Publish a message to a topic.

        Args:
            topic: Topic to publish to
            content: Message content
            sender: Agent sending the message
            message_type: Type of message
            correlation_id: Optional correlation ID for request-response
            metadata: Optional metadata

        Returns:
            The published message
        """
        message = Message(
            type=message_type,
            topic=topic,
            sender=sender,
            content=content,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )

        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

        logger.info(
            "message_published",
            message_id=message.id,
            topic=topic,
            sender=sender,
            type=message_type.value
        )

        # Deliver to subscribers
        await self._deliver_message(message)

        return message

    async def subscribe(
        self,
        topic: str,
        subscriber: str,
        callback: Optional[Callable] = None,
        filter_func: Optional[Callable[[Message], bool]] = None
    ) -> Subscription:
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            subscriber: Agent subscribing
            callback: Optional async callback function
            filter_func: Optional filter function

        Returns:
            Subscription object
        """
        subscription = Subscription(
            topic=topic,
            subscriber=subscriber,
            callback=callback,
            filter_func=filter_func
        )

        if topic not in self._subscriptions:
            self._subscriptions[topic] = []

        self._subscriptions[topic].append(subscription)

        logger.info(
            "subscription_created",
            subscription_id=subscription.id,
            topic=topic,
            subscriber=subscriber
        )

        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if subscription was found and removed
        """
        for topic, subs in self._subscriptions.items():
            for sub in subs:
                if sub.id == subscription_id:
                    subs.remove(sub)
                    logger.info(
                        "subscription_removed",
                        subscription_id=subscription_id,
                        topic=topic
                    )
                    return True

        return False

    async def request(
        self,
        topic: str,
        content: Dict[str, Any],
        sender: str,
        timeout: float = 30.0
    ) -> Message:
        """
        Send a request and wait for a response.

        Args:
            topic: Topic to send request to
            content: Request content
            sender: Agent sending the request
            timeout: Timeout in seconds

        Returns:
            Response message

        Raises:
            asyncio.TimeoutError: If no response within timeout
        """
        correlation_id = str(uuid.uuid4())

        # Create future for response
        response_future = asyncio.Future()
        self._pending_responses[correlation_id] = response_future

        # Publish request
        await self.publish(
            topic=topic,
            content=content,
            sender=sender,
            message_type=MessageType.REQUEST,
            correlation_id=correlation_id
        )

        logger.info(
            "request_sent",
            correlation_id=correlation_id,
            topic=topic,
            sender=sender
        )

        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(
                "request_timeout",
                correlation_id=correlation_id,
                topic=topic
            )
            raise
        finally:
            # Clean up
            self._pending_responses.pop(correlation_id, None)

    async def respond(
        self,
        original_message: Message,
        content: Dict[str, Any],
        sender: str
    ) -> Message:
        """
        Respond to a request message.

        Args:
            original_message: The request message to respond to
            content: Response content
            sender: Agent sending the response

        Returns:
            Response message
        """
        if not original_message.correlation_id:
            raise ValueError("Cannot respond to message without correlation_id")

        response = await self.publish(
            topic=f"{original_message.topic}.response",
            content=content,
            sender=sender,
            message_type=MessageType.RESPONSE,
            correlation_id=original_message.correlation_id
        )

        # If there's a pending future, resolve it
        if original_message.correlation_id in self._pending_responses:
            future = self._pending_responses[original_message.correlation_id]
            if not future.done():
                future.set_result(response)

        logger.info(
            "response_sent",
            correlation_id=original_message.correlation_id,
            sender=sender
        )

        return response

    async def get_history(
        self,
        topic: Optional[str] = None,
        sender: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get message history.

        Args:
            topic: Optional topic filter
            sender: Optional sender filter
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        messages = self._message_history

        if topic:
            messages = [m for m in messages if m.topic == topic]

        if sender:
            messages = [m for m in messages if m.sender == sender]

        return messages[-limit:]

    async def _deliver_message(self, message: Message):
        """
        Deliver a message to all subscribers.

        Args:
            message: Message to deliver
        """
        subscriptions = self._subscriptions.get(message.topic, [])

        delivery_tasks = []
        for sub in subscriptions:
            # Apply filter if present
            if sub.filter_func and not sub.filter_func(message):
                continue

            # Call callback if present
            if sub.callback:
                task = asyncio.create_task(self._safe_callback(sub, message))
                delivery_tasks.append(task)

        # Wait for all deliveries
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

    async def _safe_callback(self, subscription: Subscription, message: Message):
        """
        Safely execute a callback.

        Args:
            subscription: Subscription with callback
            message: Message to deliver
        """
        try:
            if asyncio.iscoroutinefunction(subscription.callback):
                await subscription.callback(message)
            else:
                subscription.callback(message)

            logger.debug(
                "message_delivered",
                message_id=message.id,
                subscriber=subscription.subscriber
            )
        except Exception as e:
            logger.error(
                "callback_error",
                subscriber=subscription.subscriber,
                message_id=message.id,
                error=str(e)
            )

    def get_subscription_count(self, topic: Optional[str] = None) -> int:
        """
        Get number of subscriptions.

        Args:
            topic: Optional topic to filter by

        Returns:
            Number of subscriptions
        """
        if topic:
            return len(self._subscriptions.get(topic, []))

        return sum(len(subs) for subs in self._subscriptions.values())

    def get_topics(self) -> List[str]:
        """
        Get list of all topics with subscriptions.

        Returns:
            List of topic names
        """
        return list(self._subscriptions.keys())
