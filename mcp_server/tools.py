"""
MCP Server tool implementations.

These functions implement the MCP tools that agents can call to interact
with the EMBM-J DS system.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import structlog
import math

from .models import (
    DeconflictionRequest,
    DeconflictionResponse,
    DeconflictionStatus,
    FrequencyAllocation,
    AllocationResult,
    Emitter,
    ThreatAssessment,
    ThreatType,
    ThreatLevel,
    COAImpactAnalysis,
    FriendlyAction,
    AffectedAsset,
    EnemyEffects,
    InterferenceReport,
    InterferenceSource,
    SpectrumPlan,
    Location,
    Priority,
)
from .data.allocations import allocation_store
from .data.emitters import emitter_store
from .data.requests import request_store
from .business_logic.deconfliction import DeconflictionEngine
from .business_logic.roe_engine import ROEEngine
from .business_logic.propagation import PropagationModel

logger = structlog.get_logger()

# Initialize business logic engines
deconfliction_engine = DeconflictionEngine()
roe_engine = ROEEngine()
propagation_model = PropagationModel()


async def get_spectrum_plan(
    ao_geojson: str,
    start_time: str,
    end_time: str
) -> Dict[str, Any]:
    """
    Retrieve current spectrum allocation plan for an area and time period.

    Args:
        ao_geojson: Area of operations as GeoJSON polygon string
        start_time: Start time (ISO format)
        end_time: End time (ISO format)

    Returns:
        Spectrum plan with all allocations
    """
    logger.info("get_spectrum_plan", ao=ao_geojson, start=start_time, end=end_time)

    # Parse times
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    # Get all active allocations in the time range
    # For simplicity, we get all allocations active at start_time
    # A more sophisticated implementation would filter by geographic area
    allocations = await allocation_store.get_active_allocations(start_dt)

    # Filter allocations that overlap with the requested time range
    filtered_allocations = [
        alloc for alloc in allocations
        if alloc.end_time >= start_dt and alloc.start_time <= end_dt
    ]

    # Create spectrum plan
    plan = SpectrumPlan(
        ao_geojson=ao_geojson,
        start_time=start_dt,
        end_time=end_dt,
        allocations=filtered_allocations
    )

    return plan.model_dump(mode='json')


async def request_deconfliction(
    asset_rid: str,
    frequency_mhz: float,
    bandwidth_khz: float,
    power_dbm: float,
    location: Dict[str, float],
    start_time: str,
    duration_minutes: int,
    priority: str,
    purpose: str
) -> Dict[str, Any]:
    """
    Request spectrum deconfliction for a proposed frequency allocation.

    Args:
        asset_rid: Requesting asset RID
        frequency_mhz: Requested frequency in MHz
        bandwidth_khz: Bandwidth in kHz
        power_dbm: Transmit power in dBm
        location: Location dict with 'lat', 'lon' keys
        start_time: Start time (ISO format)
        duration_minutes: Duration in minutes
        priority: Priority level (ROUTINE, PRIORITY, IMMEDIATE, FLASH)
        purpose: Purpose description

    Returns:
        Deconfliction response with status and details
    """
    logger.info(
        "request_deconfliction",
        asset=asset_rid,
        freq=frequency_mhz,
        priority=priority
    )

    # Create request object
    request = DeconflictionRequest(
        asset_rid=asset_rid,
        frequency_mhz=frequency_mhz,
        bandwidth_khz=bandwidth_khz,
        power_dbm=power_dbm,
        location=Location(**location),
        start_time=datetime.fromisoformat(start_time.replace('Z', '+00:00')),
        duration_minutes=duration_minutes,
        priority=Priority(priority),
        purpose=purpose
    )

    # Store the request
    await request_store.add_request(request)

    # Check ROE constraints
    current_flash_count = len([
        r for r in await request_store.get_all_requests()
        if r.priority == Priority.FLASH
    ])
    roe_violations = roe_engine.validate_request(request, current_flash_count)

    if roe_violations:
        response = DeconflictionResponse(
            request_id=request.request_id,
            status=DeconflictionStatus.DENIED,
            justification=f"ROE violations: {'; '.join(roe_violations)}"
        )
        await request_store.add_response(response)
        logger.warning("request_denied_roe", violations=roe_violations)
        return response.model_dump(mode='json')

    # Get existing allocations for conflict checking
    request_end = request.start_time + timedelta(minutes=duration_minutes)
    allocations = await allocation_store.get_active_allocations(request.start_time)

    # Check for conflicts
    conflicts = deconfliction_engine.check_conflicts(request, allocations)

    # Determine status
    if not conflicts:
        status = DeconflictionStatus.APPROVED
        justification = "No conflicts detected. Request approved."
        authorization_id = str(uuid.uuid4())
    elif deconfliction_engine.evaluate_priority_override(request, conflicts):
        status = DeconflictionStatus.APPROVED
        justification = f"High priority override: {request.priority.value}. Request approved despite {len(conflicts)} low-severity conflict(s)."
        authorization_id = str(uuid.uuid4())
    else:
        status = DeconflictionStatus.CONFLICT
        justification = f"Conflicts detected: {len(conflicts)} issue(s) found."
        authorization_id = None

    # Generate alternative frequencies if denied/conflict
    alternative_frequencies = []
    if status != DeconflictionStatus.APPROVED:
        alternative_frequencies = deconfliction_engine.suggest_alternatives(
            request,
            allocations,
            num_suggestions=3
        )

    # Create response
    response = DeconflictionResponse(
        request_id=request.request_id,
        status=status,
        conflict_details=conflicts,
        alternative_frequencies=alternative_frequencies,
        justification=justification,
        authorization_id=authorization_id
    )

    await request_store.add_response(response)

    logger.info(
        "deconfliction_complete",
        request_id=request.request_id,
        status=status.value,
        conflicts=len(conflicts)
    )

    return response.model_dump(mode='json')


async def allocate_frequency(
    asset_id: str,
    frequency_mhz: float,
    bandwidth_khz: float,
    duration_minutes: int,
    authorization_id: str,
    location: Dict[str, float],
    power_dbm: float,
    priority: str,
    purpose: str,
    service: str = "Joint"
) -> Dict[str, Any]:
    """
    Allocate a frequency after successful deconfliction.

    Args:
        asset_id: Asset ID
        frequency_mhz: Frequency in MHz
        bandwidth_khz: Bandwidth in kHz
        duration_minutes: Duration in minutes
        authorization_id: Authorization ID from deconfliction approval
        location: Location dict
        power_dbm: Power in dBm
        priority: Priority level
        purpose: Purpose description
        service: Service branch

    Returns:
        Allocation result
    """
    logger.info("allocate_frequency", asset=asset_id, auth=authorization_id)

    # Verify authorization exists
    all_responses = await request_store.get_all_responses()
    authorized = any(
        r.authorization_id == authorization_id and
        r.status == DeconflictionStatus.APPROVED
        for r in all_responses
    )

    if not authorized:
        result = AllocationResult(
            allocation_id="",
            status="FAILED",
            message=f"Invalid or missing authorization ID: {authorization_id}"
        )
        logger.error("allocation_failed", reason="invalid_authorization")
        return result.model_dump(mode='json')

    # Create allocation
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=duration_minutes)

    allocation = FrequencyAllocation(
        asset_id=asset_id,
        frequency_mhz=frequency_mhz,
        bandwidth_khz=bandwidth_khz,
        location=Location(**location),
        start_time=start_time,
        end_time=end_time,
        service=service,
        priority=Priority(priority),
        power_dbm=power_dbm,
        purpose=purpose
    )

    # Store allocation
    await allocation_store.add(allocation)

    result = AllocationResult(
        allocation_id=allocation.allocation_id,
        status="SUCCESS",
        expires_at=end_time,
        message=f"Frequency {frequency_mhz} MHz allocated to {asset_id}"
    )

    logger.info("allocation_success", allocation_id=allocation.allocation_id)

    return result.model_dump(mode='json')


async def report_emitter(
    location: Dict[str, float],
    frequency_mhz: float,
    bandwidth_khz: float,
    signal_characteristics: Dict[str, Any],
    detection_time: str,
    confidence: float
) -> Dict[str, Any]:
    """
    Report a detected electromagnetic emitter.

    Args:
        location: Location dict
        frequency_mhz: Frequency in MHz
        bandwidth_khz: Bandwidth in kHz
        signal_characteristics: Signal characteristics dict
        detection_time: Detection time (ISO format)
        confidence: Detection confidence 0-1

    Returns:
        Emitter ID and threat assessment
    """
    logger.info("report_emitter", freq=frequency_mhz, confidence=confidence)

    # Create emitter
    from .models import SignalCharacteristics

    emitter = Emitter(
        location=Location(**location),
        frequency_mhz=frequency_mhz,
        bandwidth_khz=bandwidth_khz,
        signal_characteristics=SignalCharacteristics(**signal_characteristics),
        detection_time=datetime.fromisoformat(detection_time.replace('Z', '+00:00')),
        confidence=confidence
    )

    # Perform basic threat assessment (simplified)
    threat_assessment = _assess_threat(emitter)
    emitter.threat_assessment = threat_assessment

    # Store emitter
    await emitter_store.add(emitter)

    logger.info(
        "emitter_reported",
        emitter_id=emitter.emitter_id,
        threat_level=threat_assessment.threat_level.value
    )

    return {
        "emitter_id": emitter.emitter_id,
        "threat_assessment": threat_assessment.model_dump(mode='json')
    }


async def analyze_coa_impact(
    coa_id: str,
    friendly_actions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze the impact of a Course of Action on the electromagnetic environment.

    Args:
        coa_id: COA identifier
        friendly_actions: List of friendly action dicts

    Returns:
        Impact analysis
    """
    logger.info("analyze_coa_impact", coa_id=coa_id, num_actions=len(friendly_actions))

    # Convert to FriendlyAction objects
    actions = [FriendlyAction(**action) for action in friendly_actions]

    # Check ROE compliance
    roe_violations = roe_engine.validate_coa_actions(actions)

    # Analyze impact on friendly assets
    affected_assets = await _analyze_friendly_impact(actions)

    # Analyze impact on enemy systems
    enemy_effects = await _analyze_enemy_impact(actions)

    # Calculate overall impact score
    impact_score = _calculate_impact_score(affected_assets, enemy_effects, roe_violations)

    # Generate risk summary
    risk_summary = _generate_risk_summary(affected_assets, enemy_effects, roe_violations)

    analysis = COAImpactAnalysis(
        coa_id=coa_id,
        impact_score=impact_score,
        risk_summary=risk_summary,
        affected_friendly_assets=affected_assets,
        enemy_effects=enemy_effects,
        roe_violations=roe_violations
    )

    logger.info("coa_analysis_complete", impact_score=impact_score)

    return analysis.model_dump(mode='json')


