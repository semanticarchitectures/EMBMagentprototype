"""
Prometheus Metrics for EMBM-J DS Multi-Agent System.

PHASE 5 ENHANCEMENT: Metrics collection and export for monitoring.

Provides metrics for:
- Agent execution performance
- Deconfliction decisions
- ROE violations
- Message broker activity
- LLM cache performance
- System health

Usage:
    from metrics import metrics

    # Increment counters
    metrics.deconfliction_requests.inc()
    metrics.deconfliction_approvals.inc()

    # Record durations
    with metrics.agent_duration.labels(agent_name="Spectrum Manager").time():
        # Agent execution
        ...

    # Set gauges
    metrics.active_agents.set(3)
"""

from typing import Optional
import structlog

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning(
        "prometheus_not_available",
        message="Install prometheus_client for metrics support: pip install prometheus-client"
    )


logger = structlog.get_logger(__name__)


class EMBMMetrics:
    """
    Prometheus metrics for EMBM-J DS system.

    PHASE 5 ENHANCEMENT: Comprehensive metrics collection.
    """

    def __init__(self):
        """Initialize Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_metrics_disabled")
            return

        # System info
        self.system_info = Info(
            "embm_system",
            "EMBM-J DS system information"
        )
        self.system_info.info({
            "version": "1.0.0",
            "phase": "5",
            "system": "EMBM-J DS Multi-Agent"
        })

        # Deconfliction metrics
        self.deconfliction_requests = Counter(
            "embm_deconfliction_requests_total",
            "Total number of deconfliction requests",
            ["asset_type", "priority"]
        )

        self.deconfliction_approvals = Counter(
            "embm_deconfliction_approvals_total",
            "Total number of approved deconfliction requests",
            ["asset_type", "priority"]
        )

        self.deconfliction_denials = Counter(
            "embm_deconfliction_denials_total",
            "Total number of denied deconfliction requests",
            ["asset_type", "priority", "reason"]
        )

        self.deconfliction_conflicts = Counter(
            "embm_deconfliction_conflicts_total",
            "Total number of conflicting deconfliction requests"
        )

        self.deconfliction_duration = Histogram(
            "embm_deconfliction_duration_seconds",
            "Time spent processing deconfliction requests",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        # Agent metrics
        self.agent_sessions = Counter(
            "embm_agent_sessions_total",
            "Total number of agent sessions",
            ["agent_name", "status"]
        )

        self.agent_duration = Histogram(
            "embm_agent_duration_seconds",
            "Agent execution duration",
            ["agent_name"],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
        )

        self.agent_iterations = Histogram(
            "embm_agent_iterations",
            "Number of think-act-observe iterations per agent",
            ["agent_name"],
            buckets=[1, 2, 3, 4, 5, 10]
        )

        self.agent_tool_calls = Counter(
            "embm_agent_tool_calls_total",
            "Total number of tool calls by agents",
            ["agent_name", "tool_name"]
        )

        self.active_agents = Gauge(
            "embm_active_agents",
            "Number of currently active agents"
        )

        # LLM metrics
        self.llm_requests = Counter(
            "embm_llm_requests_total",
            "Total number of LLM requests",
            ["provider", "model"]
        )

        self.llm_cache_hits = Counter(
            "embm_llm_cache_hits_total",
            "Total number of LLM cache hits"
        )

        self.llm_cache_misses = Counter(
            "embm_llm_cache_misses_total",
            "Total number of LLM cache misses"
        )

        self.llm_cache_size = Gauge(
            "embm_llm_cache_size",
            "Current size of LLM cache"
        )

        self.llm_duration = Histogram(
            "embm_llm_duration_seconds",
            "LLM request duration",
            ["provider"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        # ROE metrics
        self.roe_violations = Counter(
            "embm_roe_violations_total",
            "Total number of ROE violations",
            ["violation_type", "severity"]
        )

        self.roe_checks = Counter(
            "embm_roe_checks_total",
            "Total number of ROE compliance checks",
            ["result"]  # compliant, violation
        )

        # Message broker metrics
        self.messages_published = Counter(
            "embm_messages_published_total",
            "Total number of messages published",
            ["topic", "message_type"]
        )

        self.messages_received = Counter(
            "embm_messages_received_total",
            "Total number of messages received",
            ["topic", "subscriber"]
        )

        self.active_subscriptions = Gauge(
            "embm_active_subscriptions",
            "Number of active message broker subscriptions"
        )

        self.message_broker_topics = Gauge(
            "embm_message_broker_topics",
            "Number of active message broker topics"
        )

        # System health metrics
        self.mcp_server_up = Gauge(
            "embm_mcp_server_up",
            "MCP server health status (1 = up, 0 = down)"
        )

        self.web_dashboard_clients = Gauge(
            "embm_web_dashboard_clients",
            "Number of connected web dashboard clients"
        )

        self.database_connections = Gauge(
            "embm_database_connections",
            "Number of active database connections"
        )

        # Performance metrics
        self.http_requests = Counter(
            "embm_http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code"]
        )

        self.http_request_duration = Histogram(
            "embm_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )

        logger.info("prometheus_metrics_initialized")

    def record_deconfliction(
        self,
        asset_type: str,
        priority: str,
        status: str,
        duration: float,
        conflict_count: int = 0,
        denial_reason: Optional[str] = None
    ):
        """
        Record deconfliction decision metrics.

        Args:
            asset_type: Type of asset
            priority: Priority level
            status: Decision status (APPROVED, DENIED, CONFLICT)
            duration: Processing duration in seconds
            conflict_count: Number of conflicts
            denial_reason: Reason for denial (if applicable)
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.deconfliction_requests.labels(
            asset_type=asset_type,
            priority=priority
        ).inc()

        if status == "APPROVED":
            self.deconfliction_approvals.labels(
                asset_type=asset_type,
                priority=priority
            ).inc()
        elif status == "DENIED":
            self.deconfliction_denials.labels(
                asset_type=asset_type,
                priority=priority,
                reason=denial_reason or "unknown"
            ).inc()

        if conflict_count > 0:
            self.deconfliction_conflicts.inc(conflict_count)

        self.deconfliction_duration.observe(duration)

    def record_agent_session(
        self,
        agent_name: str,
        duration: float,
        iterations: int,
        tool_calls: int,
        status: str
    ):
        """
        Record agent session metrics.

        Args:
            agent_name: Name of agent
            duration: Execution duration in seconds
            iterations: Number of iterations
            tool_calls: Number of tool calls
            status: Final status
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.agent_sessions.labels(
            agent_name=agent_name,
            status=status
        ).inc()

        self.agent_duration.labels(agent_name=agent_name).observe(duration)
        self.agent_iterations.labels(agent_name=agent_name).observe(iterations)

    def record_llm_request(
        self,
        provider: str,
        model: str,
        duration: float,
        cache_hit: bool
    ):
        """
        Record LLM request metrics.

        Args:
            provider: LLM provider
            model: Model name
            duration: Request duration in seconds
            cache_hit: Whether request was served from cache
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.llm_requests.labels(provider=provider, model=model).inc()

        if cache_hit:
            self.llm_cache_hits.inc()
        else:
            self.llm_cache_misses.inc()

        self.llm_duration.labels(provider=provider).observe(duration)

    def record_roe_violation(
        self,
        violation_type: str,
        severity: str
    ):
        """
        Record ROE violation.

        Args:
            violation_type: Type of violation
            severity: Severity level
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.roe_violations.labels(
            violation_type=violation_type,
            severity=severity
        ).inc()

        self.roe_checks.labels(result="violation").inc()

    def record_roe_compliance(self):
        """Record successful ROE compliance check."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.roe_checks.labels(result="compliant").inc()

    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in text format.

        Returns:
            Metrics in Prometheus text format
        """
        if not PROMETHEUS_AVAILABLE:
            return b"# Prometheus client not installed\n"

        return generate_latest(REGISTRY)


# Global metrics instance
metrics = EMBMMetrics()


# Example usage
if __name__ == "__main__":
    import time

    print("=== EMBM-J DS Metrics Example ===")
    print()

    # Simulate some metrics
    metrics.deconfliction_requests.labels(asset_type="RADAR", priority="ROUTINE").inc()
    metrics.deconfliction_approvals.labels(asset_type="RADAR", priority="ROUTINE").inc()

    metrics.agent_sessions.labels(agent_name="Spectrum Manager", status="COMPLETED").inc()
    metrics.agent_duration.labels(agent_name="Spectrum Manager").observe(15.5)
    metrics.agent_iterations.labels(agent_name="Spectrum Manager").observe(3)

    metrics.llm_requests.labels(provider="anthropic", model="claude-3-5-sonnet-20241022").inc()
    metrics.llm_cache_hits.inc()

    metrics.roe_violations.labels(violation_type="RESTRICTED_ZONE", severity="HIGH").inc()

    metrics.active_agents.set(2)
    metrics.mcp_server_up.set(1)

    # Print metrics
    print("Metrics collected:")
    print(metrics.get_metrics().decode('utf-8'))
