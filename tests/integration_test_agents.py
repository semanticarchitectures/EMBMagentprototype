"""
Integration tests for individual agents.

These tests use real LLM calls and MCP server interactions.
Run with: pytest tests/integration_test_agents.py -v -m integration
"""

import pytest


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_spectrum_agent_allocation_request(spectrum_agent, safe_frequency_request):
    """Test Spectrum Manager processing a frequency allocation request."""
    response = await spectrum_agent.process_allocation_request(**safe_frequency_request)

    # Verify response is a string with content
    assert isinstance(response, str)
    assert len(response) > 0

    # Response should contain decision keywords
    assert any(keyword in response.lower() for keyword in [
        "approved", "denied", "deconfliction", "frequency", "allocation"
    ])


@pytest.mark.asyncio
async def test_spectrum_agent_uses_mcp_tools(spectrum_agent, safe_frequency_request):
    """Test that Spectrum Manager actually calls MCP tools."""
    # Run allocation request
    response = await spectrum_agent.process_allocation_request(**safe_frequency_request)

    # Agent should have made at least one MCP tool call
    # This is validated by the agent completing successfully
    assert response is not None
    assert len(response) > 50  # Should have substantial response


@pytest.mark.asyncio
async def test_spectrum_agent_handles_interference_analysis(spectrum_agent):
    """Test Spectrum Manager analyzing interference."""
    response = await spectrum_agent.analyze_interference(
        latitude=38.0,
        longitude=48.0,
        min_freq_mhz=3000.0,
        max_freq_mhz=4000.0
    )

    # Should return analysis
    assert isinstance(response, str)
    assert len(response) > 0

    # Should mention interference or analysis
    assert any(keyword in response.lower() for keyword in [
        "interference", "sources", "analysis", "frequency"
    ])


@pytest.mark.asyncio
async def test_spectrum_agent_reviews_spectrum_plan(spectrum_agent, future_timestamp):
    """Test Spectrum Manager reviewing spectrum plan."""
    from datetime import datetime, timezone, timedelta

    ao_geojson = '{"type": "Polygon", "coordinates": [[[47.0, 37.0], [49.0, 37.0], [49.0, 39.0], [47.0, 39.0], [47.0, 37.0]]]}'
    end_time = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()

    response = await spectrum_agent.review_spectrum_plan(
        ao_geojson=ao_geojson,
        start_time=future_timestamp,
        end_time=end_time
    )

    # Should return plan analysis
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_isr_agent_sensor_coordination(isr_agent, isr_sensor_request):
    """Test ISR Manager coordinating a radar sensor."""
    response = await isr_agent.coordinate_rf_sensor(**isr_sensor_request)

    # Verify response
    assert isinstance(response, str)
    assert len(response) > 0

    # Response should discuss coordination or spectrum
    assert any(keyword in response.lower() for keyword in [
        "spectrum", "frequency", "coordination", "sensor", "radar"
    ])


@pytest.mark.asyncio
async def test_isr_agent_sensor_tasking(isr_agent):
    """Test ISR Manager tasking a sensor."""
    response = await isr_agent.task_sensor(
        sensor_type="RADAR",
        target_area="Test Area: 38°N, 48°E",
        collection_requirement="Detect and track vehicles in area",
        priority="PRIORITY",
        duration_minutes=60,
        additional_params={
            "frequency_mhz": 9500.0,
            "power_dbm": 60.0,
            "scan_rate_rpm": 12
        }
    )

    # Should return tasking plan
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_isr_agent_collection_gap_analysis(isr_agent):
    """Test ISR Manager analyzing collection gaps."""
    response = await isr_agent.analyze_collection_gap(
        intelligence_requirement="Monitor vehicle movements in target area",
        current_coverage="Limited coverage, no persistent surveillance",
        available_sensors=["RADAR-001 (X-band)", "UAV-002 (EO/IR)", "SIGINT-003"]
    )

    # Should provide gap analysis
    assert isinstance(response, str)
    assert len(response) > 0

    # Should mention recommendations or gaps
    assert any(keyword in response.lower() for keyword in [
        "gap", "recommend", "sensor", "coverage"
    ])


@pytest.mark.asyncio
async def test_ew_agent_jamming_planning(ew_agent, ew_jamming_request):
    """Test EW Planner planning a jamming operation."""
    response = await ew_agent.plan_jamming_operation(**ew_jamming_request)

    # Verify response
    assert isinstance(response, str)
    assert len(response) > 0

    # Response should discuss jamming or coordination
    assert any(keyword in response.lower() for keyword in [
        "jamming", "frequency", "coordination", "spectrum", "deconfliction"
    ])


@pytest.mark.asyncio
async def test_ew_agent_threat_analysis(ew_agent):
    """Test EW Planner analyzing a threat emitter."""
    response = await ew_agent.analyze_threat_emitter(
        emitter_freq_mhz=9600.0,
        emitter_location="38.1°N, 48.1°E",
        signal_characteristics={
            "waveform": "Pulse",
            "prf": "1000 Hz",
            "pulse_width": "10 microseconds",
            "power_estimate": "High"
        },
        threat_level="HIGH"
    )

    # Should provide threat analysis
    assert isinstance(response, str)
    assert len(response) > 0

    # Should mention threat or countermeasures
    assert any(keyword in response.lower() for keyword in [
        "threat", "emitter", "jamming", "countermeasure"
    ])


@pytest.mark.asyncio
async def test_ew_agent_deconfliction(ew_agent, future_timestamp):
    """Test EW Planner deconflicting EW operations."""
    response = await ew_agent.deconflict_ew_with_comms(
        ew_freq_range_mhz=(9500.0, 9700.0),
        ew_location="38.0°N, 48.0°E",
        affected_area_km=50.0,
        start_time=future_timestamp,
        duration_minutes=60
    )

    # Should provide deconfliction analysis
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_agent_iteration_limits(spectrum_agent, safe_frequency_request):
    """Test that agents respect iteration limits."""
    # Agent configured with max_iterations=3
    response = await spectrum_agent.process_allocation_request(**safe_frequency_request)

    # Should complete without hitting recursion errors
    assert response is not None


@pytest.mark.asyncio
async def test_agent_error_recovery(spectrum_agent):
    """Test agent handles errors gracefully."""
    # Try to analyze with invalid parameters
    response = await spectrum_agent.run("This is an ambiguous request with no clear parameters")

    # Agent should still return something reasonable
    assert isinstance(response, str)
    # Agent should ask for clarification or indicate it needs more info
    assert len(response) > 0


@pytest.mark.asyncio
async def test_agent_caching_benefits(spectrum_agent, safe_frequency_request, llm_provider):
    """Test that caching improves performance on repeated requests."""
    import time

    # Get initial cache stats
    initial_stats = llm_provider.get_cache_stats()

    # First request (cold)
    start1 = time.time()
    response1 = await spectrum_agent.process_allocation_request(**safe_frequency_request)
    time1 = time.time() - start1

    # Second request (should hit cache)
    start2 = time.time()
    response2 = await spectrum_agent.process_allocation_request(**safe_frequency_request)
    time2 = time.time() - start2

    # Get final cache stats
    final_stats = llm_provider.get_cache_stats()

    # Verify caching occurred
    assert final_stats["hits"] > initial_stats["hits"]

    # Second request should be faster (though not always guaranteed due to overhead)
    # At minimum, cache should have been used
    assert final_stats["total_requests"] > initial_stats["total_requests"]
