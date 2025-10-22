# Phase 5: Production-Ready Deployment

**Status:** ✅ COMPLETE
**Focus:** Database persistence, metrics, analytics, production readiness
**Priority:** HIGH - Foundation for operational deployment

---

## Overview

Phase 5 transforms the EMBM-J DS Multi-Agent System into a production-ready application with:
- **Persistent database** for all system activity
- **Prometheus metrics** for monitoring and alerting
- **Analytics tools** for performance analysis
- **Production hardening** for operational deployment

---

## Key Enhancements

### 1. ✅ Database Persistence Layer

**Files:**
- `database/models.py` - SQLAlchemy database models
- `database/__init__.py` - Database connection and session management
- `database/repository.py` - High-level data access layer

**Database Schema:**

```
┌─────────────────────────┐
│ FrequencyAllocation     │
├─────────────────────────┤
│ id (PK)                 │
│ allocation_id (unique)  │
│ asset_rid               │
│ frequency_mhz          │
│ bandwidth_khz          │
│ power_dbm              │
│ latitude, longitude    │
│ start_time, end_time   │
│ priority               │
│ status                 │
└─────────────────────────┘
           │
           │ 1:1
           ↓
┌─────────────────────────┐
│ DeconflictionDecision   │
├─────────────────────────┤
│ id (PK)                 │
│ decision_id (unique)    │
│ allocation_id (FK)      │
│ status                  │
│ conflict_count         │
│ roe_violations         │
│ reasoning              │
└─────────────────────────┘
           │
           │ 1:N
           ↓
┌─────────────────────────┐
│ ROEViolation            │
├─────────────────────────┤
│ id (PK)                 │
│ violation_id (unique)   │
│ decision_id (FK)        │
│ violation_type          │
│ severity                │
│ description             │
└─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│ AgentSession            │     │ MessageBrokerEvent      │
├─────────────────────────┤     ├─────────────────────────┤
│ id (PK)                 │     │ id (PK)                 │
│ session_id (unique)     │     │ event_id (unique)       │
│ agent_name              │     │ topic                   │
│ start_time, end_time   │     │ sender, recipient       │
│ iterations, tool_calls │     │ message_type            │
│ status                  │     │ content                 │
└─────────────────────────┘     └─────────────────────────┘

┌─────────────────────────┐
│ SystemMetrics           │
├─────────────────────────┤
│ id (PK)                 │
│ timestamp               │
│ active_agents           │
│ total_requests          │
│ approval_rate           │
│ cache_hit_rate         │
└─────────────────────────┘
```

**Models:**
1. **FrequencyAllocation** - All frequency allocations with status tracking
2. **DeconflictionDecision** - Deconfliction requests and outcomes
3. **AgentSession** - Agent execution history and performance
4. **ROEViolation** - ROE compliance violations
5. **MessageBrokerEvent** - Message broker activity log
6. **SystemMetrics** - Periodic system metrics snapshots

**Database Support:**
- **SQLite** - Default, file-based database (easy setup)
- **PostgreSQL** - Production-ready relational database
- **In-Memory** - Testing and development

---

### 2. ✅ Repository Layer

**File:** `database/repository.py`

High-level data access with business logic:

**AllocationRepository:**
```python
from database import session_scope
from database.repository import AllocationRepository
from database.models import Priority

# Create allocation
with session_scope() as session:
    allocation = AllocationRepository.create_allocation(
        session=session,
        asset_rid="RADAR-01",
        frequency_mhz=3200.0,
        bandwidth_khz=50.0,
        power_dbm=55.0,
        latitude=35.0,
        longitude=45.0,
        start_time=datetime.utcnow(),
        duration_minutes=180,
        priority=Priority.ROUTINE,
        purpose="ISR surveillance"
    )

# Get active allocations
active = AllocationRepository.get_active_allocations(session)

# Find conflicts
conflicts = AllocationRepository.get_conflicting_allocations(
    session,
    frequency_mhz=3200.0,
    bandwidth_khz=50.0,
    start_time=start_time,
    end_time=end_time
)
```

