"""
Database Repository Layer for EMBM-J DS.

PHASE 5 ENHANCEMENT: Clean data access layer with business logic.

Provides high-level data access methods for:
- Frequency allocations
- Deconfliction decisions
- Agent sessions
- ROE violations
- Analytics and reporting
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
import structlog

from database.models import (
    FrequencyAllocation,
    DeconflictionDecision,
    AgentSession,
    ROEViolation,
    MessageBrokerEvent,
    SystemMetrics,
    AllocationStatus,
    Priority,
    AgentStatus
)


logger = structlog.get_logger(__name__)


class AllocationRepository:
    """Repository for frequency allocations."""

    @staticmethod
    def create_allocation(
        session: Session,
        asset_rid: str,
        frequency_mhz: float,
        bandwidth_khz: float,
        power_dbm: float,
        latitude: float,
        longitude: float,
        start_time: datetime,
        duration_minutes: int,
        priority: Priority,
        purpose: Optional[str] = None
    ) -> FrequencyAllocation:
        """Create a new frequency allocation."""
        allocation = FrequencyAllocation(
            allocation_id=str(uuid4()),
            asset_rid=asset_rid,
            frequency_mhz=frequency_mhz,
            bandwidth_khz=bandwidth_khz,
            power_dbm=power_dbm,
            latitude=latitude,
            longitude=longitude,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            duration_minutes=duration_minutes,
            priority=priority,
            purpose=purpose,
            status=AllocationStatus.PENDING
        )

        session.add(allocation)
        session.flush()

        logger.info(
            "allocation_created",
            allocation_id=allocation.allocation_id,
            asset=asset_rid,
            frequency=frequency_mhz
        )

        return allocation

    @staticmethod
    def get_active_allocations(
        session: Session,
        at_time: Optional[datetime] = None
    ) -> List[FrequencyAllocation]:
        """
        Get all active allocations at a given time.

        Args:
            session: Database session
            at_time: Time to check (defaults to now)

        Returns:
            List of active allocations
        """
        if at_time is None:
            at_time = datetime.utcnow()

        return session.query(FrequencyAllocation).filter(
            and_(
                FrequencyAllocation.status == AllocationStatus.APPROVED,
                FrequencyAllocation.start_time <= at_time,
                FrequencyAllocation.end_time >= at_time
            )
        ).all()

    @staticmethod
    def get_conflicting_allocations(
        session: Session,
        frequency_mhz: float,
        bandwidth_khz: float,
        start_time: datetime,
        end_time: datetime,
        min_separation_mhz: float = 10.0
    ) -> List[FrequencyAllocation]:
        """
        Find allocations that conflict with given parameters.

        Args:
            session: Database session
            frequency_mhz: Center frequency
            bandwidth_khz: Bandwidth
            start_time: Start time
            end_time: End time
            min_separation_mhz: Minimum frequency separation

        Returns:
            List of conflicting allocations
        """
        freq_min = frequency_mhz - min_separation_mhz
        freq_max = frequency_mhz + min_separation_mhz

        return session.query(FrequencyAllocation).filter(
            and_(
                FrequencyAllocation.status == AllocationStatus.APPROVED,
                FrequencyAllocation.frequency_mhz >= freq_min,
                FrequencyAllocation.frequency_mhz <= freq_max,
                or_(
                    and_(
                        FrequencyAllocation.start_time <= start_time,
                        FrequencyAllocation.end_time >= start_time
                    ),
                    and_(
                        FrequencyAllocation.start_time <= end_time,
                        FrequencyAllocation.end_time >= end_time
                    ),
                    and_(
                        FrequencyAllocation.start_time >= start_time,
                        FrequencyAllocation.end_time <= end_time
                    )
                )
            )
        ).all()


class DeconflictionRepository:
    """Repository for deconfliction decisions."""

    @staticmethod
    def create_decision(
        session: Session,
        asset_rid: str,
        frequency_mhz: float,
        priority: Priority,
        status: AllocationStatus,
        allocation_id: Optional[int] = None,
        conflict_count: int = 0,
        conflicting_allocations: Optional[List[str]] = None,
        roe_violations: Optional[List[str]] = None,
        reasoning: Optional[str] = None
    ) -> DeconflictionDecision:
        """Create a new deconfliction decision."""
        decision = DeconflictionDecision(
            decision_id=str(uuid4()),
            allocation_id=allocation_id,
            asset_rid=asset_rid,
            frequency_mhz=frequency_mhz,
            priority=priority,
            status=status,
            conflict_count=conflict_count,
            conflicting_allocations=conflicting_allocations,
            roe_violations=roe_violations,
            roe_compliant=not roe_violations if roe_violations else True,
            reasoning=reasoning
        )

        session.add(decision)
        session.flush()

        logger.info(
            "deconfliction_decision_created",
            decision_id=decision.decision_id,
            asset=asset_rid,
            status=status.value
        )

        return decision

    @staticmethod
    def get_approval_rate(
        session: Session,
        since: Optional[datetime] = None
    ) -> float:
        """
        Calculate deconfliction approval rate.

        Args:
            session: Database session
            since: Calculate rate since this time

        Returns:
            Approval rate (0.0 to 1.0)
        """
        query = session.query(DeconflictionDecision)

        if since:
            query = query.filter(DeconflictionDecision.decision_time >= since)

        total = query.count()
        if total == 0:
            return 0.0

        approved = query.filter(
            DeconflictionDecision.status == AllocationStatus.APPROVED
        ).count()

        return approved / total


class AgentRepository:
    """Repository for agent sessions."""

    @staticmethod
    def create_session(
        session: Session,
        agent_name: str,
        agent_role: str,
        agent_provider: str,
        input_message: str
    ) -> AgentSession:
        """Create a new agent session."""
        agent_session = AgentSession(
            session_id=str(uuid4()),
            agent_name=agent_name,
            agent_role=agent_role,
            agent_provider=agent_provider,
            start_time=datetime.utcnow(),
            status=AgentStatus.RUNNING,
            input_message=input_message,
            input_length=len(input_message)
        )

        session.add(agent_session)
        session.flush()

        logger.info(
            "agent_session_created",
            session_id=agent_session.session_id,
            agent=agent_name
        )

        return agent_session

    @staticmethod
    def complete_session(
        session: Session,
        session_id: str,
        status: AgentStatus,
        iterations: int = 0,
        tool_calls: int = 0,
        final_output: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Mark agent session as complete."""
        agent_session = session.query(AgentSession).filter(
            AgentSession.session_id == session_id
        ).first()

        if not agent_session:
            logger.error("agent_session_not_found", session_id=session_id)
            return

        agent_session.end_time = datetime.utcnow()
        agent_session.duration_seconds = (
            agent_session.end_time - agent_session.start_time
        ).total_seconds()
        agent_session.status = status
        agent_session.iterations = iterations
        agent_session.tool_calls = tool_calls
        agent_session.final_output = final_output
        agent_session.error_message = error_message

        session.flush()

        logger.info(
            "agent_session_completed",
            session_id=session_id,
            status=status.value,
            duration=agent_session.duration_seconds
        )

    @staticmethod
    def get_avg_duration(
        session: Session,
        agent_name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> float:
        """
        Calculate average agent execution duration.

        Args:
            session: Database session
            agent_name: Filter by agent name
            since: Calculate average since this time

        Returns:
            Average duration in seconds
        """
        query = session.query(func.avg(AgentSession.duration_seconds))

        if agent_name:
            query = query.filter(AgentSession.agent_name == agent_name)

        if since:
            query = query.filter(AgentSession.start_time >= since)

        result = query.scalar()
        return result if result else 0.0


class Analytics:
    """Analytics and reporting queries."""

    @staticmethod
    def get_deconfliction_stats(
        session: Session,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get deconfliction statistics.

        Returns:
            Dictionary with stats
        """
        query = session.query(DeconflictionDecision)

        if since:
            query = query.filter(DeconflictionDecision.decision_time >= since)

        total = query.count()

        return {
            "total_requests": total,
            "approved": query.filter(
                DeconflictionDecision.status == AllocationStatus.APPROVED
            ).count(),
            "denied": query.filter(
                DeconflictionDecision.status == AllocationStatus.DENIED
            ).count(),
            "conflicts": query.filter(
                DeconflictionDecision.status == AllocationStatus.CONFLICT
            ).count(),
            "approval_rate": DeconflictionRepository.get_approval_rate(session, since)
        }

    @staticmethod
    def get_agent_performance(
        session: Session,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Returns:
            Dictionary with performance stats
        """
        query = session.query(AgentSession)

        if since:
            query = query.filter(AgentSession.start_time >= since)

        total = query.count()

        return {
            "total_sessions": total,
            "completed": query.filter(
                AgentSession.status == AgentStatus.COMPLETED
            ).count(),
            "errors": query.filter(
                AgentSession.status == AgentStatus.ERROR
            ).count(),
            "avg_duration": AgentRepository.get_avg_duration(session, since=since),
            "avg_iterations": session.query(func.avg(AgentSession.iterations)).scalar() or 0.0
        }

    @staticmethod
    def get_roe_violation_summary(
        session: Session,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get ROE violation summary.

        Returns:
            Dictionary with violation stats
        """
        query = session.query(ROEViolation)

        if since:
            query = query.filter(ROEViolation.violated_at >= since)

        total = query.count()

        return {
            "total_violations": total,
            "critical": query.filter(ROEViolation.severity == "CRITICAL").count(),
            "high": query.filter(ROEViolation.severity == "HIGH").count(),
            "medium": query.filter(ROEViolation.severity == "MEDIUM").count(),
            "low": query.filter(ROEViolation.severity == "LOW").count()
        }

    @staticmethod
    def get_frequency_usage(
        session: Session,
        frequency_range: tuple = (3000.0, 4000.0)
    ) -> List[Dict[str, Any]]:
        """
        Get frequency usage statistics.

        Args:
            session: Database session
            frequency_range: (min_mhz, max_mhz)

        Returns:
            List of frequency allocations with usage stats
        """
        min_freq, max_freq = frequency_range

        allocations = session.query(FrequencyAllocation).filter(
            and_(
                FrequencyAllocation.frequency_mhz >= min_freq,
                FrequencyAllocation.frequency_mhz <= max_freq,
                FrequencyAllocation.status == AllocationStatus.APPROVED
            )
        ).all()

        return [
            {
                "frequency_mhz": alloc.frequency_mhz,
                "bandwidth_khz": alloc.bandwidth_khz,
                "asset": alloc.asset_rid,
                "start_time": alloc.start_time.isoformat(),
                "end_time": alloc.end_time.isoformat(),
                "priority": alloc.priority.value
            }
            for alloc in allocations
        ]