async def get_interference_report(
    location: Dict[str, float],
    frequency_range_mhz: Dict[str, float]
) -> Dict[str, Any]:
    """
    Get interference report for a location and frequency range.

    Args:
        location: Location dict with 'lat', 'lon'
        frequency_range_mhz: Frequency range dict with 'min', 'max'

    Returns:
        Interference report
    """
    logger.info(
        "get_interference_report",
        location=location,
        freq_range=frequency_range_mhz
    )

    loc = Location(**location)
    min_freq = frequency_range_mhz['min']
    max_freq = frequency_range_mhz['max']

    # Get allocations in frequency range
    allocations = await allocation_store.get_by_frequency_range(
        min_freq,
        max_freq,
        datetime.utcnow()
    )

    # Calculate interference from each allocation
    sources: List[InterferenceSource] = []
    total_power_mw = 0.0  # Total interference power in milliwatts

    for alloc in allocations:
        distance_km = propagation_model.calculate_distance_km(loc, alloc.location)

        # Calculate interference
        interference_power, normalized_level = propagation_model.calculate_interference_level(
            alloc.power_dbm,
            alloc.frequency_mhz,
            (min_freq + max_freq) / 2,  # Center of requested range
            distance_km
        )

        # Calculate azimuth
        azimuth = _calculate_azimuth(loc, alloc.location)

        source = InterferenceSource(
            source_id=alloc.asset_id,
            frequency_mhz=alloc.frequency_mhz,
            estimated_power_dbm=interference_power,
            azimuth_degrees=azimuth,
            interference_level=normalized_level
        )
        sources.append(source)

        # Accumulate total power (convert dBm to mW)
        power_mw = 10 ** (interference_power / 10.0)
        total_power_mw += power_mw

    # Convert total back to dBm
    if total_power_mw > 0:
        total_noise_floor = 10 * math.log10(total_power_mw)
    else:
        total_noise_floor = -120.0  # Thermal noise floor

    report = InterferenceReport(
        location=loc,
        frequency_range_mhz=frequency_range_mhz,
        interference_sources=sources,
        total_noise_floor=total_noise_floor
    )

    logger.info("interference_report_generated", num_sources=len(sources))

    return report.model_dump(mode='json')


