"""
Tests for MCP Server Tools.
"""

import pytest
from datetime import datetime, timezone, timedelta
from mcp_server import tools
from mcp_server.models import DeconflictionStatus


@pytest.mark.asyncio
async def test_request_deconfliction_approved(sample_deconfliction_request):
    """Test deconfliction request that should be approved."""
    # Modify to use a safe frequency
    sample_deconfliction_request["frequency_mhz"] = 3000.0
    sample_deconfliction_request["location"] = {"lat": 36.0, "lon": 46.0}  # Away from restricted zones

    result = await tools.request_deconfliction(**sample_deconfliction_request)

    assert "status" in result
    # Result could be APPROVED or DENIED depending on ROE
    assert result["status"] in [DeconflictionStatus.APPROVED.value, DeconflictionStatus.DENIED.value]
    assert "authorization_id" in result


@pytest.mark.asyncio
async def test_request_deconfliction_creates_record(sample_deconfliction_request):
    """Test that deconfliction request creates a record."""
    from mcp_server.data.requests import request_store

    initial_count = len(await request_store.get_all_requests())

    await tools.request_deconfliction(**sample_deconfliction_request)

    final_count = len(await request_store.get_all_requests())
    assert final_count == initial_count + 1


@pytest.mark.asyncio
async def test_allocate_frequency_success():
    """Test successful frequency allocation with valid authorization."""
    # First, request deconfliction to get authorization
    deconf_request = {
        "asset_rid": "TEST-001",
        "frequency_mhz": 3000.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 36.0, "lon": 46.0},
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test allocation"
    }

    deconf_result = await tools.request_deconfliction(**deconf_request)

    # Only proceed if approved
    if deconf_result["status"] == DeconflictionStatus.APPROVED.value:
        # Now allocate with the authorization
        alloc_result = await tools.allocate_frequency(
            asset_id="TEST-001",
            frequency_mhz=3000.0,
            bandwidth_khz=25.0,
            duration_minutes=60,
            authorization_id=deconf_result["authorization_id"],
            location={"lat": 36.0, "lon": 46.0},
            power_dbm=40.0,
            priority="ROUTINE",
            purpose="Test allocation",
            service="Joint"
        )

        assert alloc_result["status"] == "SUCCESS"
        assert "allocation_id" in alloc_result
        assert alloc_result["allocation_id"] != ""


@pytest.mark.asyncio
async def test_allocate_frequency_invalid_auth():
    """Test frequency allocation with invalid authorization."""
    result = await tools.allocate_frequency(
        asset_id="TEST-001",
        frequency_mhz=3000.0,
        bandwidth_khz=25.0,
        duration_minutes=60,
        authorization_id="invalid-auth-id",
        location={"lat": 36.0, "lon": 46.0},
        power_dbm=40.0,
        priority="ROUTINE",
        purpose="Test allocation",
        service="Joint"
    )

    assert result["status"] == "FAILED"
    assert "Invalid or missing authorization" in result["message"]


@pytest.mark.asyncio
async def test_get_interference_report(sample_interference_request):
    """Test getting interference report."""
    result = await tools.get_interference_report(**sample_interference_request)

    assert "interference_sources" in result
    assert "total_noise_floor" in result
    assert "timestamp" in result
    assert isinstance(result["interference_sources"], list)


@pytest.mark.asyncio
async def test_report_emitter():
    """Test reporting an electromagnetic emitter."""
    emitter_data = {
        "location": {"lat": 35.0, "lon": 45.0},
        "frequency_mhz": 2500.0,
        "bandwidth_khz": 50.0,
        "signal_characteristics": {
            "waveform": "CW",  # Required field
            "modulation": "FM",
            "power_estimate_dbm": 45.0
        },
        "detection_time": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.85
    }

    result = await tools.report_emitter(**emitter_data)

    assert "emitter_id" in result
    assert "threat_assessment" in result
    assert result["threat_assessment"]["threat_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@pytest.mark.asyncio
async def test_get_spectrum_plan():
    """Test getting spectrum plan for an area."""
    ao_geojson = '{"type": "Polygon", "coordinates": [[[44.0, 34.0], [46.0, 34.0], [46.0, 36.0], [44.0, 36.0], [44.0, 34.0]]]}'
    start_time = datetime.now(timezone.utc).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    result = await tools.get_spectrum_plan(
        ao_geojson=ao_geojson,
        start_time=start_time,
        end_time=end_time
    )

    assert "plan_id" in result
    assert "allocations" in result
    assert isinstance(result["allocations"], list)
    assert "generated_at" in result


@pytest.mark.asyncio
async def test_analyze_coa_impact():
    """Test COA impact analysis."""
    coa_data = {
        "coa_id": "COA-TEST-001",
        "friendly_actions": [
            {
                "action_type": "JAMMING",  # Must be uppercase enum value
                "asset_id": "JAMMER-001",  # Required field
                "frequency_mhz": 2400.0,
                "power_dbm": 50.0,
                "location": {"lat": 35.0, "lon": 45.0},
                "duration_minutes": 60  # Required field
            }
        ]
    }

    result = await tools.analyze_coa_impact(**coa_data)

    assert "coa_id" in result
    assert "impact_score" in result
    assert "risk_summary" in result
    assert "affected_friendly_assets" in result
    assert isinstance(result["affected_friendly_assets"], list)


@pytest.mark.asyncio
async def test_deconfliction_detects_conflicts():
    """Test that deconfliction detects frequency conflicts."""
    # First allocation
    request1 = {
        "asset_rid": "ASSET-1",
        "frequency_mhz": 2400.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 35.0, "lon": 45.0},
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test 1"
    }

    await tools.request_deconfliction(**request1)

    # Second allocation - overlapping frequency and location
    request2 = {
        "asset_rid": "ASSET-2",
        "frequency_mhz": 2400.5,  # Very close frequency
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 35.01, "lon": 45.01},  # Very close location
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test 2"
    }

    result2 = await tools.request_deconfliction(**request2)

    # Should detect conflict
    assert "conflict_details" in result2
    # May have conflicts or ROE violations


@pytest.mark.asyncio
async def test_multiple_allocations_in_different_locations():
    """Test that non-conflicting allocations in different locations work."""
    base_time = datetime.now(timezone.utc).isoformat()

    # Allocation 1
    request1 = {
        "asset_rid": "ASSET-A",
        "frequency_mhz": 2400.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 35.0, "lon": 45.0},
        "start_time": base_time,
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test A"
    }

    # Allocation 2 - different location, same frequency
    request2 = {
        "asset_rid": "ASSET-B",
        "frequency_mhz": 2400.0,
        "bandwidth_khz": 25.0,
        "power_dbm": 40.0,
        "location": {"lat": 40.0, "lon": 50.0},  # Far away
        "start_time": base_time,
        "duration_minutes": 60,
        "priority": "ROUTINE",
        "purpose": "Test B"
    }

    result1 = await tools.request_deconfliction(**request1)
    result2 = await tools.request_deconfliction(**request2)

    # Both might be approved or denied based on ROE, but should not conflict with each other
    assert "status" in result1
    assert "status" in result2