**DeconflictionRepository:**
```python
# Create decision
decision = DeconflictionRepository.create_decision(
    session=session,
    asset_rid="RADAR-01",
    frequency_mhz=3200.0,
    priority=Priority.ROUTINE,
    status=AllocationStatus.APPROVED,
    reasoning="No conflicts detected"
)

# Get approval rate
approval_rate = DeconflictionRepository.get_approval_rate(
    session,
    since=datetime.utcnow() - timedelta(days=7)
)
```

**AgentRepository:**
```python
# Track agent session
agent_session = AgentRepository.create_session(
    session=session,
    agent_name="Spectrum Manager",
    agent_role="Electromagnetic Spectrum Manager",
    agent_provider="anthropic",
    input_message="Review spectrum plan..."
)

# Complete session
AgentRepository.complete_session(
    session=session,
    session_id=agent_session.session_id,
    status=AgentStatus.COMPLETED,
    iterations=3,
    tool_calls=5,
    final_output="Spectrum plan approved"
)

# Get average duration
avg_duration = AgentRepository.get_avg_duration(
    session,
    agent_name="Spectrum Manager"
)
```

---

### 3. ✅ Analytics & Reporting

**File:** `database/repository.py` - `Analytics` class

**Deconfliction Stats:**
```python
from database.repository import Analytics

with session_scope() as session:
    stats = Analytics.get_deconfliction_stats(
        session,
        since=datetime.utcnow() - timedelta(days=7)
    )

# Returns:
{
    "total_requests": 150,
    "approved": 120,
    "denied": 25,
    "conflicts": 5,
    "approval_rate": 0.80
}
```

**Agent Performance:**
```python
performance = Analytics.get_agent_performance(session)

# Returns:
{
    "total_sessions": 45,
    "completed": 42,
    "errors": 3,
    "avg_duration": 18.5,
    "avg_iterations": 2.8
}
```

**ROE Violations:**
```python
violations = Analytics.get_roe_violation_summary(session)

# Returns:
{
    "total_violations": 12,
    "critical": 2,
    "high": 5,
    "medium": 3,
    "low": 2
}
```

**Frequency Usage:**
```python
usage = Analytics.get_frequency_usage(
    session,
    frequency_range=(3000.0, 4000.0)
)

# Returns list of allocations in range
[
    {
        "frequency_mhz": 3200.0,
        "bandwidth_khz": 50.0,
        "asset": "RADAR-01",
        "start_time": "2025-10-18T12:00:00Z",
        "end_time": "2025-10-18T15:00:00Z",
        "priority": "ROUTINE"
    },
    ...
]
```

---

### 4. ✅ Prometheus Metrics

**File:** `metrics.py`

Comprehensive metrics collection for monitoring and alerting.

**Metrics Categories:**

1. **Deconfliction Metrics:**
   - `embm_deconfliction_requests_total` - Total requests
   - `embm_deconfliction_approvals_total` - Approvals
   - `embm_deconfliction_denials_total` - Denials
   - `embm_deconfliction_duration_seconds` - Processing time

2. **Agent Metrics:**
   - `embm_agent_sessions_total` - Agent sessions
   - `embm_agent_duration_seconds` - Execution duration
   - `embm_agent_iterations` - Iterations per session
   - `embm_agent_tool_calls_total` - Tool calls
   - `embm_active_agents` - Currently active agents

3. **LLM Metrics:**
   - `embm_llm_requests_total` - LLM API calls
   - `embm_llm_cache_hits_total` - Cache hits
   - `embm_llm_cache_misses_total` - Cache misses
   - `embm_llm_duration_seconds` - Request duration

4. **ROE Metrics:**
   - `embm_roe_violations_total` - Violations
   - `embm_roe_checks_total` - Compliance checks

5. **System Health:**
   - `embm_mcp_server_up` - MCP server status
   - `embm_web_dashboard_clients` - Connected clients
   - `embm_database_connections` - DB connections

**Usage:**
```python
from metrics import metrics

# Record deconfliction
metrics.record_deconfliction(
    asset_type="RADAR",
    priority="ROUTINE",
    status="APPROVED",
    duration=1.2
)

# Record agent session
metrics.record_agent_session(
    agent_name="Spectrum Manager",
    duration=15.5,
    iterations=3,
    tool_calls=5,
    status="COMPLETED"
)

# Record LLM request
metrics.record_llm_request(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    duration=2.3,
    cache_hit=True
)

# Set gauges
metrics.active_agents.set(3)
metrics.mcp_server_up.set(1)

# Get metrics (for Prometheus scraping)
prometheus_metrics = metrics.get_metrics()
```

