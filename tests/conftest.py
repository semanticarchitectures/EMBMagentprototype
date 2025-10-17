"""
Pytest configuration and fixtures for EMBM-J DS tests.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from mcp_server.models import Location, Priority, ServiceBranch


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_location() -> Location:
    """Sample location for testing."""
    return Location(lat=35.0, lon=45.0)


@pytest.fixture
def sample_allocation_params() -> Dict[str, Any]:
    """Sample frequency allocation parameters."""
    return {
        "asset_id": "TEST-ASSET-001",
        "frequency_mhz": 2400.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "latitude": 35.0,
        "longitude": 45.0,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test allocation"
    }


@pytest.fixture
def sample_deconfliction_request() -> Dict[str, Any]:
    """Sample deconfliction request parameters."""
    return {
        "asset_rid": "TEST-ASSET-001",
        "frequency_mhz": 2400.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 35.0, "lon": 45.0},
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test deconfliction"
    }


@pytest.fixture
def sample_interference_request() -> Dict[str, Any]:
    """Sample interference report request."""
    return {
        "location": {"lat": 35.0, "lon": 45.0},
        "frequency_range_mhz": {"min": 2300.0, "max": 2500.0}
    }


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def mcp_server_url():
    """Get MCP server URL from environment."""
    import os
    return os.getenv("EMBM_SERVER_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
async def llm_provider():
    """Get LLM provider for testing."""
    from llm_abstraction import get_global_registry, configure_global_cache

    # Configure cache for integration tests
    configure_global_cache(max_size=50, default_ttl_seconds=300)

    registry = get_global_registry()
    provider = registry.get_provider()
    return provider


@pytest.fixture
async def mcp_client(mcp_server_url):
    """Create MCP client connected to server."""
    from mcp_client import MCPClient

    async with MCPClient(mcp_server_url) as client:
        # Verify server is healthy
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("MCP server is not available")
        yield client


@pytest.fixture
async def spectrum_agent(llm_provider, mcp_client):
    """Create Spectrum Manager agent."""
    from agents import SpectrumManagerAgent

    agent = SpectrumManagerAgent(
        llm_provider=llm_provider,
        mcp_client=mcp_client,
        max_iterations=5  # Increased for integration tests
    )
    return agent


@pytest.fixture
async def isr_agent(llm_provider, mcp_client):
    """Create ISR Manager agent."""
    from agents import ISRManagerAgent

    agent = ISRManagerAgent(
        llm_provider=llm_provider,
        mcp_client=mcp_client,
        max_iterations=5  # Increased for integration tests
    )
    return agent


@pytest.fixture
async def ew_agent(llm_provider, mcp_client):
    """Create EW Planner agent."""
    from agents import EWPlannerAgent

    agent = EWPlannerAgent(
        llm_provider=llm_provider,
        mcp_client=mcp_client,
        max_iterations=5  # Increased for integration tests
    )
    return agent


@pytest.fixture
async def message_broker():
    """Create message broker for multi-agent tests."""
    from broker import MessageBroker

    broker = MessageBroker(max_history=100)
    return broker


@pytest.fixture
def future_timestamp():
    """Get a timestamp 2 hours in the future."""
    from datetime import timedelta
    return (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()


@pytest.fixture
def safe_frequency_request(future_timestamp):
    """Create a safe frequency request that should pass ROE."""
    return {
        "asset_id": "TEST-INTEGRATION-001",
        "frequency_mhz": 3500.0,  # Safe frequency
        "bandwidth_khz": 25.0,
        "power_dbm": 35.0,
        "latitude": 38.0,  # Away from restricted zones
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Integration test frequency allocation"
    }


@pytest.fixture
def isr_sensor_request(future_timestamp):
    """Create an ISR sensor coordination request."""
    return {
        "sensor_id": "RADAR-TEST-001",
        "frequency_mhz": 9500.0,  # X-band radar
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 120,
        "purpose": "Integration test ISR collection"
    }


@pytest.fixture
def ew_jamming_request(future_timestamp):
    """Create an EW jamming operation request."""
    return {
        "threat_emitter_freq_mhz": 9600.0,
        "threat_location": "38.1°N, 48.1°E",
        "jammer_location": "38.0°N, 48.0°E",
        "jamming_technique": "spot",
        "power_dbm": 55.0,
        "duration_minutes": 120,
        "priority": "PRIORITY",
        "justification": "Integration test EW jamming operation"
    }