# Helper functions

def _assess_threat(emitter: Emitter) -> ThreatAssessment:
    """Perform basic threat assessment on an emitter."""
    # Simplified threat assessment based on frequency and signal characteristics
    waveform = emitter.signal_characteristics.waveform.upper()

    # Determine threat type
    if 'RADAR' in waveform or emitter.signal_characteristics.prf_hz:
        threat_type = ThreatType.RADAR
    elif 'JAM' in waveform:
        threat_type = ThreatType.JAMMER
    elif 'COMM' in waveform or 'FM' in waveform or 'AM' in waveform:
        threat_type = ThreatType.COMMUNICATIONS
    else:
        threat_type = ThreatType.UNKNOWN

    # Determine threat level (simplified)
    if emitter.frequency_mhz > 8000:  # X-band and above (typical fire control radar)
        threat_level = ThreatLevel.HIGH
    elif emitter.frequency_mhz > 2000:  # S-band (typical search radar)
        threat_level = ThreatLevel.MEDIUM
    else:
        threat_level = ThreatLevel.LOW

    # Adjust based on confidence
    if emitter.confidence < 0.5:
        threat_level = ThreatLevel.LOW

    return ThreatAssessment(
        threat_type=threat_type,
        threat_level=threat_level,
        matches_known_system=None,  # Would require database lookup
        confidence=emitter.confidence
    )


