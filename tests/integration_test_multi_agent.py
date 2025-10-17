"""
Integration tests for multi-agent coordination.

These tests verify that multiple agents can coordinate through the message broker.
Run with: pytest tests/integration_test_multi_agent.py -v -m integration
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_isr_spectrum_coordination(isr_agent, spectrum_agent, message_broker, future_timestamp):
    """Test ISR agent coordinating with Spectrum Manager for sensor frequency."""
    # ISR agent needs spectrum for a radar sensor
    sensor_request = {
        "sensor_id": "RADAR-COORD-001",
        "frequency_mhz": 9500.0,
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 120,
        "purpose": "Multi-agent coordination test - ISR sensor"
    }

    # Set broker for both agents
    isr_agent.broker = message_broker
    spectrum_agent.broker = message_broker

    # Subscribe spectrum agent to coordination requests
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # ISR agent requests coordination
    response = await isr_agent.coordinate_rf_sensor(**sensor_request)

    # Should have coordinated successfully
    assert isinstance(response, str)
    assert len(response) > 0
    assert any(keyword in response.lower() for keyword in [
        "spectrum", "frequency", "coordination", "approved", "deconfliction"
    ])


@pytest.mark.asyncio
async def test_ew_spectrum_coordination(ew_agent, spectrum_agent, message_broker, future_timestamp):
    """Test EW agent coordinating with Spectrum Manager for jamming operation."""
    jamming_request = {
        "threat_emitter_freq_mhz": 9600.0,
        "threat_location": "38.1°N, 48.1°E",
        "jammer_location": "38.0°N, 48.0°E",
        "jamming_technique": "spot",
        "power_dbm": 55.0,
        "duration_minutes": 120,
        "priority": "PRIORITY",
        "justification": "Multi-agent test - EW jamming coordination"
    }

    # Set broker for both agents
    ew_agent.broker = message_broker
    spectrum_agent.broker = message_broker

    # Subscribe spectrum agent to coordination requests
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # EW agent plans jamming operation
    response = await ew_agent.plan_jamming_operation(**jamming_request)

    # Should have coordinated with spectrum manager
    assert isinstance(response, str)
    assert len(response) > 0
    assert any(keyword in response.lower() for keyword in [
        "jamming", "spectrum", "coordination", "deconfliction"
    ])


@pytest.mark.asyncio
async def test_isr_ew_deconfliction(isr_agent, ew_agent, spectrum_agent, message_broker, future_timestamp):
    """Test ISR and EW agents deconflicting operations through Spectrum Manager."""
    # ISR wants to use 9500 MHz for radar
    isr_request = {
        "sensor_id": "RADAR-DECONF-001",
        "frequency_mhz": 9500.0,
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 120,
        "purpose": "ISR collection - deconfliction test"
    }

    # EW wants to jam at 9550 MHz (close frequency, same location)
    ew_request = {
        "threat_emitter_freq_mhz": 9550.0,
        "threat_location": "38.05°N, 48.05°E",
        "jammer_location": "38.0°N, 48.0°E",
        "jamming_technique": "spot",
        "power_dbm": 55.0,
        "duration_minutes": 120,
        "priority": "PRIORITY",
        "justification": "EW jamming - deconfliction test"
    }

    # Set broker for all agents
    isr_agent.broker = message_broker
    ew_agent.broker = message_broker
    spectrum_agent.broker = message_broker

    # Subscribe agents to relevant topics
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")
    await message_broker.subscribe("coordination.isr", "isr_agent")
    await message_broker.subscribe("coordination.ew", "ew_agent")

    # Both agents coordinate
    isr_response, ew_response = await asyncio.gather(
        isr_agent.coordinate_rf_sensor(**isr_request),
        ew_agent.plan_jamming_operation(**ew_request)
    )

    # Both should complete
    assert isinstance(isr_response, str)
    assert isinstance(ew_response, str)
    assert len(isr_response) > 0
    assert len(ew_response) > 0


@pytest.mark.asyncio
async def test_message_broker_coordination(message_broker):
    """Test basic message broker coordination between simulated agents."""
    received_messages = []

    async def agent1_callback(message):
        received_messages.append(("agent1", message))

    async def agent2_callback(message):
        received_messages.append(("agent2", message))

    # Subscribe two agents to same topic
    await message_broker.subscribe("test.coordination", "agent1", callback=agent1_callback)
    await message_broker.subscribe("test.coordination", "agent2", callback=agent2_callback)

    # Publish a coordination message
    msg = await message_broker.publish(
        topic="test.coordination",
        content={"action": "coordinate", "data": "test data"},
        sender="coordinator"
    )

    # Wait for callbacks
    await asyncio.sleep(0.1)

    # Both agents should have received the message
    assert len(received_messages) == 2
    assert received_messages[0][0] == "agent1"
    assert received_messages[1][0] == "agent2"
    assert received_messages[0][1].content["action"] == "coordinate"


@pytest.mark.asyncio
async def test_request_response_coordination(message_broker):
    """Test request-response pattern for agent coordination."""
    async def responder_callback(message):
        if message.type.value == "request":  # Lowercase to match MessageType enum
            await message_broker.respond(
                original_message=message,
                content={"status": "approved", "allocation_id": "TEST-123"},
                sender="spectrum_agent"
            )

    # Subscribe responder
    await message_broker.subscribe("coordination.request", "spectrum_agent",
                                   callback=responder_callback)

    # Send request and wait for response
    response = await message_broker.request(
        topic="coordination.request",
        content={"frequency_mhz": 3500.0, "action": "allocate"},
        sender="isr_agent",
        timeout=2.0
    )

    # Should receive response
    assert response is not None
    assert response.type.value == "response"  # Lowercase to match MessageType enum
    assert response.content["status"] == "approved"
    assert response.sender == "spectrum_agent"


@pytest.mark.asyncio
async def test_three_agent_coordination_scenario(isr_agent, ew_agent, spectrum_agent,
                                                 message_broker, future_timestamp):
    """Test complex three-agent coordination scenario.

    Scenario:
    1. ISR agent needs radar frequency at 9500 MHz
    2. EW agent plans jamming at 9600 MHz (different frequency, should be OK)
    3. Spectrum Manager coordinates both
    """
    # Set broker for all agents
    isr_agent.broker = message_broker
    ew_agent.broker = message_broker
    spectrum_agent.broker = message_broker

    # Subscribe to coordination topics
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")
    await message_broker.subscribe("coordination.isr", "isr_agent")
    await message_broker.subscribe("coordination.ew", "ew_agent")

    # ISR request
    isr_request = {
        "sensor_id": "RADAR-SCENARIO-001",
        "frequency_mhz": 9500.0,
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 120,
        "purpose": "Three-agent scenario - ISR collection"
    }

    # EW request (different frequency to avoid conflict)
    ew_request = {
        "threat_emitter_freq_mhz": 9700.0,
        "threat_location": "38.2°N, 48.2°E",
        "jammer_location": "38.0°N, 48.0°E",
        "jamming_technique": "spot",
        "power_dbm": 55.0,
        "duration_minutes": 120,
        "priority": "PRIORITY",
        "justification": "Three-agent scenario - EW jamming"
    }

    # Execute both requests in parallel
    results = await asyncio.gather(
        isr_agent.coordinate_rf_sensor(**isr_request),
        ew_agent.plan_jamming_operation(**ew_request),
        return_exceptions=True
    )

    # Check results
    isr_response = results[0]
    ew_response = results[1]

    # Both should complete successfully
    assert not isinstance(isr_response, Exception), f"ISR failed: {isr_response}"
    assert not isinstance(ew_response, Exception), f"EW failed: {ew_response}"
    assert isinstance(isr_response, str)
    assert isinstance(ew_response, str)
    assert len(isr_response) > 0
    assert len(ew_response) > 0


@pytest.mark.asyncio
async def test_message_filtering(message_broker):
    """Test message filtering in broker subscriptions."""
    high_priority_messages = []
    all_messages = []

    async def high_priority_callback(message):
        high_priority_messages.append(message)

    async def all_messages_callback(message):
        all_messages.append(message)

    # Subscribe with filter for high priority
    await message_broker.subscribe(
        "operations",
        "high_priority_agent",
        callback=high_priority_callback,
        message_filter=lambda m: m.content.get("priority") == "HIGH"
    )

    # Subscribe to all messages
    await message_broker.subscribe(
        "operations",
        "all_agent",
        callback=all_messages_callback
    )

    # Publish low priority message
    await message_broker.publish(
        topic="operations",
        content={"priority": "LOW", "data": "test1"},
        sender="test"
    )

    # Publish high priority message
    await message_broker.publish(
        topic="operations",
        content={"priority": "HIGH", "data": "test2"},
        sender="test"
    )

    # Wait for callbacks
    await asyncio.sleep(0.1)

    # Filtered subscriber should only see high priority
    assert len(high_priority_messages) == 1
    assert high_priority_messages[0].content["priority"] == "HIGH"

    # All messages subscriber should see both
    assert len(all_messages) == 2


@pytest.mark.asyncio
async def test_concurrent_coordination_requests(spectrum_agent, message_broker, future_timestamp):
    """Test spectrum agent handling multiple concurrent coordination requests."""
    spectrum_agent.broker = message_broker
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # Create multiple allocation requests
    requests = []
    for i in range(3):
        request = {
            "asset_id": f"CONCURRENT-{i:03d}",
            "frequency_mhz": 3500.0 + (i * 100),  # Different frequencies
            "bandwidth_khz": 25.0,
            "power_dbm": 40.0,
            "latitude": 38.0 + (i * 0.5),  # Different locations
            "longitude": 48.0 + (i * 0.5),
            "start_time": future_timestamp,
            "duration_minutes": 60,
            "priority": "ROUTINE",
            "purpose": f"Concurrent test {i}"
        }
        requests.append(request)

    # Process all requests concurrently
    results = await asyncio.gather(
        *[spectrum_agent.process_allocation_request(**req) for req in requests],
        return_exceptions=True
    )

    # All should complete
    for i, result in enumerate(results):
        assert not isinstance(result, Exception), f"Request {i} failed: {result}"
        assert isinstance(result, str)
        assert len(result) > 0