---

## Installation

### Dependencies

Install Phase 5 dependencies:

```bash
# Database support
pip install sqlalchemy

# Prometheus metrics
pip install prometheus-client

# Optional: PostgreSQL driver
pip install psycopg2-binary
```

### Database Setup

#### SQLite (Default):

```yaml
# config.yaml
database:
  enabled: true
  type: sqlite
  # Creates data/embm.db automatically
```

```python
from database import init_database

# Initialize database
init_database()
```

#### PostgreSQL (Production):

```yaml
# config.yaml
database:
  enabled: true
  type: postgresql
  host: localhost
  port: 5432
  name: embm_db
```

```bash
# Set credentials
export EMBM_DB_USER=embm_user
export EMBM_DB_PASSWORD=your_password

# Create database
createdb embm_db

# Initialize schema
python -c "from database import init_database; init_database()"
```

---

## Usage Examples

### 1. Basic Database Operations

```python
from database import init_database, session_scope
from database.models import FrequencyAllocation, Priority, AllocationStatus
from database.repository import AllocationRepository
from datetime import datetime, timedelta

# Initialize database
init_database()

# Create allocation
with session_scope() as session:
    allocation = AllocationRepository.create_allocation(
        session,
        asset_rid="RADAR-01",
        frequency_mhz=3200.0,
        bandwidth_khz=50.0,
        power_dbm=55.0,
        latitude=35.0,
        longitude=45.0,
        start_time=datetime.utcnow(),
        duration_minutes=180,
        priority=Priority.ROUTINE
    )
    print(f"Created allocation: {allocation.allocation_id}")

# Query allocations
with session_scope() as session:
    active = AllocationRepository.get_active_allocations(session)
    print(f"Active allocations: {len(active)}")

    for alloc in active:
        print(f"  - {alloc.asset_rid} @ {alloc.frequency_mhz} MHz")
```

### 2. Analytics Queries

```python
from database import session_scope
from database.repository import Analytics
from datetime import datetime, timedelta

with session_scope() as session:
    # Deconfliction stats for last 7 days
    stats = Analytics.get_deconfliction_stats(
        session,
        since=datetime.utcnow() - timedelta(days=7)
    )

    print(f"Deconfliction Statistics (7 days):")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Approved: {stats['approved']}")
    print(f"  Denied: {stats['denied']}")
    print(f"  Approval Rate: {stats['approval_rate']:.2%}")

    # Agent performance
    performance = Analytics.get_agent_performance(session)
    print(f"\nAgent Performance:")
    print(f"  Avg Duration: {performance['avg_duration']:.2f}s")
    print(f"  Avg Iterations: {performance['avg_iterations']:.1f}")

    # ROE violations
    violations = Analytics.get_roe_violation_summary(session)
    print(f"\nROE Violations:")
    print(f"  Total: {violations['total_violations']}")
    print(f"  Critical: {violations['critical']}")
```

### 3. Metrics Collection

```python
from metrics import metrics

# In your agent code
start_time = time.time()
result = agent.run(message)
duration = time.time() - start_time

metrics.record_agent_session(
    agent_name="Spectrum Manager",
    duration=duration,
    iterations=3,
    tool_calls=5,
    status="COMPLETED"
)

# In deconfliction code
metrics.record_deconfliction(
    asset_type="RADAR",
    priority="ROUTINE",
    status="APPROVED",
    duration=1.2
)

# ROE violations
if violations:
    for violation in violations:
        metrics.record_roe_violation(
            violation_type="RESTRICTED_ZONE",
            severity="HIGH"
        )
```

### 4. Metrics Export for Prometheus

```python
from fastapi import FastAPI, Response
from metrics import metrics

app = FastAPI()

@app.get("/metrics")
def prometheus_metrics():
    """Prometheus scrape endpoint."""
    return Response(
        content=metrics.get_metrics(),
        media_type="text/plain"
    )

# Prometheus will scrape http://localhost:9090/metrics
```

---

## Production Configuration

### Database Configuration

**SQLite (Development/Small Deployments):**
```yaml
database:
  enabled: true
  type: sqlite
  # Automatic file creation in data/ directory
```