async def _analyze_friendly_impact(actions: List[FriendlyAction]) -> List[AffectedAsset]:
    """Analyze impact of COA on friendly assets."""
    affected: List[AffectedAsset] = []

    # Get all current allocations
    allocations = await allocation_store.get_active_allocations(datetime.utcnow())

    for action in actions:
        for alloc in allocations:
            # Calculate potential interference
            distance_km = propagation_model.calculate_distance_km(
                action.location,
                alloc.location
            )

            interference_power, severity = propagation_model.calculate_interference_level(
                action.power_dbm,
                action.frequency_mhz,
                alloc.frequency_mhz,
                distance_km
            )

            if severity > 0.1:  # Only report significant impacts
                affected.append(AffectedAsset(
                    asset_id=alloc.asset_id,
                    impact_type="INTERFERENCE",
                    severity=severity,
                    description=f"Interference from {action.action_type.value}: {interference_power:.1f} dBm at {distance_km:.1f} km"
                ))

    return affected


async def _analyze_enemy_impact(actions: List[FriendlyAction]) -> EnemyEffects:
    """Analyze impact of COA on enemy systems."""
    # Get known enemy emitters
    emitters = await emitter_store.get_all()

    affected_systems: List[str] = []
    total_degradation_prob = 0.0

    for action in actions:
        for emitter in emitters:
            if action.action_type.value == "JAMMING":
                # Calculate J/S ratio
                distance_to_emitter = propagation_model.calculate_distance_km(
                    action.location,
                    emitter.location
                )

                # Simplified: assume emitter receiver is co-located
                js_ratio = propagation_model.calculate_jamming_effectiveness(
                    action.power_dbm,
                    action.frequency_mhz,
                    30.0,  # Assume enemy transmitter power
                    emitter.frequency_mhz,
                    50.0,  # Assume 50km to enemy receiver
                    distance_to_emitter
                )

                # J/S > 0 dB means jamming is effective
                if js_ratio > 0:
                    degradation_prob = min(1.0, js_ratio / 20.0)  # Normalize
                    total_degradation_prob = max(total_degradation_prob, degradation_prob)

                    system_name = emitter.threat_assessment.matches_known_system if emitter.threat_assessment and emitter.threat_assessment.matches_known_system else f"Emitter-{emitter.emitter_id[:8]}"
                    affected_systems.append(system_name)

    return EnemyEffects(
        probability_of_degradation=total_degradation_prob,
        affected_systems=list(set(affected_systems))  # Remove duplicates
    )


def _calculate_impact_score(
    affected_assets: List[AffectedAsset],
    enemy_effects: EnemyEffects,
    roe_violations: List[str]
) -> float:
    """Calculate overall impact score (0-1, higher is better)."""
    # Start with enemy effects (positive contribution)
    score = enemy_effects.probability_of_degradation * 0.6

    # Subtract friendly impacts (negative contribution)
    if affected_assets:
        avg_friendly_impact = sum(a.severity for a in affected_assets) / len(affected_assets)
        score -= avg_friendly_impact * 0.3

    # ROE violations are critical
    if roe_violations:
        score -= 0.5

    return max(0.0, min(1.0, score))


def _generate_risk_summary(
    affected_assets: List[AffectedAsset],
    enemy_effects: EnemyEffects,
    roe_violations: List[str]
) -> str:
    """Generate human-readable risk summary."""
    parts = []

    if roe_violations:
        parts.append(f"ROE VIOLATIONS: {len(roe_violations)} violation(s)")

    if affected_assets:
        high_impact = [a for a in affected_assets if a.severity > 0.7]
        if high_impact:
            parts.append(f"HIGH RISK: {len(high_impact)} friendly asset(s) severely impacted")
        else:
            parts.append(f"MODERATE RISK: {len(affected_assets)} friendly asset(s) impacted")

    if enemy_effects.affected_systems:
        parts.append(f"EFFECTIVENESS: {len(enemy_effects.affected_systems)} enemy system(s) degraded ({enemy_effects.probability_of_degradation*100:.0f}% probability)")

    if not parts:
        return "LOW RISK: Minimal impact on friendly assets, limited enemy effects"

    return "; ".join(parts)


def _calculate_azimuth(from_loc: Location, to_loc: Location) -> float:
    """Calculate azimuth from one location to another (0-360 degrees)."""
    import math

    lat1 = math.radians(from_loc.lat)
    lat2 = math.radians(to_loc.lat)
    dlon = math.radians(to_loc.lon - from_loc.lon)

    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    azimuth_rad = math.atan2(y, x)
    azimuth_deg = math.degrees(azimuth_rad)

    # Normalize to 0-360
    return (azimuth_deg + 360) % 360
