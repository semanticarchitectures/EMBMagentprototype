"""
Tests for the Message Broker.
"""

import pytest
import asyncio
from broker import MessageBroker, Message, MessageType


@pytest.mark.asyncio
async def test_broker_initialization():
    """Test message broker initialization."""
    broker = MessageBroker(max_history=100)
    assert broker._max_history == 100
    assert len(broker._message_history) == 0
    assert broker.get_subscription_count() == 0


@pytest.mark.asyncio
async def test_publish_message():
    """Test publishing a message."""
    broker = MessageBroker()

    message = await broker.publish(
        topic="test.topic",
        content={"data": "test"},
        sender="test_sender",
        message_type=MessageType.BROADCAST
    )

    assert message.topic == "test.topic"
    assert message.sender == "test_sender"
    assert message.content == {"data": "test"}
    assert message.type == MessageType.BROADCAST
    assert len(broker._message_history) == 1


@pytest.mark.asyncio
async def test_subscribe_and_receive():
    """Test subscribing to a topic and receiving messages."""
    broker = MessageBroker()
    received_messages = []

    async def callback(message: Message):
        received_messages.append(message)

    # Subscribe
    subscription = await broker.subscribe(
        topic="test.topic",
        subscriber="test_subscriber",
        callback=callback
    )

    assert subscription.topic == "test.topic"
    assert subscription.subscriber == "test_subscriber"
    assert broker.get_subscription_count() == 1

    # Publish message
    await broker.publish(
        topic="test.topic",
        content={"data": "test"},
        sender="test_sender"
    )

    # Wait for async delivery
    await asyncio.sleep(0.1)

    # Check message was received
    assert len(received_messages) == 1
    assert received_messages[0].content == {"data": "test"}


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test multiple subscribers to same topic."""
    broker = MessageBroker()
    received_by_sub1 = []
    received_by_sub2 = []

    async def callback1(message: Message):
        received_by_sub1.append(message)

    async def callback2(message: Message):
        received_by_sub2.append(message)

    # Subscribe two subscribers
    await broker.subscribe("test.topic", "subscriber1", callback1)
    await broker.subscribe("test.topic", "subscriber2", callback2)

    assert broker.get_subscription_count() == 2
    assert broker.get_subscription_count("test.topic") == 2

    # Publish message
    await broker.publish(
        topic="test.topic",
        content={"data": "broadcast"},
        sender="sender"
    )

    # Wait for async delivery
    await asyncio.sleep(0.1)

    # Both subscribers should receive
    assert len(received_by_sub1) == 1
    assert len(received_by_sub2) == 1


@pytest.mark.asyncio
async def test_message_filtering():
    """Test message filtering with filter function."""
    broker = MessageBroker()
    received_messages = []

    async def callback(message: Message):
        received_messages.append(message)

    # Only receive messages with "important" in content
    def filter_func(message: Message) -> bool:
        return message.content.get("important", False)

    await broker.subscribe(
        topic="test.topic",
        subscriber="filtered_subscriber",
        callback=callback,
        filter_func=filter_func
    )

    # Publish important message
    await broker.publish(
        topic="test.topic",
        content={"important": True, "data": "critical"},
        sender="sender"
    )

    # Publish non-important message
    await broker.publish(
        topic="test.topic",
        content={"important": False, "data": "routine"},
        sender="sender"
    )

    # Wait for async delivery
    await asyncio.sleep(0.1)

    # Only important message should be received
    assert len(received_messages) == 1
    assert received_messages[0].content["data"] == "critical"


@pytest.mark.asyncio
async def test_request_response_pattern():
    """Test request-response messaging pattern."""
    broker = MessageBroker()

    # Subscriber that responds to requests
    async def request_handler(message: Message):
        if message.type == MessageType.REQUEST:
            await broker.respond(
                original_message=message,
                content={"result": "processed"},
                sender="responder"
            )

    await broker.subscribe(
        topic="request.topic",
        subscriber="responder",
        callback=request_handler
    )

    # Send request and wait for response
    response = await broker.request(
        topic="request.topic",
        content={"action": "process"},
        sender="requester",
        timeout=2.0
    )

    assert response.type == MessageType.RESPONSE
    assert response.content["result"] == "processed"


@pytest.mark.asyncio
async def test_request_timeout():
    """Test request timeout when no response."""
    broker = MessageBroker()

    # No subscriber to respond
    with pytest.raises(asyncio.TimeoutError):
        await broker.request(
            topic="nonexistent.topic",
            content={"action": "process"},
            sender="requester",
            timeout=0.5
        )


@pytest.mark.asyncio
async def test_unsubscribe():
    """Test unsubscribing from a topic."""
    broker = MessageBroker()
    received_messages = []

    async def callback(message: Message):
        received_messages.append(message)

    subscription = await broker.subscribe(
        topic="test.topic",
        subscriber="test_subscriber",
        callback=callback
    )

    assert broker.get_subscription_count() == 1

    # Unsubscribe
    result = await broker.unsubscribe(subscription.id)
    assert result is True
    assert broker.get_subscription_count() == 0

    # Publish message after unsubscribe
    await broker.publish(
        topic="test.topic",
        content={"data": "test"},
        sender="sender"
    )

    await asyncio.sleep(0.1)

    # No messages should be received
    assert len(received_messages) == 0


@pytest.mark.asyncio
async def test_message_history():
    """Test message history tracking."""
    broker = MessageBroker(max_history=5)

    # Publish multiple messages
    for i in range(7):
        await broker.publish(
            topic=f"topic{i}",
            content={"index": i},
            sender="sender"
        )

    # Only last 5 should be kept
    assert len(broker._message_history) == 5

    # Get history
    history = await broker.get_history(limit=3)
    assert len(history) == 3
    assert history[-1].content["index"] == 6  # Most recent


@pytest.mark.asyncio
async def test_get_history_with_filters():
    """Test getting history with topic and sender filters."""
    broker = MessageBroker()

    # Publish messages from different senders and topics
    await broker.publish("topic1", {"data": 1}, "sender1")
    await broker.publish("topic2", {"data": 2}, "sender1")
    await broker.publish("topic1", {"data": 3}, "sender2")

    # Filter by topic
    history = await broker.get_history(topic="topic1")
    assert len(history) == 2

    # Filter by sender
    history = await broker.get_history(sender="sender1")
    assert len(history) == 2

    # Filter by both
    history = await broker.get_history(topic="topic1", sender="sender1")
    assert len(history) == 1
    assert history[0].content["data"] == 1


@pytest.mark.asyncio
async def test_get_topics():
    """Test getting list of topics with subscriptions."""
    broker = MessageBroker()

    async def callback(message: Message):
        pass

    await broker.subscribe("topic1", "sub1", callback)
    await broker.subscribe("topic2", "sub2", callback)
    await broker.subscribe("topic1", "sub3", callback)

    topics = broker.get_topics()
    assert len(topics) == 2
    assert "topic1" in topics
    assert "topic2" in topics