**PostgreSQL (Production):**
```yaml
database:
  enabled: true
  type: postgresql
  host: db.example.com
  port: 5432
  name: embm_production

# Set via environment:
# EMBM_DB_USER=embm_prod
# EMBM_DB_PASSWORD=<secure_password>
```

### Metrics Configuration

```yaml
metrics:
  enabled: true

  prometheus:
    enabled: true
    port: 9090
    path: /metrics

  collect:
    - agent_execution_time
    - llm_cache_hit_rate
    - mcp_tool_call_count
    - deconfliction_approval_rate
    - roe_violation_count
    - message_broker_throughput
```

### Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'embm-j-ds'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']
        labels:
          environment: 'production'
          system: 'embm-j-ds'
```

---

## Database Schema Details

### FrequencyAllocation Table

Stores all frequency allocation requests and their lifecycle.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| allocation_id | String(255) | Unique allocation identifier (UUID) |
| asset_rid | String(255) | Asset reference ID |
| frequency_mhz | Float | Center frequency in MHz |
| bandwidth_khz | Float | Bandwidth in kHz |
| power_dbm | Float | Transmit power in dBm |
| latitude | Float | Geographic latitude |
| longitude | Float | Geographic longitude |
| start_time | DateTime | Allocation start time |
| end_time | DateTime | Allocation end time |
| duration_minutes | Integer | Duration in minutes |
| priority | Enum | ROUTINE, PRIORITY, IMMEDIATE, FLASH |
| purpose | Text | Purpose/description |
| status | Enum | PENDING, APPROVED, DENIED, CONFLICT, EXPIRED |
| approval_time | DateTime | When approved (nullable) |
| approved_by | String(255) | Approving agent/system |
| created_at | DateTime | Record creation time |
| updated_at | DateTime | Last update time |

**Indexes:**
- `allocation_id` (unique)
- `asset_rid`
- `frequency_mhz`
- `start_time`
- `priority`
- `status`

---

### DeconflictionDecision Table

Stores all deconfliction analysis and decisions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| decision_id | String(255) | Unique decision identifier (UUID) |
| allocation_id | Integer | Foreign key to allocation |
| asset_rid | String(255) | Asset reference ID (denormalized) |
| frequency_mhz | Float | Frequency (denormalized) |
| priority | Enum | Priority level |
| status | Enum | Decision outcome |
| decision_time | DateTime | When decision was made |
| decided_by | String(255) | Decision maker |
| conflict_count | Integer | Number of conflicts found |
| conflicting_allocations | JSON | List of conflicting allocation IDs |
| roe_violations | JSON | List of ROE violations |
| roe_compliant | Boolean | ROE compliance status |
| reasoning | Text | LLM reasoning for decision |
| alternatives_considered | JSON | Alternative frequencies/times |
| created_at | DateTime | Record creation time |

**Indexes:**
- `decision_id` (unique)
- `asset_rid`
- `frequency_mhz`
- `status`
- `decision_time`

---

### AgentSession Table

Tracks agent execution sessions and performance.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| session_id | String(255) | Unique session identifier (UUID) |
| agent_name | String(255) | Agent name |
| agent_role | String(255) | Agent role description |
| agent_provider | String(100) | LLM provider |
| start_time | DateTime | Session start |
| end_time | DateTime | Session end |
| duration_seconds | Float | Execution duration |
| iterations | Integer | Number of iterations |
| tool_calls | Integer | Number of tool calls |
| llm_calls | Integer | Number of LLM requests |
| cache_hits | Integer | Cache hits |
| cache_misses | Integer | Cache misses |
| status | Enum | RUNNING, COMPLETED, ERROR, TIMEOUT |
| error_message | Text | Error details |
| final_output | Text | Agent's final output |
| input_message | Text | Input message |
| input_length | Integer | Input length in characters |
| tools_used | JSON | List of tools used |
| created_at | DateTime | Record creation time |

**Indexes:**
- `session_id` (unique)
- `agent_name`
- `start_time`
- `status`

---

## Prometheus Metrics Reference

### Deconfliction Metrics

```
# Total deconfliction requests
embm_deconfliction_requests_total{asset_type="RADAR",priority="ROUTINE"} 150

