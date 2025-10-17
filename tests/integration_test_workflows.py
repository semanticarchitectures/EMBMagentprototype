"""
End-to-end workflow integration tests.

These tests verify complete workflows from start to finish.
Run with: pytest tests/integration_test_workflows.py -v -m integration
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_frequency_allocation_workflow(spectrum_agent, mcp_client, future_timestamp):
    """Test complete frequency allocation workflow end-to-end."""
    # Request allocation
    allocation_request = {
        "asset_id": "WORKFLOW-001",
        "frequency_mhz": 3500.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "End-to-end workflow test"
    }

    # Process allocation through agent
    response = await spectrum_agent.process_allocation_request(**allocation_request)

    # Verify agent response
    assert isinstance(response, str)
    assert len(response) > 0
    assert any(keyword in response.lower() for keyword in [
        "approved", "denied", "deconfliction", "allocation"
    ])

    # Verify allocation was recorded in MCP server (if approved)
    if "approved" in response.lower():
        # Check interference report to see if allocation appears
        interference_result = await mcp_client.call_tool(
            "get_interference_report",
            {
                "latitude": 38.0,
                "longitude": 48.0,
                "min_freq_mhz": 3400.0,
                "max_freq_mhz": 3600.0
            }
        )
        assert "interference_sources" in interference_result


@pytest.mark.asyncio
async def test_isr_sensor_tasking_workflow(isr_agent, spectrum_agent, message_broker, future_timestamp):
    """Test complete ISR sensor tasking and coordination workflow."""
    # Set up agents with broker
    isr_agent.broker = message_broker
    spectrum_agent.broker = message_broker
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # ISR agent tasks sensor
    sensor_task = {
        "sensor_type": "RADAR",
        "target_area": "38°N, 48°E",
        "collection_requirement": "Detect and track vehicles",
        "priority": "PRIORITY",
        "duration_minutes": 120,
        "additional_params": {
            "frequency_mhz": 9500.0,
            "power_dbm": 60.0,
            "scan_rate_rpm": 12
        }
    }

    # Execute tasking
    response = await isr_agent.task_sensor(**sensor_task)

    # Should complete with tasking plan
    assert isinstance(response, str)
    assert len(response) > 0
    assert any(keyword in response.lower() for keyword in [
        "sensor", "tasking", "radar", "frequency", "spectrum"
    ])


@pytest.mark.asyncio
async def test_ew_threat_response_workflow(ew_agent, spectrum_agent, mcp_client,
                                           message_broker, future_timestamp):
    """Test complete EW threat detection and response workflow."""
    # Set up agents with broker
    ew_agent.broker = message_broker
    spectrum_agent.broker = message_broker
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")
    await message_broker.subscribe("coordination.ew", "ew_agent")

    # Step 1: Report threat emitter
    emitter_report = {
        "location": {"lat": 38.1, "lon": 48.1},
        "frequency_mhz": 9600.0,
        "bandwidth_khz": 50.0,
        "signal_characteristics": {
            "waveform": "Pulse",
            "prf": "1000 Hz",
            "pulse_width": "10 microseconds",
            "power_estimate_dbm": 65.0
        },
        "detection_time": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.9
    }

    emitter_result = await mcp_client.call_tool("report_emitter", emitter_report)
    assert "emitter_id" in emitter_result
    assert "threat_assessment" in emitter_result

    # Step 2: Analyze threat
    threat_analysis = await ew_agent.analyze_threat_emitter(
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

    assert isinstance(threat_analysis, str)
    assert len(threat_analysis) > 0

    # Step 3: Plan jamming response
    jamming_plan = await ew_agent.plan_jamming_operation(
        threat_emitter_freq_mhz=9600.0,
        threat_location="38.1°N, 48.1°E",
        jammer_location="38.0°N, 48.0°E",
        jamming_technique="spot",
        power_dbm=55.0,
        duration_minutes=120,
        priority="IMMEDIATE",
        justification="Response to high threat emitter"
    )

    assert isinstance(jamming_plan, str)
    assert len(jamming_plan) > 0


@pytest.mark.asyncio
async def test_multi_domain_operation_workflow(isr_agent, ew_agent, spectrum_agent,
                                               message_broker, mcp_client, future_timestamp):
    """Test complex multi-domain operation with all three agents.

    Scenario:
    1. ISR collection requirement identified
    2. Spectrum Manager allocates frequency for radar
    3. EW identifies nearby threat emitter
    4. All agents coordinate deconfliction
    """
    # Set up agents with broker
    isr_agent.broker = message_broker
    ew_agent.broker = message_broker
    spectrum_agent.broker = message_broker

    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")
    await message_broker.subscribe("coordination.isr", "isr_agent")
    await message_broker.subscribe("coordination.ew", "ew_agent")

    # Step 1: ISR identifies collection gap
    gap_analysis = await isr_agent.analyze_collection_gap(
        intelligence_requirement="Track enemy vehicle movements in AO",
        current_coverage="Limited coverage, no persistent surveillance",
        available_sensors=["RADAR-001 (X-band)", "UAV-002 (EO/IR)"]
    )

    assert isinstance(gap_analysis, str)
    assert len(gap_analysis) > 0

    # Step 2: ISR tasks radar sensor (needs spectrum coordination)
    isr_coordination = isr_agent.coordinate_rf_sensor(
        sensor_id="RADAR-001",
        frequency_mhz=9500.0,
        bandwidth_khz=100.0,
        power_dbm=60.0,
        latitude=38.0,
        longitude=48.0,
        start_time=future_timestamp,
        duration_minutes=120,
        purpose="Multi-domain operation - ISR collection"
    )

    # Step 3: EW detects threat and plans jamming (needs spectrum coordination)
    ew_jamming = ew_agent.plan_jamming_operation(
        threat_emitter_freq_mhz=9650.0,
        threat_location="38.15°N, 48.15°E",
        jammer_location="38.0°N, 48.0°E",
        jamming_technique="spot",
        power_dbm=55.0,
        duration_minutes=120,
        priority="PRIORITY",
        justification="Multi-domain operation - EW support"
    )

    # Execute both coordination tasks
    isr_result, ew_result = await asyncio.gather(
        isr_coordination,
        ew_jamming,
        return_exceptions=True
    )

    # Verify both completed
    assert not isinstance(isr_result, Exception), f"ISR failed: {isr_result}"
    assert not isinstance(ew_result, Exception), f"EW failed: {ew_result}"
    assert isinstance(isr_result, str) and len(isr_result) > 0
    assert isinstance(ew_result, str) and len(ew_result) > 0

    # Step 4: Get spectrum plan for area of operations
    ao_geojson = '{\"type\": \"Polygon\", \"coordinates\": [[[47.0, 37.0], [49.0, 37.0], [49.0, 39.0], [47.0, 39.0], [47.0, 37.0]]]}'
    end_time = (datetime.fromisoformat(future_timestamp.replace('Z', '+00:00')) + timedelta(hours=2)).isoformat()

    spectrum_plan = await spectrum_agent.review_spectrum_plan(
        ao_geojson=ao_geojson,
        start_time=future_timestamp,
        end_time=end_time
    )

    assert isinstance(spectrum_plan, str)
    assert len(spectrum_plan) > 0


@pytest.mark.asyncio
async def test_coa_analysis_workflow(mcp_client, spectrum_agent):
    """Test Course of Action (COA) analysis workflow."""
    # Define a COA with friendly actions
    coa_data = {
        "coa_id": "COA-WORKFLOW-001",
        "friendly_actions": [
            {
                "action_type": "JAMMING",
                "asset_id": "JAMMER-001",
                "frequency_mhz": 2400.0,
                "power_dbm": 50.0,
                "location": {"lat": 35.0, "lon": 45.0},
                "duration_minutes": 60
            },
            {
                "action_type": "COMMUNICATION",
                "asset_id": "RADIO-001",
                "frequency_mhz": 2500.0,
                "power_dbm": 40.0,
                "location": {"lat": 35.1, "lon": 45.1},
                "duration_minutes": 120
            }
        ]
    }

    # Analyze COA impact
    coa_result = await mcp_client.call_tool("analyze_coa_impact", coa_data)

    # Verify analysis
    assert "coa_id" in coa_result
    assert coa_result["coa_id"] == "COA-WORKFLOW-001"
    assert "impact_score" in coa_result
    assert "risk_summary" in coa_result
    assert "affected_friendly_assets" in coa_result
    assert isinstance(coa_result["affected_friendly_assets"], list)


@pytest.mark.asyncio
async def test_dynamic_replanning_workflow(spectrum_agent, isr_agent, message_broker,
                                           mcp_client, future_timestamp):
    """Test dynamic replanning when initial allocation is denied."""
    # Set up agents
    isr_agent.broker = message_broker
    spectrum_agent.broker = message_broker
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # Request potentially problematic frequency (in restricted band)
    initial_request = {
        "sensor_id": "RADAR-REPLAN-001",
        "frequency_mhz": 2400.0,  # May be restricted or congested
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": future_timestamp,
        "duration_minutes": 120,
        "purpose": "Replanning workflow test"
    }

    # Try coordination
    response = await isr_agent.coordinate_rf_sensor(**initial_request)

    # Agent should handle any issues (denial, conflict, etc.) gracefully
    assert isinstance(response, str)
    assert len(response) > 0

    # If denied, agent should suggest alternatives or explain reasoning
    if "denied" in response.lower() or "conflict" in response.lower():
        # Agent handled denial appropriately
        assert any(keyword in response.lower() for keyword in [
            "alternative", "conflict", "restricted", "roe"
        ])


@pytest.mark.asyncio
async def test_spectrum_monitoring_workflow(mcp_client, spectrum_agent):
    """Test continuous spectrum monitoring and interference detection workflow."""
    # Get baseline interference
    baseline = await mcp_client.call_tool(
        "get_interference_report",
        {
            "latitude": 38.0,
            "longitude": 48.0,
            "min_freq_mhz": 3000.0,
            "max_freq_mhz": 4000.0
        }
    )

    assert "interference_sources" in baseline
    assert "total_noise_floor" in baseline
    baseline_sources = len(baseline["interference_sources"])

    # Analyze interference
    analysis = await spectrum_agent.analyze_interference(
        latitude=38.0,
        longitude=48.0,
        min_freq_mhz=3000.0,
        max_freq_mhz=4000.0
    )

    assert isinstance(analysis, str)
    assert len(analysis) > 0


@pytest.mark.asyncio
async def test_time_sensitive_coordination(spectrum_agent, isr_agent, message_broker):
    """Test time-sensitive coordination with near-term start time."""
    # Set up agents
    isr_agent.broker = message_broker
    spectrum_agent.broker = message_broker
    await message_broker.subscribe("coordination.spectrum", "spectrum_agent")

    # Request with very near-term start (5 minutes from now)
    near_future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    urgent_request = {
        "sensor_id": "RADAR-URGENT-001",
        "frequency_mhz": 9500.0,
        "bandwidth_khz": 100.0,
        "power_dbm": 60.0,
        "latitude": 38.0,
        "longitude": 48.0,
        "start_time": near_future,
        "duration_minutes": 30,
        "purpose": "Time-sensitive coordination test"
    }

    # Should process quickly
    import time
    start_time = time.time()
    response = await isr_agent.coordinate_rf_sensor(**urgent_request)
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 30 seconds)
    assert elapsed < 30
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_large_area_spectrum_plan(spectrum_agent, mcp_client, future_timestamp):
    """Test spectrum planning for large area of operations."""
    # Large AO covering significant area
    large_ao = '{\"type\": \"Polygon\", \"coordinates\": [[[44.0, 34.0], [50.0, 34.0], [50.0, 40.0], [44.0, 40.0], [44.0, 34.0]]]}'
    end_time = (datetime.fromisoformat(future_timestamp.replace('Z', '+00:00')) + timedelta(hours=6)).isoformat()

    # Get spectrum plan
    plan_result = await mcp_client.call_tool(
        "get_spectrum_plan",
        {
            "ao_geojson": large_ao,
            "start_time": future_timestamp,
            "end_time": end_time
        }
    )

    assert "plan_id" in plan_result
    assert "allocations" in plan_result
    assert isinstance(plan_result["allocations"], list)

    # Agent reviews plan
    review = await spectrum_agent.review_spectrum_plan(
        ao_geojson=large_ao,
        start_time=future_timestamp,
        end_time=end_time
    )

    assert isinstance(review, str)
    assert len(review) > 0
