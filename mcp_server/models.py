"""
Data models for the EMBM-J DS MCP Server.

These models define the structure of data exchanged between agents and the MCP server,
representing spectrum allocations, deconfliction requests, emitters, and related entities.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class Location(BaseModel):
    """Geographic location in WGS84 coordinates."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude_m: Optional[float] = Field(None, description="Altitude in meters above sea level")


class ServiceBranch(str, Enum):
    """US Military service branches."""
    AIR_FORCE = "Air Force"
    NAVY = "Navy"
    ARMY = "Army"
    MARINES = "Marines"
    SPACE_FORCE = "Space Force"
    JOINT = "Joint"


class Priority(str, Enum):
    """Request priority levels."""
    ROUTINE = "ROUTINE"
    PRIORITY = "PRIORITY"
    IMMEDIATE = "IMMEDIATE"
    FLASH = "FLASH"


class ConflictType(str, Enum):
    """Types of spectrum conflicts."""
    FREQUENCY = "FREQUENCY"
    GEOGRAPHIC = "GEOGRAPHIC"
    TIME = "TIME"
    POLICY = "POLICY"
    ROE = "ROE"


class DeconflictionStatus(str, Enum):
    """Status of deconfliction requests."""
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"


class ThreatLevel(str, Enum):
    """Threat assessment levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ThreatType(str, Enum):
    """Types of electromagnetic threats."""
    RADAR = "RADAR"
    JAMMER = "JAMMER"
    COMMUNICATIONS = "COMMUNICATIONS"
    ELECTRONIC_ATTACK = "ELECTRONIC_ATTACK"
    UNKNOWN = "UNKNOWN"


class ActionType(str, Enum):
    """Types of friendly actions in COA analysis."""
    JAMMING = "JAMMING"
    COMMUNICATION = "COMMUNICATION"
    RADAR = "RADAR"
    ISR = "ISR"
    DATALINK = "DATALINK"


class FrequencyAllocation(BaseModel):
    """Represents an allocated frequency assignment."""
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str = Field(..., description="Unique identifier for the asset")
    frequency_mhz: float = Field(..., gt=0, description="Center frequency in MHz")
    bandwidth_khz: float = Field(..., gt=0, description="Bandwidth in kHz")
    location: Location
    start_time: datetime
    end_time: datetime
    service: ServiceBranch
    priority: Priority
    power_dbm: float = Field(..., description="Transmit power in dBm")
    purpose: str = Field(..., description="Purpose of the allocation")

    @validator('end_time')
    def end_after_start(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class Conflict(BaseModel):
    """Represents a spectrum conflict."""
    conflicting_asset: str = Field(..., description="Asset ID causing conflict")
    conflict_type: ConflictType
    severity: float = Field(..., ge=0, le=1, description="Severity score 0-1")
    description: str = Field(..., description="Human-readable conflict description")
    frequency_mhz: Optional[float] = None
    distance_km: Optional[float] = None


class DeconflictionRequest(BaseModel):
    """Request for spectrum deconfliction."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_rid: str = Field(..., description="Requesting asset RID")
    frequency_mhz: float = Field(..., gt=0)
    bandwidth_khz: float = Field(..., gt=0)
    power_dbm: float
    location: Location
    start_time: datetime
    duration_minutes: int = Field(..., gt=0)
    priority: Priority
    purpose: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class DeconflictionResponse(BaseModel):
    """Response to a deconfliction request."""
    request_id: str
    status: DeconflictionStatus
    conflict_details: List[Conflict] = []
    alternative_frequencies: List[float] = Field(
        default=[],
        description="Suggested alternative frequencies in MHz"
    )
    justification: str = Field(..., description="Explanation of the decision")
    authorization_id: Optional[str] = Field(
        None,
        description="Authorization ID if approved"
    )


class SignalCharacteristics(BaseModel):
    """Characteristics of a detected signal."""
    waveform: str = Field(..., description="Waveform type (e.g., CW, FM, PSK)")
    prf_hz: Optional[float] = Field(None, description="Pulse repetition frequency in Hz")
    modulation: str = Field(..., description="Modulation type")
    pulse_width_us: Optional[float] = Field(None, description="Pulse width in microseconds")


class ThreatAssessment(BaseModel):
    """Assessment of a detected emitter threat."""
    threat_type: ThreatType
    threat_level: ThreatLevel
    matches_known_system: Optional[str] = Field(
        None,
        description="Known system match (e.g., 'S-400 radar')"
    )
    confidence: float = Field(..., ge=0, le=1, description="Assessment confidence 0-1")


class Emitter(BaseModel):
    """Represents a detected electromagnetic emitter."""
    emitter_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location: Location
    frequency_mhz: float = Field(..., gt=0)
    bandwidth_khz: float = Field(..., gt=0)
    signal_characteristics: SignalCharacteristics
    detection_time: datetime
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence 0-1")
    threat_assessment: Optional[ThreatAssessment] = None


class FriendlyAction(BaseModel):
    """Represents a friendly action in a Course of Action."""
    action_type: ActionType
    asset_id: str
    frequency_mhz: float = Field(..., gt=0)
    power_dbm: float
    location: Location
    duration_minutes: int = Field(..., gt=0)


class AffectedAsset(BaseModel):
    """Asset affected by a COA."""
    asset_id: str
    impact_type: str = Field(..., description="Type of impact (e.g., INTERFERENCE, DETECTION_RISK)")
    severity: float = Field(..., ge=0, le=1, description="Impact severity 0-1")
    description: str


class EnemyEffects(BaseModel):
    """Expected effects on enemy systems."""
    probability_of_degradation: float = Field(
        ...,
        ge=0,
        le=1,
        description="Probability enemy systems will be degraded"
    )
    affected_systems: List[str] = Field(
        default=[],
        description="List of enemy systems expected to be affected"
    )


class COAImpactAnalysis(BaseModel):
    """Analysis of a Course of Action's impact."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    coa_id: str
    impact_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall impact score 0-1 (higher is better)"
    )
    risk_summary: str
    affected_friendly_assets: List[AffectedAsset] = []
    enemy_effects: EnemyEffects
    roe_violations: List[str] = Field(
        default=[],
        description="List of ROE violations, empty if compliant"
    )


class InterferenceSource(BaseModel):
    """Source of electromagnetic interference."""
    source_id: str
    frequency_mhz: float = Field(..., gt=0)
    estimated_power_dbm: float
    azimuth_degrees: float = Field(..., ge=0, lt=360)
    interference_level: float = Field(
        ...,
        ge=0,
        le=1,
        description="Interference level 0-1"
    )


class InterferenceReport(BaseModel):
    """Report of interference at a location."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location: Location
    frequency_range_mhz: Dict[str, float] = Field(
        ...,
        description="Frequency range {'min': x, 'max': y}"
    )
    interference_sources: List[InterferenceSource] = []
    total_noise_floor: float = Field(..., description="Total noise floor in dBm")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AllocationResult(BaseModel):
    """Result of a frequency allocation."""
    allocation_id: str
    status: str = Field(..., description="SUCCESS or FAILED")
    expires_at: Optional[datetime] = None
    message: str


class SpectrumPlan(BaseModel):
    """Complete spectrum allocation plan for an area and time period."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ao_geojson: str = Field(..., description="Area of operations as GeoJSON polygon")
    start_time: datetime
    end_time: datetime
    allocations: List[FrequencyAllocation] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# MCP Protocol Wrappers
class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 request wrapper."""
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = {}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class MCPError(BaseModel):
    """MCP JSON-RPC 2.0 error object."""
    code: int
    message: str
    data: Optional[Any] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC 2.0 response wrapper."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: str
