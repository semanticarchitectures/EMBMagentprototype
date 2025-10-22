"""
Database Models for EMBM-J DS Multi-Agent System.

PHASE 5 ENHANCEMENT: Persistent storage for allocations, decisions, and agent history.

Models:
- FrequencyAllocation: Spectrum allocations with deconfliction status
- DeconflictionDecision: All deconfliction requests and outcomes
- AgentSession: Agent execution sessions and performance metrics
- ROEViolation: Rules of Engagement violations
- MessageBrokerEvent: Message broker activity log
"""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import structlog


logger = structlog.get_logger(__name__)


Base = declarative_base()


class AllocationStatus(str, PyEnum):
    """Status of frequency allocation."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CONFLICT = "CONFLICT"
    EXPIRED = "EXPIRED"


class Priority(str, PyEnum):
    """Priority levels for requests."""
    ROUTINE = "ROUTINE"
    PRIORITY = "PRIORITY"
    IMMEDIATE = "IMMEDIATE"
    FLASH = "FLASH"


class AgentStatus(str, PyEnum):
    """Agent execution status."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class FrequencyAllocation(Base):
    """
    Frequency allocation record.

    Stores all frequency allocation requests and their status.
    """
    __tablename__ = "frequency_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allocation_id = Column(String(255), unique=True, nullable=False, index=True)

    # Request details
    asset_rid = Column(String(255), nullable=False, index=True)
    frequency_mhz = Column(Float, nullable=False, index=True)
    bandwidth_khz = Column(Float, nullable=False)
    power_dbm = Column(Float, nullable=False)

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    # Priority and purpose
    priority = Column(Enum(Priority), nullable=False, index=True)
    purpose = Column(Text, nullable=True)

    # Status
    status = Column(Enum(AllocationStatus), nullable=False, default=AllocationStatus.PENDING, index=True)
    approval_time = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deconfliction_decision = relationship("DeconflictionDecision", back_populates="allocation", uselist=False)

    def __repr__(self):
        return f"<FrequencyAllocation(id={self.allocation_id}, asset={self.asset_rid}, freq={self.frequency_mhz} MHz, status={self.status})>"


class DeconflictionDecision(Base):
    """
    Deconfliction decision record.

    Stores all deconfliction requests, analysis, and decisions.
    """
    __tablename__ = "deconfliction_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String(255), unique=True, nullable=False, index=True)

    # Link to allocation
    allocation_id = Column(Integer, ForeignKey("frequency_allocations.id"), nullable=True)
    allocation = relationship("FrequencyAllocation", back_populates="deconfliction_decision")

    # Request details (denormalized for query performance)
    asset_rid = Column(String(255), nullable=False, index=True)
    frequency_mhz = Column(Float, nullable=False, index=True)
    priority = Column(Enum(Priority), nullable=False)

    # Decision
    status = Column(Enum(AllocationStatus), nullable=False, index=True)
    decision_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    decided_by = Column(String(255), nullable=True)  # Agent or system that made decision

    # Conflicts
    conflict_count = Column(Integer, default=0)
    conflicting_allocations = Column(JSON, nullable=True)  # List of conflicting allocation IDs

    # ROE analysis
    roe_violations = Column(JSON, nullable=True)  # List of ROE violation descriptions
    roe_compliant = Column(Boolean, default=True)

    # Reasoning
    reasoning = Column(Text, nullable=True)  # LLM reasoning for decision
    alternatives_considered = Column(JSON, nullable=True)  # Alternative frequencies/times

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    violations = relationship("ROEViolation", back_populates="decision")

    def __repr__(self):
        return f"<DeconflictionDecision(id={self.decision_id}, asset={self.asset_rid}, status={self.status})>"


class AgentSession(Base):
    """
    Agent execution session record.

    Tracks agent invocations, performance, and outcomes.
    """
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)

    # Agent details
    agent_name = Column(String(255), nullable=False, index=True)
    agent_role = Column(String(255), nullable=False)
    agent_provider = Column(String(100), nullable=False)  # anthropic, openai, google

    # Execution details
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Performance metrics
    iterations = Column(Integer, default=0)
    tool_calls = Column(Integer, default=0)
    llm_calls = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)

    # Status and outcome
    status = Column(Enum(AgentStatus), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    final_output = Column(Text, nullable=True)

    # Input
    input_message = Column(Text, nullable=False)
    input_length = Column(Integer, nullable=False)

    # Tools used
    tools_used = Column(JSON, nullable=True)  # List of tool names

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<AgentSession(id={self.session_id}, agent={self.agent_name}, status={self.status}, iterations={self.iterations})>"


class ROEViolation(Base):
    """
    Rules of Engagement violation record.

    Tracks all ROE violations for compliance and analysis.
    """
    __tablename__ = "roe_violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(String(255), unique=True, nullable=False, index=True)

    # Link to decision
    decision_id = Column(Integer, ForeignKey("deconfliction_decisions.id"), nullable=True)
    decision = relationship("DeconflictionDecision", back_populates="violations")

    # Violation details
    violation_type = Column(String(255), nullable=False, index=True)  # RESTRICTED_ZONE, FREQUENCY_BAND, POWER_LIMIT, etc.
    severity = Column(String(50), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)

    # Request that caused violation
    asset_rid = Column(String(255), nullable=False, index=True)
    frequency_mhz = Column(Float, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)

    # ROE rule violated
    rule_name = Column(String(255), nullable=True)
    rule_description = Column(Text, nullable=True)

    # Timestamp
    violated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ROEViolation(id={self.violation_id}, type={self.violation_type}, severity={self.severity})>"


class MessageBrokerEvent(Base):
    """
    Message broker event record.

    Logs message broker activity for analysis and debugging.
    """
    __tablename__ = "message_broker_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # published, received, subscription, etc.
    topic = Column(String(255), nullable=False, index=True)
    sender = Column(String(255), nullable=True, index=True)
    recipient = Column(String(255), nullable=True, index=True)

    # Message details
    message_type = Column(String(100), nullable=True)  # broadcast, notification, request, response
    message_id = Column(String(255), nullable=True, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)

    # Content
    content = Column(JSON, nullable=True)
    content_size_bytes = Column(Integer, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<MessageBrokerEvent(id={self.event_id}, type={self.event_type}, topic={self.topic})>"


class SystemMetrics(Base):
    """
    System metrics snapshots.

    Stores periodic system metrics for trend analysis.
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Agent metrics
    active_agents = Column(Integer, default=0)
    total_agent_sessions = Column(Integer, default=0)
    avg_agent_duration_seconds = Column(Float, default=0.0)

    # Deconfliction metrics
    total_deconfliction_requests = Column(Integer, default=0)
    approved_requests = Column(Integer, default=0)
    denied_requests = Column(Integer, default=0)
    conflict_requests = Column(Integer, default=0)

    # ROE metrics
    total_roe_violations = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)

    # Message broker metrics
    total_messages = Column(Integer, default=0)
    total_subscriptions = Column(Integer, default=0)
    active_topics = Column(Integer, default=0)

    # LLM cache metrics
    cache_hit_rate = Column(Float, default=0.0)
    cache_size = Column(Integer, default=0)

    # System health
    mcp_server_healthy = Column(Boolean, default=True)
    web_dashboard_clients = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemMetrics(timestamp={self.timestamp}, agents={self.active_agents}, requests={self.total_deconfliction_requests})>"