# Approvals
embm_deconfliction_approvals_total{asset_type="RADAR",priority="ROUTINE"} 120

# Denials
embm_deconfliction_denials_total{asset_type="RADAR",priority="ROUTINE",reason="ROE_VIOLATION"} 25

# Processing duration histogram
embm_deconfliction_duration_seconds_bucket{le="1.0"} 50
embm_deconfliction_duration_seconds_bucket{le="5.0"} 120
embm_deconfliction_duration_seconds_sum 180.5
embm_deconfliction_duration_seconds_count 150
```

### Agent Metrics

```
# Agent sessions
embm_agent_sessions_total{agent_name="Spectrum Manager",status="COMPLETED"} 45

# Duration histogram
embm_agent_duration_seconds_bucket{agent_name="Spectrum Manager",le="30.0"} 40
embm_agent_duration_seconds_sum 697.5
embm_agent_duration_seconds_count 45

# Tool calls
embm_agent_tool_calls_total{agent_name="Spectrum Manager",tool_name="get_spectrum_plan"} 45
```

### System Health Metrics

```
# Active agents (gauge)
embm_active_agents 3

# MCP server status (gauge)
embm_mcp_server_up 1

# Web dashboard clients (gauge)
embm_web_dashboard_clients 2
```

---

## Grafana Dashboard Example

### Metrics to Visualize

1. **Deconfliction Success Rate**
   - Query: `rate(embm_deconfliction_approvals_total[5m]) / rate(embm_deconfliction_requests_total[5m])`
   - Panel: Gauge (0-100%)

2. **Agent Performance**
   - Query: `histogram_quantile(0.95, rate(embm_agent_duration_seconds_bucket[5m]))`
   - Panel: Graph (95th percentile duration)

3. **LLM Cache Hit Rate**
   - Query: `rate(embm_llm_cache_hits_total[5m]) / (rate(embm_llm_cache_hits_total[5m]) + rate(embm_llm_cache_misses_total[5m]))`
   - Panel: Gauge (0-100%)

4. **ROE Violations**
   - Query: `sum by (severity) (rate(embm_roe_violations_total[1h]))`
   - Panel: Bar chart by severity

---

## Migration from Previous Phases

### Add Database to Existing System

```python
# 1. Install dependencies
# pip install sqlalchemy

# 2. Add to your existing workflow
from database import init_database, session_scope
from database.repository import AllocationRepository, DeconflictionRepository

# 3. Initialize at startup
init_database()

# 4. Store decisions
with session_scope() as session:
    decision = DeconflictionRepository.create_decision(
        session,
        asset_rid="RADAR-01",
        frequency_mhz=3200.0,
        priority=Priority.ROUTINE,
        status=AllocationStatus.APPROVED
    )
```

### Add Metrics to Existing System

```python
# 1. Install dependency
# pip install prometheus-client

# 2. Import metrics
from metrics import metrics

# 3. Add metrics to your code
@app.get("/api/deconfliction")
def request_deconfliction(...):
    start = time.time()

    # Your existing code
    result = perform_deconfliction(...)

    # Add metrics
    duration = time.time() - start
    metrics.record_deconfliction(
        asset_type="RADAR",
        priority="ROUTINE",
        status=result.status,
        duration=duration
    )

    return result

# 4. Add metrics endpoint
@app.get("/metrics")
def prometheus_metrics():
    return Response(
        content=metrics.get_metrics(),
        media_type="text/plain"
    )
```

---

## Summary

Phase 5 provides:

✅ **Database Persistence**
- All system activity stored in SQL database
- Full audit trail for compliance
- Historical analysis capabilities

✅ **Analytics & Reporting**
- Deconfliction success rates
- Agent performance metrics
- ROE compliance tracking
- Frequency usage analysis

✅ **Prometheus Metrics**
- 20+ metrics for monitoring
- Grafana dashboard integration
- Production-ready alerting

✅ **Production Ready**
- Scalable database backend
- Comprehensive metrics
- Performance monitoring
- Audit capabilities

**Benefits:**
- Historical analysis and trends
- Performance optimization insights
- Compliance and audit support
- Production monitoring and alerting
- Data-driven decision making

**Next Steps:**
- Deploy to production environment
- Set up Grafana dashboards
- Configure alerting rules
- Train operators on analytics tools
