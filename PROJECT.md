EMBM-J DS Multi-Agent Prototype: Complete Project Plan
Version: 1.0
Date: October 16, 2025
Duration: 16 weeks

Table of Contents

Executive Summary
Project Context
Phase 0: Foundation & Requirements (Weeks 1-2)
Phase 1: Mock EMBM-J DS MCP Server (Weeks 3-5)
Phase 2: Agent Foundation & MCP Integration (Weeks 6-9)
Phase 3: Multi-Agent Collaboration (Weeks 10-13)
Phase 4: Validation, Comparison & Documentation (Weeks 14-16)
Resource Requirements
Risk Management
Success Metrics
Timeline Summary


Executive Summary
Goal
Demonstrate external AI agents collaborating via MCP (Model Context Protocol) to interact with a mock EMBM-J DS (Electromagnetic Battle Management - Joint Decision Support) application, proving viability for electromagnetic spectrum operations workflows while establishing reusable patterns for future Palantir integration.
Key Objectives

Demonstrate MCP Integration - Prove agents can interact with external systems via standardized protocol
Show Multi-Agent Coordination - Agents collaborate, negotiate, and resolve conflicts
Prove EMBM Workflow Capability - Agents handle realistic spectrum management scenarios
Create Reusable Methodology - Document patterns for future AI agent development
Compare LLM Providers - Quantify differences between Claude and GPT-4

Architecture Overview

Three specialized agents: Spectrum Manager, ISR Collection Manager, EW Planner
External to Palantir: Agents built with Python/LangChain for this prototype
Communication: Agent-to-agent via broker pattern, agent-to-system via MCP
LLM Flexibility: Abstraction layer supports multiple providers (Anthropic, OpenAI)
Mock EMBM: Realistic simulation with business logic, not just static responses

Core Risk
Validating that agents can handle real EMBM workflows requires significant domain expertise that may not exist in the team.

Project Context
Background
This prototype is based on the architectural concepts described in "Cognitive Dominance in the Spectrum: A Multi-Agent System Architecture for Joint Electromagnetic Battle Management on the Palantir Platform." However, this prototype:

Uses external agents (not Palantir AIP) to prove concepts independently
Focuses on MCP integration as the interoperability layer
Creates a mock EMBM-J DS application (not the real system)
Establishes methodology and patterns for future production implementation

Future Path
While this prototype is external to Palantir, the learnings and patterns will inform:

Integration of these agents into Palantir AIP
Use of Palantir Ontology as the digital twin
Migration path from external to embedded agents
Production deployment considerations


Phase 0: Foundation & Requirements (Weeks 1-2)
Objectives

Gather sufficient EMBM-J DS domain knowledge
Define specific workflows to demonstrate
Establish development methodology
Set up technical infrastructure


0.1 Domain Knowledge Acquisition
Why this matters: Without understanding real spectrum management workflows, we'll build technically correct but operationally meaningless agents.
Activities
Interview SMEs (if available):

Spectrum managers
ISR collection managers
EW planners
Joint operations center personnel

Document Review:

AFDP 3-85 (Electromagnetic Spectrum Operations)
Joint Publication 3-85
EMBM-J DS documentation (if available)
Operational scenarios and vignettes

Define 3-5 Core Workflows:

Frequency Deconfliction Request/Approval

Actor: Asset operator requests frequency
Process: Spectrum Manager checks allocations, approves/denies
Complexity: Low (good starting point)


Pop-Up Threat Detection → ISR Retasking

Actor: EMBM detects new emitter
Process: ISR Manager assesses threat, tasks sensor
Complexity: Medium (involves coordination)


Joint Mission Planning with Spectrum Constraints

Actor: Mission planner needs spectrum for strike package
Process: Multiple agents coordinate allocations
Complexity: High (multi-agent negotiation)


Interference Resolution Across Services

Actor: Interference detected
Process: Identify source, negotiate resolution
Complexity: Medium (conflict resolution)


Electronic Warfare COA Planning

Actor: Threat identified
Process: EW Planner generates jamming options, analyzes impact
Complexity: Medium (COA analysis)



Deliverables
Workflow Specification Document containing:

Actor roles and responsibilities
Step-by-step process flows
Decision points and branching logic
Required data inputs/outputs
Constraints (ROE, policies, physics)
Success/failure criteria
Edge cases and error conditions

Format example:
markdown## Workflow: Frequency Deconfliction

### Actors
- Asset Operator (external to system)
- Spectrum Manager Agent
- EMBM-J DS System

### Preconditions
- Asset needs frequency allocation
- Asset location and parameters known

### Steps
1. Operator submits deconfliction request to EMBM
2. EMBM notifies Spectrum Manager Agent
3. Agent queries current spectrum plan (MCP call)
4. Agent checks for conflicts:
   - Frequency overlap?
   - Geographic proximity?
   - Time window conflict?
5. Agent evaluates request against policy
6. If approved: allocate frequency (MCP call)
7. If denied: provide justification
8. EMBM notifies operator of decision

### Success Criteria
- Correct conflict detection
- Valid justification for decision
- Completes within 10 seconds

### Edge Cases
- Multiple simultaneous requests
- Conflicting priority levels
- ROE violations
```

---

### 0.2 Architecture Design Document

#### System Architecture

**Component Diagram:**
```
┌─────────────────────────────────────────────────┐
│                 Agent System                     │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   Spectrum   │  │     ISR      │            │
│  │   Manager    │  │  Collection  │            │
│  │    Agent     │  │    Manager   │            │
│  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                     │
│         └────────┬─────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │  Agent Broker   │                     │
│         │ (Message Bus)   │                     │
│         └────────┬────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │   EW Planner    │                     │
│         │     Agent       │                     │
│         └────────┬────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │   MCP Client    │                     │
│         │    Library      │                     │
│         └────────┬────────┘                     │
└──────────────────┼──────────────────────────────┘
                   │ MCP Protocol
                   │ (JSON-RPC 2.0)
┌──────────────────▼──────────────────────────────┐
│         Mock EMBM-J DS MCP Server                │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │           Tool Endpoints                  │  │
│  │  - get_spectrum_plan                     │  │
│  │  - request_deconfliction                 │  │
│  │  - analyze_coa_impact                    │  │
│  │  - allocate_frequency                    │  │
│  │  - report_emitter                        │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │         Business Logic Layer              │  │
│  │  - Deconfliction algorithm               │  │
│  │  - ROE constraint engine                 │  │
│  │  - EM propagation models                 │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │          Data Layer                       │  │
│  │  - Current allocations                   │  │
│  │  - Emitter database                      │  │
│  │  - Pending requests                      │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
Agent Architecture
Individual Agent Structure (LangGraph):
pythonAgent Components:
├── System Prompt (role, expertise, constraints)
├── LLM Provider (Anthropic/OpenAI via abstraction)
├── Tool Set
│   ├── MCP Tools (call EMBM functions)
│   ├── Collaboration Tools (send messages to other agents)
│   └── Reasoning Tools (internal calculations)
├── State Graph (LangGraph workflow)
│   ├── Nodes (processing steps)
│   └── Edges (transitions)
└── Memory/Context
    ├── Conversation history
    └── Current state
```

#### Technology Stack

**Core Technologies:**
- **Python 3.11+** - Primary language
- **LangChain/LangGraph** - Agent orchestration framework
- **Anthropic API** - Primary LLM (Claude Sonnet 4)
- **OpenAI API** - Secondary LLM (GPT-4 Turbo) for comparison
- **FastAPI** - Mock EMBM-J DS server
- **Pydantic** - Data validation and schemas
- **Asyncio** - Asynchronous operations
- **Pytest** - Testing framework

**Infrastructure:**
- **Git/GitHub** - Version control
- **Docker** - Containerization (optional)
- **AWS/GCP** - Cloud hosting for demo
- **Logging:** Structured JSON logs
- **Monitoring:** Custom dashboard (simple web app)

#### Key Design Decisions

**Decision 1: External Agents vs. Palantir AIP**
- **Choice:** External agents using LangChain
- **Rationale:** 
  - Faster prototyping without Palantir dependencies
  - Easier LLM provider comparison
  - Transferable patterns for future Palantir integration
  - Lower barrier to entry for team

**Decision 2: MCP as Integration Layer**
- **Choice:** Use MCP protocol for all agent-to-EMBM communication
- **Rationale:**
  - Open standard, future-proof
  - Clean separation of concerns
  - Same pattern can work with real EMBM-J DS
  - Testable in isolation

**Decision 3: Broker Pattern for Agent Communication**
- **Choice:** Central message broker, not direct agent-to-agent
- **Rationale:**
  - Better observability (all messages logged)
  - Loose coupling (agents don't need to know about each other)
  - Easier to add/remove agents
  - Message prioritization and filtering capabilities

**Decision 4: LLM Abstraction Layer**
- **Choice:** Provider-agnostic interface
- **Rationale:**
  - Easy comparison between providers
  - A/B testing capability
  - Cost optimization flexibility
  - Resilience (failover to backup provider)

#### Future Palantir Integration Considerations

**Migration Path:**

**Phase 1: Current Prototype (External)**
- Agents external to Palantir
- MCP to mock EMBM
- Independent development

**Phase 2: Hybrid Integration**
- Migrate agents to Palantir AIP Agent Studio
- Keep MCP connection to real EMBM-J DS
- Use Palantir Ontology for state management
- Leverage Palantir security model

**Phase 3: Full Integration**
- EMBM-J DS integrated into Palantir platform
- Agents interact with Ontology directly
- Unified security and governance
- Production deployment

**Design Principles to Maintain:**
- Clean separation between agent logic and communication
- Well-defined interfaces (can swap implementations)
- Comprehensive logging (for migration debugging)
- Modular architecture (components can be reused)

#### Deliverables

**Architecture Decision Records (ADRs):**
- Document each major decision
- Rationale, alternatives considered, tradeoffs
- Update as decisions evolve

**Architecture Diagram:**
- Component diagram (above)
- Sequence diagrams for key workflows
- Data flow diagrams

**Design Document:**
- System overview
- Component descriptions
- Interface specifications
- Deployment considerations

---

### 0.3 Development Environment Setup

#### Project Structure
```
embm-agent-prototype/
├── README.md
├── PROJECT_PLAN.md
├── ARCHITECTURE.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── docker-compose.yml (optional)
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── spectrum_manager/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── isr_manager/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   └── ew_planner/
│       ├── __init__.py
│       ├── agent.py
│       ├── prompts.py
│       └── tools.py
│
├── mcp_server/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── tools.py
│   ├── business_logic/
│   │   ├── __init__.py
│   │   ├── deconfliction.py
│   │   ├── roe_engine.py
│   │   └── propagation.py
│   └── data/
│       ├── __init__.py
│       ├── allocations.py
│       ├── emitters.py
│       └── requests.py
│
├── mcp_client/
│   ├── __init__.py
│   ├── client.py
│   ├── transport.py
│   └── embm_tools.py
│
├── llm_abstraction/
│   ├── __init__.py
│   ├── provider.py
│   ├── anthropic_provider.py
│   ├── openai_provider.py
│   └── registry.py
│
├── broker/
│   ├── __init__.py
│   ├── broker.py
│   ├── messages.py
│   └── queue.py
│
├── workflows/
│   ├── __init__.py
│   ├── frequency_allocation.py
│   ├── popup_threat.py
│   └── mission_planning.py
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── evaluation/
│   ├── __init__.py
│   ├── test_cases.py
│   ├── validators.py
│   └── comparison.py
│
├── docs/
│   ├── workflow_specs/
│   ├── adr/  (Architecture Decision Records)
│   └── methodology/
│
└── scripts/
    ├── setup.sh
    ├── run_server.py
    ├── run_agents.py
    └── demo.py
Dependencies (pyproject.toml)
toml[project]
name = "embm-agent-prototype"
version = "0.1.0"
description = "Multi-agent system for EMBM-J DS via MCP"
requires-python = ">=3.11"

dependencies = [
    "langchain>=0.1.0",
    "langgraph>=0.0.20",
    "anthropic>=0.18.0",
    "openai>=1.0.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.1.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.optional-dependencies]
dev = [
    "black>=24.0.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "ipython>=8.20.0",
]

dashboard = [
    "streamlit>=1.31.0",  # For simple dashboard
    "plotly>=5.18.0",
]

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true
Environment Configuration
.env.example:
bash# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# MCP Server
EMBM_SERVER_URL=http://localhost:8000
EMBM_SERVER_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Agent Configuration
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-sonnet-4-20250514
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=60

# Broker Configuration
MESSAGE_QUEUE_SIZE=1000
MESSAGE_RETENTION_HOURS=24

# Development
DEBUG=false
Setup Scripts
scripts/setup.sh:
bash#!/bin/bash

echo "Setting up EMBM Agent Prototype..."

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev,dashboard]"

# Create .env from template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please add your API keys."
fi

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p evaluation/results

echo "Setup complete! Activate with: source venv/bin/activate"
Initial Documentation
README.md:
markdown# EMBM-J DS Multi-Agent Prototype

Demonstration of AI agents collaborating via MCP to manage electromagnetic 
spectrum operations.

## Quick Start
```bash
# Setup
./scripts/setup.sh
source venv/bin/activate

# Configure API keys
cp .env.example .env
# Edit .env and add your keys

# Start MCP server
python scripts/run_server.py

# (In another terminal) Run agents
python scripts/run_agents.py --workflow frequency_allocation
```

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## Workflows

- **Frequency Allocation**: Single agent approves spectrum requests
- **Pop-up Threat**: Multi-agent coordination for threat response
- **Mission Planning**: Complex negotiation scenario

## Development
```bash
# Run tests
pytest

# Format code
black .
ruff check .

# Type checking
mypy agents/ mcp_server/
```

## Documentation

- [Project Plan](PROJECT_PLAN.md)
- [Architecture](ARCHITECTURE.md)
- [Workflow Specifications](docs/workflow_specs/)
- [Methodology](docs/methodology/)
Deliverables

✅ Complete project structure created
✅ Dependencies configured (pyproject.toml)
✅ Development environment setup (virtual env, scripts)
✅ Initial documentation (README, structure)
✅ Git repository initialized with .gitignore
✅ Configuration templates (.env.example)

Phase 0 Complete: Foundation established, ready to begin implementation

Phase 1: Mock EMBM-J DS MCP Server (Weeks 3-5)
Objectives

Create a functional mock of EMBM-J DS that acts as an MCP server
Implement core tools that agents will call
Establish realistic data models and constraints
Enable testing without real EMBM infrastructure


1.1 Core MCP Server Implementation (Week 3)
MCP Tools Specification
Based on the document (Table p.12-13), implement these tools:
Tool 1: get_spectrum_plan
pythonInput Schema:
{
    "ao_geojson": str,        # GeoJSON polygon
    "start_time": datetime,
    "end_time": datetime
}

Output Schema:
{
    "plan_id": str,
    "allocations": [
        {
            "asset_id": str,
            "frequency_mhz": float,
            "bandwidth_khz": float,
            "location": {"lat": float, "lon": float},
            "start_time": datetime,
            "end_time": datetime,
            "service": str  # "Air Force", "Navy", etc.
        }
    ]
}
Tool 2: request_deconfliction
pythonInput Schema:
{
    "asset_rid": str,
    "frequency_mhz": float,
    "bandwidth_khz": float,
    "power_dbm": float,
    "location": {"lat": float, "lon": float},
    "start_time": datetime,
    "duration_minutes": int,
    "priority": str,  # "ROUTINE", "PRIORITY", "IMMEDIATE"
    "purpose": str
}

Output Schema:
{
    "request_id": str,
    "status": str,  # "APPROVED", "DENIED", "PENDING", "CONFLICT"
    "conflict_details": [
        {
            "conflicting_asset": str,
            "conflict_type": str,  # "FREQUENCY", "GEOGRAPHIC", "TIME"
            "severity": float  # 0.0-1.0
        }
    ],
    "alternative_frequencies": [float],  # Suggested alternatives
    "justification": str
}
Tool 3: analyze_coa_impact
pythonInput Schema:
{
    "coa_id": str,
    "friendly_actions": [
        {
            "action_type": str,  # "JAMMING", "COMMUNICATION", "RADAR"
            "asset_id": str,
            "frequency_mhz": float,
            "power_dbm": float,
            "location": {"lat": float, "lon": float},
            "duration_minutes": int
        }
    ]
}

Output Schema:
{
    "analysis_id": str,
    "impact_score": float,  # 0.0-1.0 (higher = better outcome)
    "risk_summary": str,
    "affected_friendly_assets": [
        {
            "asset_id": str,
            "impact_type": str,  # "INTERFERENCE", "DETECTION_RISK"
            "severity": float
        }
    ],
    "enemy_effects": {
        "probability_of_degradation": float,
        "affected_systems": [str]
    },
    "roe_violations": [str]  # Empty if compliant
}
Tool 4: get_interference_report
pythonInput Schema:
{
    "location": {"lat": float, "lon": float},
    "frequency_range_mhz": {"min": float, "max": float}
}

Output Schema:
{
    "report_id": str,
    "interference_sources": [
        {
            "source_id": str,
            "frequency_mhz": float,
            "estimated_power_dbm": float,
            "azimuth_degrees": float,
            "interference_level": float  # 0.0-1.0
        }
    ],
    "total_noise_floor": float
}
Tool 5: allocate_frequency
pythonInput Schema:
{
    "asset_id": str,
    "frequency_mhz": float,
    "bandwidth_khz": float,
    "duration_minutes": int,
    "authorization_id": str  # From successful deconfliction request
}

Output Schema:
{
    "allocation_id": str,
    "status": str,  # "SUCCESS", "FAILED"
    "expires_at": datetime,
    "message": str
}
Tool 6: report_emitter
pythonInput Schema:
{
    "location": {"lat": float, "lon": float},
    "frequency_mhz": float,
    "bandwidth_khz": float,
    "signal_characteristics": {
        "waveform": str,
        "prf_hz": Optional[float],  # Pulse repetition frequency
        "modulation": str
    },
    "detection_time": datetime,
    "confidence": float  # 0.0-1.0
}

Output Schema:
{
    "emitter_id": str,
    "threat_assessment": {
        "threat_type": str,  # "RADAR", "JAMMER", "COMMUNICATIONS"
        "threat_level": str,  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
        "matches_known_system": Optional[str]  # e.g., "S-400 radar"
    }
}
FastAPI Server Implementation
mcp_server/main.py:
pythonfrom fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import structlog

from .tools import (
    get_spectrum_plan,
    request_deconfliction,
    analyze_coa_impact,
    allocate_frequency,
    report_emitter,
    get_interference_report
)

app = FastAPI(title="EMBM-J DS MCP Server")
logger = structlog.get_logger()

# MCP JSON-RPC 2.0 endpoint
@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """
    MCP protocol endpoint
    Accepts JSON-RPC 2.0 formatted requests
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    
    logger.info("mcp_call", method=method, params=params)
    
    # Route to appropriate tool
    tool_map = {
        "get_spectrum_plan": get_spectrum_plan,
        "request_deconfliction": request_deconfliction,
        "analyze_coa_impact": analyze_coa_impact,
        "allocate_frequency": allocate_frequency,
        "report_emitter": report_emitter,
        "get_interference_report": get_interference_report
    }
    
    if method not in tool_map:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": "Method not found"},
            "id": request_id
        }
    
    try:
        result = await tool_map[method](**params)
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
    except Exception as e:
        logger.error("tool_error", method=method, error=str(e))
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": request_id
        }

# Introspection endpoint (list available tools)
@app.get("/mcp/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "get_spectrum_plan",
                "description": "Retrieve current spectrum allocation plan",
                "input_schema": {...}
            },
            # ... other tools
        ]
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}
Data Models
mcp_server/models.py:
pythonfrom pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    altitude_m: Optional[float] = None

class FrequencyAllocation(BaseModel):
    allocation_id: str
    asset_id: str
    frequency_mhz: float = Field(..., gt=0)
    bandwidth_khz: float = Field(..., gt=0)
    location: Location
    start_time: datetime
    end_time: datetime
    service: str  # "Air Force", "Navy", "Army", "Marines"
    priority: str
    power_dbm: float

class ConflictType(str, Enum):
    FREQUENCY = "FREQUENCY"
    GEOGRAPHIC = "GEOGRAPHIC"
    TIME = "TIME"
    POLICY = "POLICY"

class Conflict(BaseModel):
    conflicting_asset: str
    conflict_type: ConflictType
    severity: float = Field(..., ge=0, le=1)
    description: str

class DeconflictionStatus(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"

class DeconflictionRequest(BaseModel):
    request_id: str
    asset_rid: str
    frequency_mhz: float
    bandwidth_khz: float
    power_dbm: float
    location: Location
    start_time: datetime
    duration_minutes: int
    priority: str
    purpose: str
    submitted_at: datetime

class Emitter(BaseModel):
    emitter_id: str
    location: Location
    frequency_mhz: float
    bandwidth_khz: float
    signal_characteristics: dict
    detection_time: datetime
    confidence: float = Field(..., ge=0, le=1)
    threat_assessment: Optional[dict] = None
In-Memory State Management
mcp_server/data/allocations.py:
pythonfrom typing import Dict, List
from ..models import FrequencyAllocation
from datetime import datetime
import asyncio

class AllocationStore:
    """
    In-memory storage for current spectrum allocations
    """
    def __init__(self):
        self._allocations: Dict[str, FrequencyAllocation] = {}
        self._lock = asyncio.Lock()
    
    async def add(self, allocation: FrequencyAllocation):
        async with self._lock:
            self._allocations[allocation.allocation_id] = allocation
    
    async def get_active_allocations(self, at_time: datetime) -> List[FrequencyAllocation]:
        async with self._lock:
            return [
                alloc for alloc in self._allocations.values()
                if alloc.start_time <= at_time <= alloc.end_time
            ]
    
    async def get_by_frequency_range(
        self, 
        min_freq: float, 
        max_freq: float,
        at_time: datetime
    ) -> List[FrequencyAllocation]:
        active = await self.get_active_allocations(at_time)
        return [
            alloc for alloc in active
            if (alloc.frequency_mhz >= min_freq and 
                alloc.frequency_mhz <= max_freq)
        ]
    
    async def clear_expired(self, current_time: datetime):
        async with self._lock:
            self._allocations = {
                aid: alloc for aid, alloc in self._allocations.items()
                if alloc.end_time > current_time
            }

# Global instance
allocation_store = AllocationStore()
Activities

✅ Implement FastAPI server with MCP endpoint
✅ Define all tool input/output schemas with Pydantic
✅ Create data models for allocations, requests, emitters
✅ Implement in-memory state stores
✅ Add structured logging
✅ Write unit tests for each tool
✅ Create Postman/curl examples for manual testing

Deliverables

Running MCP server on localhost:8000
All 6 tools implemented and testable
Documentation of each tool's API
Unit tests with >80% coverage


1.2 Realistic Business Logic & Constraints (Week 4)
The mock must apply realistic rules to be meaningful for agent testing.
Deconfliction Algorithm
mcp_server/business_logic/deconfliction.py:
pythonfrom typing import List, Tuple
from ..models import FrequencyAllocation, Conflict, ConflictType
import math

class DeconflictionEngine:
    """
    Implements realistic frequency deconfliction logic
    """
    
    def __init__(self):
        # Configuration
        self.min_frequency_separation_mhz = 5.0  # Minimum safe separation
        self.min_geographic_separation_km = 50.0  # Minimum distance
        self.interference_threshold_db = -90.0   # Receiver sensitivity
    
    async def check_conflicts(
        self,
        proposed: FrequencyAllocation,
        existing: List[FrequencyAllocation]
    ) -> List[Conflict]:
        """
        Check for conflicts with existing allocations
        """
        conflicts = []
        
        for alloc in existing:
            # Check time overlap
            if not self._time_overlaps(proposed, alloc):
                continue
            
            # Check frequency proximity
            freq_separation = abs(proposed.frequency_mhz - alloc.frequency_mhz)
            
            # Check geographic proximity
            distance_km = self._calculate_distance(
                proposed.location, 
                alloc.location
            )
            
            # Determine if this is a conflict
            if freq_separation < self.min_frequency_separation_mhz:
                # Frequency overlap - check if geographic separation saves us
                if distance_km < self.min_geographic_separation_km:
                    conflicts.append(Conflict(
                        conflicting_asset=alloc.asset_id,
                        conflict_type=ConflictType.FREQUENCY,
                        severity=self._calculate_interference_severity(
                            freq_separation,
                            distance_km,
                            proposed.power_dbm,
                            alloc.power_dbm
                        ),
                        description=f"Frequency overlap with {alloc.asset_id}"
                    ))
        
        return conflicts
    
    def _calculate_distance(self, loc1, loc2) -> float:
        """Haversine distance in km"""
        R = 6371  # Earth radius in km
        
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_interference_severity(
        self,
        freq_sep_mhz: float,
        distance_km: float,
        power1_dbm: float,
        power2_dbm: float
    ) -> float:
        """
        Calculate interference severity (0.0-1.0)
        Uses simplified path loss model
        """
        # Free space path loss (simplified)
        frequency_mhz = 1000  # Approximate
        path_loss_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz) + 32.45
        
        # Received power at victim receiver
        received_power_dbm = power2_dbm - path_loss_db
        
        # Interference margin
        interference_margin_db = received_power_dbm - self.interference_threshold_db
        
        # Frequency selectivity (simplified)
        freq_rejection_db = freq_sep_mhz * 2  # 2 dB per MHz separation
        
        effective_interference = interference_margin_db - freq_rejection_db
        
        # Map to 0.0-1.0
        if effective_interference <= 0:
            return 0.0
        elif effective_interference >= 20:
            return 1.0
        else:
            return effective_interference / 20.0
    
    def _time_overlaps(self, alloc1, alloc2) -> bool:
        return not (alloc1.end_time < alloc2.start_time or 
                    alloc2.end_time < alloc1.start_time)
    
    def suggest_alternatives(
        self,
        proposed_freq: float,
        conflicts: List[Conflict],
        frequency_range: Tuple[float, float] = (225.0, 400.0)
    ) -> List[float]:
        """
        Suggest alternative frequencies that avoid conflicts
        """
        alternatives = []
        
        # Try frequencies at 10 MHz intervals
        for freq in range(int(frequency_range[0]), int(frequency_range[1]), 10):
            freq_mhz = float(freq)
            
            # Check if this avoids conflicts
            if all(abs(freq_mhz - conflict.frequency_mhz) > self.min_frequency_separation_mhz 
                   for conflict in conflicts):
                alternatives.append(freq_mhz)
                
                if len(alternatives) >= 3:  # Return top 3
                    break
        
        return alternatives
Rules of Engagement Engine
mcp_server/business_logic/roe_engine.py:
pythonfrom typing import List
from ..models import Location

class ROEEngine:
    """
    Checks operations against Rules of Engagement
    """
    
    def __init__(self):
        # Define restricted frequencies
        self.civilian_frequencies = [
            (88.0, 108.0),    # FM radio
            (118.0, 137.0),   # Aviation
            (162.4, 162.55),  # Weather
            (1575.42, 1575.42) # GPS L1
        ]
        
        # Define protected areas (no-jam zones)
        self.protected_areas = [
            {
                "name": "Hospital Vicinity",
                "center": Location(lat=35.0, lon=-120.0),
                "radius_km": 10.0
            },
            {
                "name": "Civilian Airport",
                "center": Location(lat=36.0, lon=-119.0),
                "radius_km": 50.0
            }
        ]
    
    async def check_compliance(
        self,
        action_type: str,
        frequency_mhz: float,
        location: Location,
        target: Optional[Location] = None
    ) -> List[str]:
        """
        Check if action violates ROE
        Returns list of violations (empty if compliant)
        """
        violations = []
        
        # Check civilian frequency protection
        if action_type == "JAMMING":
            for freq_range in self.civilian_frequencies:
                if freq_range[0] <= frequency_mhz <= freq_range[1]:
                    violations.append(
                        f"VIOLATION: Cannot jam civilian frequency {frequency_mhz} MHz"
                    )
        
        # Check protected area restrictions
        for area in self.protected_areas:
            distance = self._calculate_distance(location, area["center"])
            if distance < area["radius_km"]:
                violations.append(
                    f"VIOLATION: Operation within protected area '{area['name']}'"
                )
        
        # Check proportionality (simplified)
        if action_type == "JAMMING" and target:
            # Ensure military necessity
            # (In reality, this would be much more complex)
            pass
        
        return violations
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Reuse distance calculation from deconfliction"""
        # (same haversine implementation)
        pass
COA Impact Analysis
mcp_server/business_logic/coa_analysis.py:
pythonfrom typing import List, Dict
from ..models import Location

class COAAnalyzer:
    """
    Analyzes Course of Action electromagnetic impact
    """
    
    def __init__(self, deconfliction_engine, roe_engine):
        self.deconfliction = deconfliction_engine
        self.roe = roe_engine
    
    async def analyze_coa(
        self,
        coa_id: str,
        friendly_actions: List[dict],
        friendly_assets: List[dict],
        enemy_systems: List[dict]
    ) -> dict:
        """
        Comprehensive COA analysis
        """
        # Check ROE compliance
        roe_violations = []
        for action in friendly_actions:
            violations = await self.roe.check_compliance(
                action["action_type"],
                action["frequency_mhz"],
                action["location"]
            )
            roe_violations.extend(violations)
        
        # Analyze friendly interference
        friendly_impacts = await self._analyze_friendly_impacts(
            friendly_actions,
            friendly_assets
        )
        
        # Estimate enemy degradation
        enemy_effects = await self._estimate_enemy_effects(
            friendly_actions,
            enemy_systems
        )
        
        # Calculate overall impact score
        impact_score = self._calculate_impact_score(
            roe_violations,
            friendly_impacts,
            enemy_effects
        )
        
        return {
            "analysis_id": f"{coa_id}_analysis",
            "impact_score": impact_score,
            "risk_summary": self._generate_risk_summary(
                friendly_impacts,
                enemy_effects
            ),
            "affected_friendly_assets": friendly_impacts,
            "enemy_effects": enemy_effects,
            "roe_violations": roe_violations
        }
    
    async def _analyze_friendly_impacts(
        self,
        actions: List[dict],
        assets: List[dict]
    ) -> List[dict]:
        """
        Check if our actions interfere with our own systems
        """
        impacts = []
        
        for asset in assets:
            for action in actions:
                # Check frequency overlap
                freq_overlap = abs(
                    action["frequency_mhz"] - asset["frequency_mhz"]
                ) < 10.0
                
                # Check proximity
                distance = self.deconfliction._calculate_distance(
                    action["location"],
                    asset["location"]
                )
                
                if freq_overlap and distance < 100.0:  # Within 100 km
                    impacts.append({
                        "asset_id": asset["asset_id"],
                        "impact_type": "INTERFERENCE",
                        "severity": 0.6  # Simplified
                    })
        
        return impacts
    
    async def _estimate_enemy_effects(
        self,
        actions: List[dict],
        enemy_systems: List[dict]
    ) -> dict:
        """
        Estimate impact on enemy systems
        """
        affected_systems = []
        total_degradation = 0.0
        
        for enemy in enemy_systems:
            for action in actions:
                if action["action_type"] != "JAMMING":
                    continue
                
                # Check if jamming frequency matches enemy system
                if abs(action["frequency_mhz"] - enemy["frequency_mhz"]) < 20.0:
                    distance = self.deconfliction._calculate_distance(
                        action["location"],
                        enemy["location"]
                    )
                    
                    # Calculate burn-through range (simplified)
                    if distance < 50.0:  # Within jamming range
                        affected_systems.append(enemy["system_name"])
                        total_degradation += 0.7
        
        probability_of_degradation = min(total_degradation, 1.0)
        
        return {
            "probability_of_degradation": probability_of_degradation,
            "affected_systems": affected_systems
        }
    
    def _calculate_impact_score(
        self,
        roe_violations: List[str],
        friendly_impacts: List[dict],
        enemy_effects: dict
    ) -> float:
        """
        Overall impact score (higher = better)
        """
        score = 0.5  # Start neutral
        
        # Penalize for ROE violations (severely)
        if roe_violations:
            score -= 0.5
        
        # Penalize for friendly interference
        score -= len(friendly_impacts) * 0.1
        
        # Reward for enemy degradation
        score += enemy_effects["probability_of_degradation"] * 0.4
        
        return max(0.0, min(1.0, score))
    
    def _generate_risk_summary(
        self,
        friendly_impacts: List[dict],
        enemy_effects: dict
    ) -> str:
        summary_parts = []
        
        if friendly_impacts:
            summary_parts.append(
                f"Risk: {len(friendly_impacts)} friendly systems may experience interference"
            )
        
        if enemy_effects["affected_systems"]:
            summary_parts.append(
                f"Benefit: {len(enemy_effects['affected_systems'])} enemy systems degraded"
            )
        
        return ". ".join(summary_parts) if summary_parts else "Minimal risk"
Tool Implementation with Business Logic
mcp_server/tools.py:
pythonfrom .business_logic.deconfliction import DeconflictionEngine
from .business_logic.roe_engine import ROEEngine
from .business_logic.coa_analysis import COAAnalyzer
from .data.allocations import allocation_store
from .models import *
from datetime import datetime, timedelta
import uuid

# Initialize engines
deconfliction_engine = DeconflictionEngine()
roe_engine = ROEEngine()
coa_analyzer = COAAnalyzer(deconfliction_engine, roe_engine)

async def request_deconfliction(
    asset_rid: str,
    frequency_mhz: float,
    bandwidth_khz: float,
    power_dbm: float,
    location: dict,
    start_time: str,
    duration_minutes: int,
    priority: str,
    purpose: str
) -> dict:
    """
    Process a deconfliction request with realistic logic
    """
    # Create proposed allocation
    proposed = FrequencyAllocation(
        allocation_id=str(uuid.uuid4()),
        asset_id=asset_rid,
        frequency_mhz=frequency_mhz,
        bandwidth_khz=bandwidth_khz,
        power_dbm=power_dbm,
        location=Location(**location),
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(start_time) + timedelta(minutes=duration_minutes),
        service="Unknown",  # Could be determined from asset_rid
        priority=priority
    )
    
    # Get existing allocations
    existing = await allocation_store.get_active_allocations(proposed.start_time)
    
    # Check for conflicts
    conflicts = await deconfliction_engine.check_conflicts(proposed, existing)
    
    # Determine status
    if not conflicts:
        status = DeconflictionStatus.APPROVED
        justification = "No conflicts detected. Allocation approved."
    elif any(c.severity > 0.7 for c in conflicts):
        status = DeconflictionStatus.DENIED
        justification = f"High-severity conflicts detected with {len(conflicts)} allocation(s)."
    else:
        status = DeconflictionStatus.PENDING
        justification = "Minor conflicts detected. Manual review required."
    
    # Suggest alternatives if conflicts exist
    alternatives = []
    if conflicts:
        alternatives = deconfliction_engine.suggest_alternatives(
            frequency_mhz,
            conflicts
        )
    
    return {
        "request_id": str(uuid.uuid4()),
        "status": status.value,
        "conflict_details": [
            {
                "conflicting_asset": c.conflicting_asset,
                "conflict_type": c.conflict_type.value,
                "severity": c.severity
            }
            for c in conflicts
        ],
        "alternative_frequencies": alternatives,
        "justification": justification
    }

async def analyze_coa_impact(
    coa_id: str,
    friendly_actions: List[dict]
) -> dict:
    """
    Analyze COA with full business logic
    """
    # In a real system, we'd fetch current friendly/enemy assets
    # For mock, use simplified data
    friendly_assets = [
        {
            "asset_id": "AWACS-01",
            "frequency_mhz": 1090.0,
            "location": Location(lat=35.5, lon=-120.5)
        }
    ]
    
    enemy_systems = [
        {
            "system_name": "S-400 Radar",
            "frequency_mhz": 3000.0,
            "location": Location(lat=36.0, lon=-119.0)
        }
    ]
    
    return await coa_analyzer.analyze_coa(
        coa_id,
        friendly_actions,
        friendly_assets,
        enemy_systems
    )

# ... implement other tools similarly
Activities

✅ Implement deconfliction algorithm with realistic physics
✅ Create ROE constraint engine
✅ Build COA impact analyzer
✅ Add electromagnetic propagation models (path loss, LOS)
✅ Integrate business logic into all tools
✅ Add stochastic elements for realism
✅ Write integration tests with complex scenarios

Deliverables

Business logic modules with >80% test coverage
Realistic responses that require agent reasoning
Integration tests demonstrating complex scenarios
Documentation of all algorithms and parameters


1.3 Observability & Debugging (Week 5)
When agents misbehave, we need to diagnose whether the problem is agent reasoning, MCP communication, or mock server logic.
Structured Logging
Configure structlog:
python# mcp_server/main.py (initialization)
import structlog
import logging
import sys

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

setup_logging()
logger = structlog.get_logger()
Add trace IDs:
pythonfrom contextvars import ContextVar
import uuid

# Context variable for request tracing
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    trace_id_var.set(trace_id)
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

# Use in logging
logger.info(
    "tool_called",
    trace_id=trace_id_var.get(),
    tool="request_deconfliction",
    params=params
)
Admin Endpoints
mcp_server/main.py:
python@app.get("/admin/allocations")
async def get_all_allocations():
    """View all current allocations"""
    allocations = await allocation_store.get_active_allocations(datetime.now())
    return {
        "count": len(allocations),
        "allocations": [alloc.dict() for alloc in allocations]
    }

@app.get("/admin/requests")
async def get_pending_requests():
    """View pending deconfliction requests"""
    # Return from request store
    pass

@app.post("/admin/clear")
async def clear_all_data():
    """Reset server state (for testing)"""
    await allocation_store.clear_all()
    return {"status": "cleared"}

@app.get("/admin/stats")
async def get_statistics():
    """Server statistics"""
    return {
        "uptime_seconds": time.time() - server_start_time,
        "total_requests": request_counter,
        "active_allocations": len(await allocation_store.get_active_allocations(datetime.now())),
        "total_conflicts_detected": conflict_counter
    }
Web Dashboard
dashboard/app.py (using Streamlit):
pythonimport streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="EMBM Mock Server Dashboard", layout="wide")

st.title("EMBM-J DS Mock Server Dashboard")

# Server status
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Server Status", "🟢 Running")

with col2:
    stats = requests.get("http://localhost:8000/admin/stats").json()
    st.metric("Active Allocations", stats["active_allocations"])

with col3:
    st.metric("Total Requests", stats["total_requests"])

# Spectrum allocation visualization
st.header("Current Spectrum Allocations")

allocations = requests.get("http://localhost:8000/admin/allocations").json()

if allocations["allocations"]:
    df = pd.DataFrame(allocations["allocations"])
    
    # Frequency chart
    fig = px.timeline(
        df,
        x_start="start_time",
        x_end="end_time",
        y="frequency_mhz",
        color="service",
        hover_data=["asset_id", "bandwidth_khz", "priority"]
    )
    fig.update_yaxes(title="Frequency (MHz)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Geographic map
    fig_map = px.scatter_geo(
        df,
        lat=[loc["lat"] for loc in df["location"]],
        lon=[loc["lon"] for loc in df["location"]],
        hover_name="asset_id",
        size="power_dbm",
        color="service"
    )
    st.plotly_chart(fig_map, use_container_width=True)

# Agent activity log
st.header("Recent MCP Calls")

# Fetch from logs (would need to implement log streaming)
# For now, placeholder
st.dataframe(pd.DataFrame({
    "Time": ["12:34:56", "12:35:01"],
    "Method": ["request_deconfliction", "get_spectrum_plan"],
    "Agent": ["Spectrum Manager", "ISR Manager"],
    "Status": ["Success", "Success"],
    "Duration (ms)": [150, 80]
}))

# Manual control panel
st.header("Control Panel")

col1, col2 = st.columns(2)

with col1:
    if st.button("Clear All Data"):
        requests.post("http://localhost:8000/admin/clear")
        st.success("Server state cleared")

with col2:
    if st.button("Reload"):
        st.rerun()
Run with:
bashstreamlit run dashboard/app.py
MCP Server Introspection
Add tool discovery endpoint:
python@app.get("/mcp/tools")
async def list_tools():
    """
    Return OpenAPI-style tool definitions
    Allows agents to discover available tools
    """
    return {
        "tools": [
            {
                "name": "get_spectrum_plan",
                "description": "Retrieve current spectrum allocation plan for an area",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ao_geojson": {
                            "type": "string",
                            "description": "GeoJSON polygon defining area of operations"
                        },
                        "start_time": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "end_time": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "required": ["ao_geojson", "start_time", "end_time"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "plan_id": {"type": "string"},
                        "allocations": {"type": "array"}
                    }
                }
            },
            # ... other tools
        ]
    }
Activities

✅ Configure structured JSON logging with trace IDs
✅ Add admin endpoints for inspecting server state
✅ Build Streamlit dashboard for visualization
✅ Implement tool introspection endpoint
✅ Add request/response logging middleware
✅ Create debugging utilities

Deliverables

Observable server with comprehensive logging
Web dashboard showing allocations, conflicts, agent activity
Admin API for inspecting and controlling server state
Documentation for debugging common issues

Phase 1 Complete: Mock EMBM-J DS MCP server is functional, realistic, and observable

Phase 2: Agent Foundation & MCP Integration (Weeks 6-9)
Objectives

Create individual agents with specialized roles
Integrate agents with MCP server
Establish LLM abstraction layer
Prove single-agent workflows function


2.1 LLM Abstraction Layer (Week 6)
Provider Interface
llm_abstraction/provider.py:
pythonfrom abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: str

@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCall]
    finish_reason: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    latency_ms: float

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers
    """
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a completion (for real-time display)
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
Anthropic Provider
llm_abstraction/anthropic_provider.py:
pythonfrom anthropic import AsyncAnthropic
from .provider import LLMProvider, Message, LLMResponse, ToolCall
import time
import os

class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"
        ]
        
        # Extract system message
        system_message = next(
            (msg.content for msg in messages if msg.role == "system"),
            None
        )
        
        # Make API call
        response = await self.client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            system=system_message,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse tool calls
        tool_calls = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_calls.append(ToolCall(
                    name=content_block.name,
                    arguments=content_block.input,
                    id=content_block.id
                ))
        
        # Extract text content
        text_content = ""
        for content_block in response.content:
            if content_block.type == "text":
                text_content += content_block.text
        
        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            latency_ms=latency_ms
        )
    
    async def stream(self, messages, tools=None, **kwargs):
        # Implementation for streaming
        # (similar pattern, using client.messages.stream())
        pass
    
    def name(self) -> str:
        return f"anthropic/{self.model}"
OpenAI Provider
llm_abstraction/openai_provider.py:
pythonfrom openai import AsyncOpenAI
from .provider import LLMProvider, Message, LLMResponse, ToolCall
import time
import os

class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4-turbo"):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
    
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        # Convert to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Make API call
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        message = response.choices[0].message
        
        # Parse tool calls
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    id=tc.id
                ))
        
        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            latency_ms=latency_ms
        )
    
    def name(self) -> str:
        return f"openai/{self.model}"
Provider Registry
llm_abstraction/registry.py:
pythonfrom typing import Dict
from .provider import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
import structlog

logger = structlog.get_logger()

class ProviderRegistry:
    """
    Factory for LLM providers with metrics tracking
    """
    
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._metrics: Dict[str, Dict] = {}
    
    def register(self, name: str, provider: LLMProvider):
        self._providers[name] = provider
        self._metrics[name] = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0
        }
    
    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        return self._providers[name]
    
    def track_call(self, provider_name: str, response: LLMResponse):
        """Track metrics for a provider call"""
        metrics = self._metrics[provider_name]
        
        metrics["total_calls"] += 1
        metrics["total_tokens"] += response.usage["total_tokens"]
        
        # Calculate cost (simplified pricing)
        if "anthropic" in provider_name:
            cost = (
                response.usage["prompt_tokens"] * 0.003 / 1000 +
                response.usage["completion_tokens"] * 0.015 / 1000
            )
        elif "openai" in provider_name:
            cost = (
                response.usage["prompt_tokens"] * 0.01 / 1000 +
                response.usage["completion_tokens"] * 0.03 / 1000
            )
        else:
            cost = 0.0
        
        metrics["total_cost_usd"] += cost
        
        # Update average latency
        n = metrics["total_calls"]
        metrics["avg_latency_ms"] = (
            metrics["avg_latency_ms"] * (n - 1) / n +
            response.latency_ms / n
        )
        
        logger.info(
            "llm_call",
            provider=provider_name,
            tokens=response.usage["total_tokens"],
            cost_usd=cost,
            latency_ms=response.latency_ms
        )
    
    def get_metrics(self, provider_name: str) -> Dict:
        return self._metrics.get(provider_name, {})
    
    def compare_providers(self) -> Dict:
        """Compare all registered providers"""
        return {
            name: self.get_metrics(name)
            for name in self._providers.keys()
        }

# Global registry
registry = ProviderRegistry()
registry.register("claude-sonnet-4", AnthropicProvider("claude-sonnet-4-20250514"))
registry.register("gpt-4-turbo", OpenAIProvider("gpt-4-turbo"))
Activities

✅ Implement provider interface
✅ Create Anthropic provider
✅ Create OpenAI provider
✅ Build registry with metrics tracking
✅ Add cost tracking per provider
✅ Write tests comparing provider outputs
✅ Document provider selection guidelines

Deliverables

LLM abstraction library supporting 2+ providers
Provider registry with metrics
Test suite demonstrating provider equivalence
Documentation on provider tradeoffs


2.2 MCP Client Library (Week 6)
MCP Transport Layer
mcp_client/transport.py:
pythonimport httpx
from typing import Dict, Any
import uuid
import structlog

logger = structlog.get_logger()

class MCPTransport:
    """
    JSON-RPC 2.0 transport for MCP protocol
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def call_tool(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        Call a tool via MCP JSON-RPC
        """
        request_id = str(uuid.uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        
        logger.info(
            "mcp_call",
            method=method,
            request_id=request_id,
            params=params
        )
        
        try:
            response = await self.client.post(
                f"{self.server_url}/mcp",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                logger.error(
                    "mcp_error",
                    method=method,
                    error=data["error"]
                )
                raise Exception(f"MCP Error: {data['error']}")
            
            logger.info(
                "mcp_success",
                method=method,
                request_id=request_id
            )
            
            return data["result"]
            
        except Exception as e:
            logger.error(
                "mcp_transport_error",
                method=method,
                error=str(e)
            )
            raise
    
    async def discover_tools(self) -> Dict:
        """
        Discover available tools from server
        """
        response = await self.client.get(f"{self.server_url}/mcp/tools")
        return response.json()
    
    async def close(self):
        await self.client.aclose()
Typed EMBM Client
mcp_client/embm_tools.py:
pythonfrom .transport import MCPTransport
from typing import List, Dict, Any
from datetime import datetime

class EMBMClient:
    """
    Typed client for EMBM-J DS MCP tools
    """
    
    def __init__(self, server_url: str):
        self.transport = MCPTransport(server_url)
    
    async def get_spectrum_plan(
        self,
        ao_geojson: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        Retrieve current spectrum allocation plan
        """
        return await self.transport.call_tool(
            "get_spectrum_plan",
            {
                "ao_geojson": ao_geojson,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
    
    async def request_deconfliction(
        self,
        asset_rid: str,
        frequency_mhz: float,
        bandwidth_khz: float,
        power_dbm: float,
        location: Dict[str, float],
        start_time: datetime,
        duration_minutes: int,
        priority: str,
        purpose: str
    ) -> Dict:
        """
        Request frequency deconfliction
        """
        return await self.transport.call_tool(
            "request_deconfliction",
            {
                "asset_rid": asset_rid,
                "frequency_mhz": frequency_mhz,
                "bandwidth_khz": bandwidth_khz,
                "power_dbm": power_dbm,
                "location": location,
                "start_time": start_time.isoformat(),
                "duration_minutes": duration_minutes,
                "priority": priority,
                "purpose": purpose
            }
        )
    
    async def analyze_coa_impact(
        self,
        coa_id: str,
        friendly_actions: List[Dict]
    ) -> Dict:
        """
        Analyze Course of Action electromagnetic impact
        """
        return await self.transport.call_tool(
            "analyze_coa_impact",
            {
                "coa_id": coa_id,
                "friendly_actions": friendly_actions
            }
        )
    
    # ... implement remaining tools
    
    async def close(self):
        await self.transport.close()
Circuit Breaker & Retry Logic
mcp_client/resilience.py:
pythonimport asyncio
from typing import Callable, Any
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker pattern for MCP calls
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )

async def with_retry(
    func: Callable,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = backoff_base ** attempt
            await asyncio.sleep(wait_time)
Activities

✅ Implement JSON-RPC 2.0 transport
✅ Create typed wrappers for EMBM tools
✅ Add circuit breaker pattern
✅ Implement retry with exponential backoff
✅ Add comprehensive error handling
✅ Log all MCP interactions
✅ Write integration tests with mock server

Deliverables

MCP client library used by all agents
Typed tool wrappers for type safety
Resilience patterns (circuit breaker, retry)
Test suite demonstrating all tools work


2.3 First Agent: Spectrum Manager (Week 7)
Agent Architecture
agents/base_agent.py:
pythonfrom abc import ABC, abstractmethod
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from dataclasses import dataclass
import structlog

from llm_abstraction.provider import LLMProvider, Message
from mcp_client.embm_tools import EMBMClient

logger = structlog.get_logger()

@dataclass
class AgentState:
    """
    Shared state across all agent nodes
    """
    messages: List[Message]
    current_task: Dict[str, Any]
    context: Dict[str, Any]
    tool_results: List[Dict[str, Any]]
    decision: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseAgent(ABC):
    """
    Base class for all agents
    """
    
    def __init__(
        self,
        agent_id: str,
        llm_provider: LLMProvider,
        embm_client: EMBMClient
    ):
        self.agent_id = agent_id
        self.llm = llm_provider
        self.embm = embm_client
        self.logger = logger.bind(agent_id=agent_id)
        self.graph = self._build_graph()
    
    @abstractmethod
    def _build_graph(self) -> StateGraph:
        """Build the agent's workflow graph"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the agent's system prompt"""
        pass
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for agent task processing
        """
        self.logger.info("task_received", task=task)
        
        initial_state = AgentState(
            messages=[Message(role="system", content=self.get_system_prompt())],
            current_task=task,
            context={},
            tool_results=[]
        )
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            self.logger.info(
                "task_completed",
                decision=final_state.get("decision")
            )
            
            return final_state["decision"]
            
        except Exception as e:
            self.logger.error("task_failed", error=str(e))
            raise
Spectrum Manager Implementation
agents/spectrum_manager/agent.py:
pythonfrom langgraph.graph import StateGraph
from ..base_agent import BaseAgent, AgentState
from .prompts import SYSTEM_PROMPT
from datetime import datetime, timedelta

class SpectrumManagerAgent(BaseAgent):
    """
    Manages electromagnetic spectrum allocation and deconfliction
    """
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("receive_request", self.receive_request)
        workflow.add_node("query_spectrum_plan", self.query_spectrum_plan)
        workflow.add_node("reason_about_request", self.reason_about_request)
        workflow.add_node("check_constraints", self.check_constraints)
        workflow.add_node("make_decision", self.make_decision)
        workflow.add_node("execute_action", self.execute_action)
        
        # Define edges (workflow)
        workflow.set_entry_point("receive_request")
        workflow.add_edge("receive_request", "query_spectrum_plan")
        workflow.add_edge("query_spectrum_plan", "reason_about_request")
        workflow.add_edge("reason_about_request", "check_constraints")
        workflow.add_edge("check_constraints", "make_decision")
        workflow.add_edge("make_decision", "execute_action")
        workflow.add_edge("execute_action", END)
        
        return workflow.compile()
    
    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
    
    async def receive_request(self, state: AgentState) -> AgentState:
        """Parse the incoming request"""
        task = state.current_task
        
        self.logger.info("processing_request", task_type=task.get("type"))
        
        # Extract request parameters
        state.context["request_params"] = {
            "asset_id": task.get("asset_id"),
            "frequency_mhz": task.get("frequency_mhz"),
            "duration_minutes": task.get("duration_minutes"),
            "location": task.get("location")
        }
        
        return state
    
    async def query_spectrum_plan(self, state: AgentState) -> AgentState:
        """Query current spectrum allocations via EMBM"""
        
        # Define area of operations (simplified)
        ao_geojson = '{"type": "Polygon", "coordinates": [...]}'
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2)
        
        # Call EMBM
        plan = await self.embm.get_spectrum_plan(
            ao_geojson=ao_geojson,
            start_time=start_time,
            end_time=end_time
        )
        
        state.context["current_plan"] = plan
        state.tool_results.append({
            "tool": "get_spectrum_plan",
            "result": plan
        })
        
        self.logger.info(
            "spectrum_plan_retrieved",
            num_allocations=len(plan.get("allocations", []))
        )
        
        return state
    
    async def reason_about_request(self, state: AgentState) -> AgentState:
        """Use LLM to analyze the request"""
        
        request = state.context["request_params"]
        plan = state.context["current_plan"]
        
        # Build reasoning prompt
        prompt = f"""
You are analyzing a frequency deconfliction request.

Request Details:
- Asset: {request['asset_id']}
- Requested Frequency: {request['frequency_mhz']} MHz
- Duration: {request['duration_minutes']} minutes
- Location: {request['location']}

Current Spectrum Plan:
{plan}

Your task:
1. Identify any potential conflicts with existing allocations
2. Assess the severity of each conflict
3. Consider geographic separation and frequency separation
4. Recommend whether to approve, deny, or suggest alternatives

Provide your analysis in a structured format.
"""
        
        state.messages.append(Message(role="user", content=prompt))
        
        # Call LLM
        response = await self.llm.complete(
            messages=state.messages,
            temperature=0.3  # Lower temperature for analytical task
        )
        
        state.messages.append(Message(
            role="assistant",
            content=response.content
        ))
        
        state.context["llm_analysis"] = response.content
        
        self.logger.info("reasoning_complete", analysis=response.content)
        
        return state
    
    async def check_constraints(self, state: AgentState) -> AgentState:
        """Verify no ROE or policy violations"""
        
        # In a real system, would check against ROE database
        # For now, simple checks
        
        request = state.context["request_params"]
        
        # Check if frequency is in civilian range
        civilian_ranges = [(88.0, 108.0), (118.0, 137.0)]
        
        for freq_range in civilian_ranges:
            if freq_range[0] <= request["frequency_mhz"] <= freq_range[1]:
                state.context["constraint_violation"] = (
                    f"Frequency {request['frequency_mhz']} MHz is in civilian range"
                )
                break
        
        return state
    
    async def make_decision(self, state: AgentState) -> AgentState:
        """Make final approval/denial decision"""
        
        # Check for constraint violations
        if "constraint_violation" in state.context:
            state.decision = {
                "approved": False,
                "reason": state.context["constraint_violation"]
            }
            return state
        
        # Use LLM analysis to decide
        analysis = state.context["llm_analysis"]
        
        # Simple heuristic: if LLM mentions "conflict" or "deny", deny
        if "deny" in analysis.lower() or "high-severity" in analysis.lower():
            state.decision = {
                "approved": False,
                "reason": "Conflicts detected",
                "llm_analysis": analysis
            }
        else:
            state.decision = {
                "approved": True,
                "reason": "No significant conflicts",
                "llm_analysis": analysis
            }
        
        self.logger.info("decision_made", decision=state.decision)
        
        return state
    
    async def execute_action(self, state: AgentState) -> AgentState:
        """Execute the decision via EMBM"""
        
        if not state.decision["approved"]:
            # Just log denial
            self.logger.info("request_denied", reason=state.decision["reason"])
            return state
        
        # Allocate frequency
        request = state.context["request_params"]
        
        # First, get approval via deconfliction request
        deconf_result = await self.embm.request_deconfliction(
            asset_rid=request["asset_id"],
            frequency_mhz=request["frequency_mhz"],
            bandwidth_khz=25.0,  # Simplified
            power_dbm=30.0,
            location=request["location"],
            start_time=datetime.now(),
            duration_minutes=request["duration_minutes"],
            priority="ROUTINE",
            purpose="Agent-approved allocation"
        )
        
        state.context["deconfliction_result"] = deconf_result
        
        if deconf_result["status"] == "APPROVED":
            # Allocate
            alloc_result = await self.embm.allocate_frequency(
                asset_id=request["asset_id"],
                frequency_mhz=request["frequency_mhz"],
                bandwidth_khz=25.0,
                duration_minutes=request["duration_minutes"],
                authorization_id=deconf_result["request_id"]
            )
            
            state.context["allocation_result"] = alloc_result
            self.logger.info("frequency_allocated", result=alloc_result)
        
        return state

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
System Prompt
agents/spectrum_manager/prompts.py:
pythonSYSTEM_PROMPT = """You are a Joint Electromagnetic Spectrum Manager responsible for allocating electromagnetic frequency resources across military services.

Your mission is to maximize spectrum utilization while preventing harmful interference and ensuring mission success.

Core Responsibilities:
1. Evaluate frequency deconfliction requests
2. Identify and assess conflicts with existing allocations
3. Apply Joint spectrum allocation policies (AFI 10-707, CJCSM 3320.01)
4. Consider geographic separation, temporal deconfliction, and power control
5. Prioritize mission-critical communications
6. Ensure compliance with Rules of Engagement

When evaluating a request, you must:
- Query current spectrum allocations via EMBM tools
- Calculate interference risk based on:
  * Frequency separation (minimum 5 MHz for safety)
  * Geographic distance (minimum 50 km without terrain masking)
  * Transmit power levels
  * Time window overlaps
- Check for ROE violations (e.g., no jamming civilian frequencies)
- Provide clear, concise justification for every decision
- Suggest alternative frequencies when conflicts exist

Decision Framework:
- APPROVE: No conflicts or only minor, resolvable conflicts
- DENY: High-severity conflicts or ROE violations
- NEGOTIATE: Moderate conflicts that could be resolved with adjustments

Always be thorough but concise. Your decisions affect mission success and safety."""
Testing
tests/unit/test_spectrum_manager.py:
pythonimport pytest
from agents.spectrum_manager.agent import SpectrumManagerAgent
from llm_abstraction.anthropic_provider import AnthropicProvider
from mcp_client.embm_tools import EMBMClient

@pytest.mark.asyncio
async def test_spectrum_manager_approve_no_conflicts():
    """Test that clear requests are approved"""
    
    # Setup
    llm = AnthropicProvider()
    embm = EMBMClient("http://localhost:8000")
    agent = SpectrumManagerAgent("spectrum-mgr-1", llm, embm)
    
    # Task
    task = {
        "type": "frequency_request",
        "asset_id": "F16-001",
        "frequency_mhz": 300.0,
        "duration_minutes": 30,
        "location": {"lat": 35.0, "lon": -120.0}
    }
    
    # Execute
    result = await agent.process_task(task)
    
    # Assert
    assert result["approved"] == True
    assert "reason" in result

@pytest.mark.asyncio
async def test_spectrum_manager_deny_civilian_frequency():
    """Test that civilian frequencies are denied"""
    
    llm = AnthropicProvider()
    embm = EMBMClient("http://localhost:8000")
    agent = SpectrumManagerAgent("spectrum-mgr-1", llm, embm)
    
    # Task with FM radio frequency
    task = {
        "type": "frequency_request",
        "asset_id": "F16-001",
        "frequency_mhz": 95.0,  # FM radio
        "duration_minutes": 30,
        "location": {"lat": 35.0, "lon": -120.0}
    }
    
    result = await agent.process_task(task)
    
    # Assert denial
    assert result["approved"] == False
    assert "civilian" in result["reason"].lower()
Activities

✅ Implement Spectrum Manager with LangGraph
✅ Create comprehensive system prompt with domain knowledge
✅ Test with various deconfliction scenarios
✅ Measure success rate (% reasonable requests handled correctly)
✅ Document failure modes and edge cases

Deliverables

Working Spectrum Manager agent
Test suite with >80% pass rate on realistic scenarios
Performance metrics (response time, accuracy)
Documentation of agent capabilities and limitations


2.4 Second Agent: ISR Collection Manager (Week 8)
[Similar structure to Spectrum Manager - abbreviated for length]
Key Differences:

More autonomous (monitors for threats, initiates actions)
Must prioritize targets
Coordinates with Spectrum Manager for sensor frequencies

Core Workflow:

Monitor for emitter reports (via EMBM)
Assess threat priority using LLM
Determine if ISR retasking needed
Request frequency from Spectrum Manager (agent-to-agent message)
Task sensor via EMBM


2.5 Third Agent: EW Planner (Week 9)
[Similar structure - abbreviated]
Key Differences:

Generates multiple COAs
Uses EMBM's analyze_coa_impact tool
Must carefully check ROE constraints
Coordinates with both Spectrum Manager and ISR Manager

Phase 2 Complete: Three independent agents successfully complete specialized workflows

Phase 3: Multi-Agent Collaboration (Weeks 10-13)
Objectives

Enable agents to communicate and coordinate
Implement realistic multi-agent workflows
Handle conflicts and negotiate solutions
Demonstrate emergent team behavior


3.1 Agent Communication Infrastructure (Week 10)
Message Broker
broker/broker.py:
pythonimport asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()

@dataclass
class Message:
    id: str
    from_agent: str
    to_agent: str
    type: str  # REQUEST, RESPONSE, NOTIFY, QUERY
    content: Dict
    timestamp: datetime
    requires_response: bool = False
    request_id: Optional[str] = None

class AgentBroker:
    """
    Central message bus for agent-to-agent communication
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self.message_queue = asyncio.Queue()
        self.conversation_history = []
        self._running = False
    
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent with the broker"""
        self.agents[agent_id] = agent
        logger.info("agent_registered", agent_id=agent_id)
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict,
        requires_response: bool = False,
        request_id: Optional[str] = None
    ):
        """Send a messageRetryKKContinueMapped out comprehensive project plan for AI agent development.The user wants me to continue generating the markdown document for the complete project plan. I was in the middle of Phase 3.1, specifically writing the AgentBroker implementation. Let me continue from where I left off.
I should complete:

The broker.py implementation
Message types
The rest of Phase 3.1 (Agent Communication Infrastructure)
Phase 3.2 (Agent Conversation Capabilities)
Phase 3.3 (Workflow 1: Coordinated Frequency Allocation)
Phase 3.4 (Workflow 2: Pop-Up Threat Response)
Phase 3.5 (Conflict Resolution & Negotiation)
Phase 4 (Validation, Comparison & Documentation)
Resource Requirements
Risk Management
Success Metrics
Timeline Summary

Let me continue the document."""
msg = Message(
id=str(uuid.uuid4()),
from_agent=from_agent,
to_agent=to_agent,
type=message_type,
content=content,
timestamp=datetime.now(),
requires_response=requires_response,
request_id=request_id
)
    await self.message_queue.put(msg)
    self.conversation_history.append(msg)
    
    logger.info(
        "message_sent",
        from_agent=from_agent,
        to_agent=to_agent,
        type=message_type,
        message_id=msg.id
    )

async def start(self):
    """Start the message routing loop"""
    self._running = True
    logger.info("broker_started")
    
    while self._running:
        try:
            msg = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=1.0
            )
            await self._route_message(msg)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error("broker_error", error=str(e))

async def _route_message(self, msg: Message):
    """Route message to target agent"""
    if msg.to_agent not in self.agents:
        logger.error(
            "unknown_agent",
            to_agent=msg.to_agent,
            message_id=msg.id
        )
        return
    
    target_agent = self.agents[msg.to_agent]
    
    try:
        await target_agent.receive_message(msg)
        logger.info(
            "message_delivered",
            to_agent=msg.to_agent,
            message_id=msg.id
        )
    except Exception as e:
        logger.error(
            "message_delivery_failed",
            to_agent=msg.to_agent,
            error=str(e)
        )

def stop(self):
    """Stop the broker"""
    self._running = False
    logger.info("broker_stopped")

def get_conversation(
    self,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Message]:
    """Get conversation history"""
    if agent_id:
        return [
            msg for msg in self.conversation_history
            if msg.from_agent == agent_id or msg.to_agent == agent_id
        ][-limit:]
    return self.conversation_history[-limit:]
Global broker instance
broker = AgentBroker()

#### Message Types

**broker/messages.py:**
````python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from uuid import UUID

@dataclass
class RequestMessage:
    """Request for action or approval from another agent"""
    request_type: str  # "frequency_approval", "threat_assessment", etc.
    parameters: Dict[str, Any]
    priority: str = "ROUTINE"  # ROUTINE, PRIORITY, IMMEDIATE
    deadline: Optional[str] = None  # ISO datetime

@dataclass
class ResponseMessage:
    """Response to a request"""
    request_id: str
    approved: bool
    reasoning: str
    data: Optional[Dict[str, Any]] = None
    alternatives: Optional[list] = None

@dataclass
class NotificationMessage:
    """Broadcast information (no response expected)"""
    event_type: str  # "threat_detected", "allocation_updated", etc.
    data: Dict[str, Any]
    severity: str = "INFO"  # INFO, WARNING, CRITICAL

@dataclass
class QueryMessage:
    """Ask for information without requesting action"""
    query: str
    context: Dict[str, Any]

@dataclass
class NegotiationMessage:
    """Propose compromise or alternative"""
    original_request_id: str
    proposal: Dict[str, Any]
    justification: str
````

#### Activities
- ✅ Implement AgentBroker with message queue
- ✅ Define message protocol and schemas
- ✅ Add message persistence for debugging
- ✅ Create message inspection tools
- ✅ Test broker with mock agents
- ✅ Implement timeout handling

#### Deliverables
- **Agent communication infrastructure**
- **Message broker** with logging
- **Message type definitions**
- **Test suite** demonstrating message flow

---

### 3.2 Agent Conversation Capabilities (Week 10-11)

#### Enhanced Base Agent

**agents/base_agent.py (updated):**
````python
class BaseAgent(ABC):
    """
    Base class with conversation capabilities
    """
    
    def __init__(
        self,
        agent_id: str,
        llm_provider: LLMProvider,
        embm_client: EMBMClient,
        broker: AgentBroker
    ):
        self.agent_id = agent_id
        self.llm = llm_provider
        self.embm = embm_client
        self.broker = broker
        self.conversation_history = []
        self.pending_requests = {}  # request_id -> request details
        self.logger = logger.bind(agent_id=agent_id)
        self.graph = self._build_graph()
        
        # Register with broker
        self.broker.register_agent(agent_id, self)
    
    async def receive_message(self, msg: Message):
        """
        Process incoming message from another agent
        """
        self.conversation_history.append(msg)
        self.logger.info(
            "message_received",
            from_agent=msg.from_agent,
            type=msg.type
        )
        
        # Route based on message type
        if msg.type == "REQUEST":
            await self._handle_request(msg)
        elif msg.type == "RESPONSE":
            await self._handle_response(msg)
        elif msg.type == "NOTIFY":
            await self._handle_notification(msg)
        elif msg.type == "QUERY":
            await self._handle_query(msg)
    
    async def _handle_request(self, msg: Message):
        """Handle incoming request from another agent"""
        
        # Use LLM to understand and respond
        prompt = f"""
You received a request from agent {msg.from_agent}.

Request Type: {msg.content.get('request_type')}
Details: {msg.content.get('parameters')}

Your current state: {self._get_state_summary()}

How should you respond? Consider:
1. Do you have authority to approve this request?
2. Do you need to query EMBM for more information?
3. Are there conflicts with your current operations?
4. Should you approve, deny, or negotiate?

Provide your response in JSON format:
{{
    "decision": "APPROVE|DENY|NEGOTIATE",
    "reasoning": "Your explanation",
    "action": "What action to take (if any)",
    "negotiate_proposal": "Alternative proposal (if negotiating)"
}}
"""
        
        response = await self.llm.complete(
            messages=[
                Message(role="system", content=self.get_system_prompt()),
                Message(role="user", content=prompt)
            ],
            temperature=0.3
        )
        
        # Parse LLM response and take action
        try:
            decision = self._parse_llm_decision(response.content)
            
            if decision["decision"] == "APPROVE":
                await self._send_approval(msg, decision["reasoning"])
            elif decision["decision"] == "DENY":
                await self._send_denial(msg, decision["reasoning"])
            elif decision["decision"] == "NEGOTIATE":
                await self._send_negotiation(msg, decision)
                
        except Exception as e:
            self.logger.error("failed_to_process_request", error=str(e))
    
    async def _send_approval(self, original_msg: Message, reasoning: str):
        """Send approval response"""
        await self.broker.send_message(
            from_agent=self.agent_id,
            to_agent=original_msg.from_agent,
            message_type="RESPONSE",
            content={
                "request_id": original_msg.id,
                "approved": True,
                "reasoning": reasoning
            },
            request_id=original_msg.id
        )
    
    async def _send_denial(self, original_msg: Message, reasoning: str):
        """Send denial response"""
        await self.broker.send_message(
            from_agent=self.agent_id,
            to_agent=original_msg.from_agent,
            message_type="RESPONSE",
            content={
                "request_id": original_msg.id,
                "approved": False,
                "reasoning": reasoning
            },
            request_id=original_msg.id
        )
    
    async def _send_negotiation(self, original_msg: Message, decision: Dict):
        """Send negotiation proposal"""
        await self.broker.send_message(
            from_agent=self.agent_id,
            to_agent=original_msg.from_agent,
            message_type="NEGOTIATE",
            content={
                "request_id": original_msg.id,
                "proposal": decision.get("negotiate_proposal"),
                "reasoning": decision["reasoning"]
            },
            requires_response=True,
            request_id=original_msg.id
        )
    
    def _get_state_summary(self) -> str:
        """Get current agent state for LLM context"""
        return f"Agent {self.agent_id} - {len(self.pending_requests)} pending requests"
    
    def _parse_llm_decision(self, llm_output: str) -> Dict:
        """Parse LLM JSON output"""
        # Strip markdown code blocks if present
        llm_output = llm_output.replace("```json", "").replace("```", "").strip()
        return json.loads(llm_output)
````

#### Collaboration Tools

**agents/collaboration_tools.py:**
````python
"""
Tools that agents can use to collaborate
"""

def get_collaboration_tools():
    """
    Return tool definitions for agent collaboration
    """
    return [
        {
            "name": "request_frequency_approval",
            "description": "Request frequency allocation approval from Spectrum Manager",
            "input_schema": {
                "type": "object",
                "properties": {
                    "frequency_mhz": {"type": "number"},
                    "duration_minutes": {"type": "integer"},
                    "priority": {"type": "string", "enum": ["ROUTINE", "PRIORITY", "IMMEDIATE"]},
                    "purpose": {"type": "string"}
                },
                "required": ["frequency_mhz", "duration_minutes", "purpose"]
            }
        },
        {
            "name": "request_threat_assessment",
            "description": "Request threat assessment from ISR Collection Manager",
            "input_schema": {
                "type": "object",
                "properties": {
                    "emitter_id": {"type": "string"},
                    "urgency": {"type": "string"}
                },
                "required": ["emitter_id"]
            }
        },
        {
            "name": "propose_alternative",
            "description": "Propose an alternative to another agent's request",
            "input_schema": {
                "type": "object",
                "properties": {
                    "original_request_id": {"type": "string"},
                    "alternative": {"type": "object"},
                    "justification": {"type": "string"}
                },
                "required": ["original_request_id", "alternative", "justification"]
            }
        },
        {
            "name": "notify_agents",
            "description": "Broadcast notification to other agents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "data": {"type": "object"},
                    "severity": {"type": "string", "enum": ["INFO", "WARNING", "CRITICAL"]}
                },
                "required": ["event_type", "data"]
            }
        }
    ]
````

#### Activities
- ✅ Enhance all agents with conversation capabilities
- ✅ Create conversation-aware system prompts
- ✅ Implement message handlers for each agent
- ✅ Add collaboration tools
- ✅ Test basic request/response flows

#### Deliverables
- **Agents can send/receive messages**
- **LLM-driven message understanding**
- **Collaboration tools** integrated
- **Test suite** for message handling

---

### 3.3 Workflow 1: Coordinated Frequency Allocation (Week 11)

#### Scenario Implementation

**workflows/frequency_allocation.py:**
````python
"""
Workflow: ISR Manager needs frequency, coordinates with Spectrum Manager
"""

async def run_coordinated_allocation_workflow():
    """
    Scenario:
    1. ISR Manager detects high-priority threat
    2. Needs sensor frequency
    3. Requests approval from Spectrum Manager
    4. Handles approval/negotiation
    5. Tasks sensor
    """
    
    # Setup
    llm = registry.get("claude-sonnet-4")
    embm = EMBMClient(os.getenv("EMBM_SERVER_URL"))
    
    # Create agents
    spectrum_mgr = SpectrumManagerAgent("spectrum-mgr", llm, embm, broker)
    isr_mgr = ISRCollectionManagerAgent("isr-mgr", llm, embm, broker)
    
    # Start broker
    asyncio.create_task(broker.start())
    
    # Simulate threat detection
    threat_emitter = {
        "emitter_id": "EMITTER-12345",
        "location": {"lat": 35.5, "lon": -120.0},
        "frequency_mhz": 3000.0,
        "threat_level": "HIGH"
    }
    
    logger.info("workflow_started", scenario="coordinated_allocation")
    
    # Step 1: ISR Manager detects threat
    await isr_mgr.process_threat_detection(threat_emitter)
    
    # Step 2: ISR Manager requests frequency from Spectrum Manager
    # (This happens internally via agent-to-agent message)
    
    # Wait for workflow to complete
    await asyncio.sleep(5)
    
    # Get conversation history
    conversation = broker.get_conversation()
    
    logger.info(
        "workflow_completed",
        total_messages=len(conversation),
        conversation=conversation
    )
    
    return conversation

# Test with different scenarios
async def test_allocation_with_conflict():
    """
    Test case: Requested frequency conflicts with existing allocation
    Expected: Negotiation and alternative frequency
    """
    pass

async def test_allocation_with_roe_violation():
    """
    Test case: Requested frequency violates ROE
    Expected: Denial with explanation
    """
    pass
````

#### Expected Message Flow
````
Message 1:
FROM: isr-mgr
TO: spectrum-mgr
TYPE: REQUEST
CONTENT: {
    "request_type": "frequency_approval",
    "parameters": {
        "frequency_mhz": 8500.0,
        "duration_minutes": 30,
        "priority": "HIGH",
        "purpose": "SAR imaging of high-value target"
    }
}

Message 2:
FROM: spectrum-mgr
TO: isr-mgr
TYPE: NEGOTIATE
CONTENT: {
    "request_id": "msg-001",
    "proposal": {
        "alternative_frequency": 9200.0,
        "reason": "8500 MHz conflict with Navy SATCOM"
    },
    "reasoning": "Geographic overlap with existing allocation"
}

Message 3:
FROM: isr-mgr
TO: spectrum-mgr
TYPE: RESPONSE
CONTENT: {
    "request_id": "msg-002",
    "approved": True,
    "reasoning": "9200 MHz acceptable for SAR mission"
}

Message 4:
FROM: spectrum-mgr
TO: isr-mgr
TYPE: RESPONSE
CONTENT: {
    "request_id": "msg-001",
    "approved": True,
    "allocation_id": "ALLOC-789",
    "reasoning": "Frequency allocated successfully"
}
````

#### Success Criteria
- ✅ Agents successfully negotiate alternative frequency
- ✅ All EMBM calls are correct
- ✅ Conversation is coherent and goal-directed
- ✅ Workflow completes in <60 seconds
- ✅ Proper error handling if no agreement reached

#### Activities
- ✅ Implement full coordinated allocation workflow
- ✅ Test with multiple conflict scenarios
- ✅ Add timeout and failure handling
- ✅ Measure negotiation success rate
- ✅ Record and analyze conversations

#### Deliverables
- **Working coordinated allocation**
- **Test suite** with 10+ scenarios
- **Performance metrics**
- **Conversation logs** for analysis

---

### 3.4 Workflow 2: Pop-Up Threat Response (Week 12)

#### Complex Multi-Agent Scenario

**workflows/popup_threat.py:**
````python
"""
Workflow: Coordinated response to new enemy radar
Involves: ISR Manager, EW Planner, Spectrum Manager
"""

async def run_popup_threat_workflow():
    """
    Scenario:
    1. EMBM detects new enemy radar (automated)
    2. ISR Manager assesses threat
    3. ISR Manager notifies EW Planner
    4. EW Planner generates jamming COAs
    5. ISR Manager requests ISR before jamming
    6. Coordinate frequencies for both operations
    7. Execute sequenced operations
    """
    
    # Setup agents
    llm = registry.get("claude-sonnet-4")
    embm = EMBMClient(os.getenv("EMBM_SERVER_URL"))
    
    spectrum_mgr = SpectrumManagerAgent("spectrum-mgr", llm, embm, broker)
    isr_mgr = ISRCollectionManagerAgent("isr-mgr", llm, embm, broker)
    ew_planner = EWPlannerAgent("ew-planner", llm, embm, broker)
    
    asyncio.create_task(broker.start())
    
    # Simulate automated emitter detection
    new_emitter = {
        "emitter_id": "THREAT-999",
        "location": {"lat": 36.0, "lon": -119.0},
        "frequency_mhz": 2800.0,
        "signal_characteristics": {
            "waveform": "pulse",
            "prf_hz": 1000.0
        },
        "threat_assessment": {
            "threat_type": "RADAR",
            "threat_level": "CRITICAL",
            "matches_known_system": "S-400 acquisition radar"
        }
    }
    
    logger.info("popup_threat_detected", emitter=new_emitter)
    
    # Step 1: Report to EMBM
    emitter_report = await embm.report_emitter(
        location=new_emitter["location"],
        frequency_mhz=new_emitter["frequency_mhz"],
        bandwidth_khz=50.0,
        signal_characteristics=new_emitter["signal_characteristics"],
        detection_time=datetime.now(),
        confidence=0.95
    )
    
    # Step 2: ISR Manager processes threat
    await isr_mgr.process_threat_detection(emitter_report)
    
    # Steps 3-7: Agents coordinate automatically
    # Wait for coordination to complete
    await asyncio.sleep(15)
    
    # Analyze results
    conversation = broker.get_conversation()
    
    # Verify sequence
    expected_sequence = [
        "ISR->EW: NOTIFY (threat detected)",
        "EW->ISR: QUERY (need ISR first?)",
        "ISR->SPECTRUM: REQUEST (ISR frequency)",
        "SPECTRUM->ISR: RESPONSE (approved)",
        "ISR->EW: NOTIFY (ISR complete)",
        "EW->SPECTRUM: REQUEST (jamming frequency)",
        "SPECTRUM->EW: RESPONSE (approved)"
    ]
    
    actual_sequence = [
        f"{msg.from_agent}->{msg.to_agent}: {msg.type}"
        for msg in conversation
    ]
    
    logger.info(
        "workflow_analysis",
        expected=expected_sequence,
        actual=actual_sequence
    )
    
    return conversation
````

#### Key Challenges

**Challenge 1: Sequencing**
- ISR must happen before jamming
- Agents must coordinate timing
- Handle delays and failures

**Challenge 2: Multiple Frequency Requests**
- Both ISR and EW need spectrum
- Could conflict with each other
- Spectrum Manager must prioritize

**Challenge 3: Dynamic Situation**
- Threat could move
- New intelligence could change priorities
- Agents must adapt

#### Success Criteria
- ✅ Proper sequencing (ISR before EW)
- ✅ All spectrum requests coordinated
- ✅ No deadlocks or race conditions
- ✅ ROE checked throughout
- ✅ End-to-end time <5 minutes

#### Activities
- ✅ Implement multi-step workflow
- ✅ Add event-driven activation
- ✅ Test timing and sequencing
- ✅ Handle race conditions
- ✅ Measure end-to-end latency

#### Deliverables
- **Working pop-up threat response**
- **Sequence verification** tests
- **Performance analysis**
- **Failure mode documentation**

---

### 3.5 Conflict Resolution & Negotiation (Week 13)

#### Conflict Scenarios

**Scenario 1: Priority Conflict**
````
ISR Manager: "Need 8.5 GHz NOW for critical ISR (PRIORITY)"
EW Planner: "Already jamming on 8.5 GHz (IMMEDIATE)"
Spectrum Manager: Must decide based on priority and mission criticality
````

**Scenario 2: Time-Sharing Negotiation**
````
Agent A: Needs frequency for 60 minutes
Agent B: Needs same frequency for 30 minutes
Resolution: Time-share (A gets 30 min, then B, then A continues)
````

**Scenario 3: Frequency Adjustment**
````
Agent A: Requests 300 MHz
Spectrum Manager: 300 MHz unavailable, suggests 305 MHz
Agent A: Must decide if 305 MHz works for mission
````

#### Negotiation Protocol

**broker/negotiation.py:**
````python
class NegotiationSession:
    """
    Manages multi-round negotiation between agents
    """
    
    def __init__(self, session_id: str, participants: List[str]):
        self.session_id = session_id
        self.participants = participants
        self.rounds = []
        self.status = "ACTIVE"  # ACTIVE, RESOLVED, DEADLOCKED
        self.resolution = None
        self.max_rounds = 5
    
    async def add_proposal(
        self,
        from_agent: str,
        proposal: Dict[str, Any]
    ):
        """Add a negotiation proposal"""
        self.rounds.append({
            "round": len(self.rounds) + 1,
            "from_agent": from_agent,
            "proposal": proposal,
            "timestamp": datetime.now()
        })
        
        # Check if we've reached agreement
        if self._check_agreement(proposal):
            self.status = "RESOLVED"
            self.resolution = proposal
        elif len(self.rounds) >= self.max_rounds:
            self.status = "DEADLOCKED"
    
    def _check_agreement(self, proposal: Dict) -> bool:
        """Check if all participants agree"""
        # Simplified: check if proposal has all approvals
        return proposal.get("agreed_by") == set(self.participants)
````

#### Resolution Strategies

**Strategy 1: Priority-Based**
````python
async def resolve_by_priority(conflict: Dict) -> str:
    """
    Spectrum Manager decides based on priority
    """
    requests = conflict["requests"]
    
    # Sort by priority
    priority_order = {"IMMEDIATE": 3, "PRIORITY": 2, "ROUTINE": 1}
    sorted_requests = sorted(
        requests,
        key=lambda r: priority_order[r["priority"]],
        reverse=True
    )
    
    # Approve highest priority
    winner = sorted_requests[0]
    
    logger.info(
        "priority_resolution",
        winner=winner["agent_id"],
        priority=winner["priority"]
    )
    
    return winner["agent_id"]
````

**Strategy 2: LLM-Mediated Negotiation**
````python
async def llm_mediate_conflict(
    spectrum_mgr: SpectrumManagerAgent,
    conflict: Dict
) -> Dict:
    """
    Use LLM to find creative solution
    """
    
    prompt = f"""
You are mediating a spectrum conflict between multiple agents:

Conflicting Requests:
{json.dumps(conflict["requests"], indent=2)}

Current Spectrum Situation:
{json.dumps(conflict["current_allocations"], indent=2)}

Find a solution that:
1. Respects mission priorities
2. Minimizes interference
3. Maximizes overall mission success
4. Is fair to all parties

Possible solutions:
- Time-sharing
- Frequency adjustment
- Geographic separation
- Power reduction
- Sequential operations

Provide solution in JSON:
{{
    "solution_type": "...",
    "resolution": {{...}},
    "justification": "..."
}}
"""
    
    response = await spectrum_mgr.llm.complete(
        messages=[Message(role="user", content=prompt)],
        temperature=0.5
    )
    
    return json.loads(response.content)
````

**Strategy 3: Human Escalation**
````python
async def escalate_to_human(conflict: Dict):
    """
    Escalate unresolvable conflict to human operator
    """
    logger.warning(
        "conflict_escalation",
        conflict=conflict,
        reason="Agents unable to reach agreement"
    )
    
    # In a real system, would trigger UI alert
    # For prototype, log and wait
    
    print("\n" + "="*80)
    print("HUMAN DECISION REQUIRED")
    print("="*80)
    print(json.dumps(conflict, indent=2))
    print("\nWaiting for operator input...")
    
    # Simulate human decision (in real system, would be UI input)
    await asyncio.sleep(5)
    
    return {
        "resolution": "human_override",
        "decision": "Approve request A"
    }
````

#### Activities
- ✅ Implement priority-based resolution
- ✅ Add LLM-mediated negotiation
- ✅ Create escalation mechanism
- ✅ Test with conflicting requests
- ✅ Measure auto-resolution success rate

#### Deliverables
- **Conflict resolution system**
- **Negotiation protocols**
- **Test suite** with conflict scenarios
- **Metrics**: % conflicts auto-resolved

**Phase 3 Complete:** Multi-agent collaboration demonstrated with negotiation and conflict resolution

---

## Phase 4: Validation, Comparison & Documentation (Weeks 14-16)

### Objectives
- Validate agents handle realistic EMBM workflows
- Compare LLM providers (Claude vs GPT-4)
- Document methodology for future development
- Create demo and presentation materials

---

### 4.1 Workflow Validation Framework (Week 14)

#### Test Case Library

**evaluation/test_cases.py:**
````python
"""
Comprehensive test cases for agent validation
"""

TEST_CASES = [
    {
        "id": "TC-001",
        "name": "Simple deconfliction - no conflicts",
        "category": "baseline",
        "setup": {
            "existing_allocations": [],
            "request": {
                "frequency_mhz": 300.0,
                "duration_minutes": 30
            }
        },
        "expected_outcome": "APPROVED",
        "success_criteria": {
            "approved": True,
            "response_time_max_sec": 10
        }
    },
    {
        "id": "TC-002",
        "name": "Deconfliction with minor conflict",
        "category": "conflict_resolution",
        "setup": {
            "existing_allocations": [
                {"frequency_mhz": 305.0, "location": {"lat": 35.0, "lon": -120.0}}
            ],
            "request": {
                "frequency_mhz": 300.0,
                "location": {"lat": 35.1, "lon": -120.1}
            }
        },
        "expected_outcome": "APPROVED or NEGOTIATED",
        "success_criteria": {
            "approved": True,
            "alternatives_provided": False  # Close enough geographically
        }
    },
    {
        "id": "TC-003",
        "name": "ROE violation - civilian frequency",
        "category": "compliance",
        "setup": {
            "request": {
                "frequency_mhz": 95.0  # FM radio
            }
        },
        "expected_outcome": "DENIED",
        "success_criteria": {
            "approved": False,
            "roe_mentioned": True,
            "specific_violation_cited": True
        }
    },
    {
        "id": "TC-004",
        "name": "Multi-agent coordination",
        "category": "collaboration",
        "setup": {
            "threat_detected": True,
            "requires_isr": True,
            "requires_ew": True
        },
        "expected_outcome": "COORDINATED_SUCCESS",
        "success_criteria": {
            "isr_before_ew": True,
            "all_frequencies_allocated": True,
            "no_interference": True,
            "total_time_max_sec": 120
        }
    },
    {
        "id": "TC-005",
        "name": "Priority conflict resolution",
        "category": "negotiation",
        "setup": {
            "conflicting_requests": [
                {"priority": "PRIORITY", "agent": "isr_mgr"},
                {"priority": "IMMEDIATE", "agent": "ew_planner"}
            ]
        },
        "expected_outcome": "IMMEDIATE wins",
        "success_criteria": {
            "higher_priority_approved": True,
            "loser_offered_alternative": True
        }
    },
    # ... 25 more test cases covering:
    # - Geographic separation edge cases
    # - Frequency bandwidth conflicts
    # - Time window overlaps
    # - Power level adjustments
    # - Terrain masking effects
    # - Coalition frequency restrictions
    # - Emergency override scenarios
]
````

#### Automated Validator

**evaluation/validators.py:**
````python
class WorkflowValidator:
    """
    Automated testing framework for agents
    """
    
    def __init__(self, embm_client, broker):
        self.embm = embm_client
        self.broker = broker
        self.results = []
    
    async def run_test_suite(
        self,
        test_cases: List[Dict],
        agent_config: Dict
    ) -> Dict:
        """
        Run all test cases and generate report
        """
        logger.info("test_suite_started", num_cases=len(test_cases))
        
        for test_case in test_cases:
            result = await self.run_test_case(test_case, agent_config)
            self.results.append(result)
        
        # Generate summary
        summary = self._generate_summary()
        
        logger.info("test_suite_completed", summary=summary)
        
        return {
            "results": self.results,
            "summary": summary
        }
    
    async def run_test_case(
        self,
        test_case: Dict,
        agent_config: Dict
    ) -> Dict:
        """
        Run a single test case
        """
        test_id = test_case["id"]
        logger.info("test_case_started", id=test_id)
        
        # Setup scenario
        await self._setup_scenario(test_case["setup"])
        
        # Start agents
        agents = await self._create_agents(agent_config)
        
        # Execute workflow
        start_time = time.time()
        
        try:
            result = await self._execute_workflow(
                test_case,
                agents
            )
            
            duration = time.time() - start_time
            
            # Evaluate outcome
            passed = self._evaluate_outcome(
                result,
                test_case["expected_outcome"],
                test_case["success_criteria"]
            )
            
            return TestResult(
                test_id=test_id,
                passed=passed,
                duration_sec=duration,
                result_data=result,
                agent_reasoning=result.get("reasoning"),
                mcp_calls=result.get("mcp_calls"),
                agent_messages=result.get("messages")
            )
            
        except Exception as e:
            logger.error("test_case_failed", id=test_id, error=str(e))
            return TestResult(
                test_id=test_id,
                passed=False,
                error=str(e)
            )
    
    def _evaluate_outcome(
        self,
        result: Dict,
        expected: str,
        criteria: Dict
    ) -> bool:
        """
        Evaluate if test passed based on criteria
        """
        # Check primary outcome
        if expected == "APPROVED":
            if not result.get("approved"):
                return False
        elif expected == "DENIED":
            if result.get("approved"):
                return False
        
        # Check all criteria
        for criterion, expected_value in criteria.items():
            actual_value = result.get(criterion)
            
            if criterion.endswith("_max_sec"):
                # Time-based criterion
                if actual_value > expected_value:
                    logger.warning(
                        "criterion_failed",
                        criterion=criterion,
                        expected=expected_value,
                        actual=actual_value
                    )
                    return False
            else:
                # Boolean or exact match
                if actual_value != expected_value:
                    logger.warning(
                        "criterion_failed",
                        criterion=criterion,
                        expected=expected_value,
                        actual=actual_value
                    )
                    return False
        
        return True
    
    def _generate_summary(self) -> Dict:
        """Generate test suite summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        
        # Group by category
        by_category = {}
        for result in self.results:
            category = result.test_case.get("category", "unknown")
            if category not in by_category:
                by_category[category] = {"passed": 0, "total": 0}
            
            by_category[category]["total"] += 1
            if result.passed:
                by_category[category]["passed"] += 1
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_category": by_category,
            "avg_duration_sec": sum(r.duration_sec for r in self.results) / total
        }
````

#### Metrics Collection

**evaluation/metrics.py:**
````python
@dataclass
class AgentMetrics:
    """Metrics for agent performance"""
    correctness_rate: float  # % test cases passed
    avg_response_time_sec: float
    avg_mcp_calls_per_workflow: float
    negotiation_success_rate: float  # % conflicts auto-resolved
    roe_compliance_rate: float  # % ROE violations caught
    reasoning_quality_score: float  # Human rating 1-5
    token_usage: Dict[str, int]
    cost_usd: float

def calculate_metrics(results: List[TestResult]) -> AgentMetrics:
    """Calculate comprehensive metrics from test results"""
    
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    
    return AgentMetrics(
        correctness_rate=passed / total,
        avg_response_time_sec=sum(r.duration_sec for r in results) / total,
        avg_mcp_calls_per_workflow=sum(
            len(r.mcp_calls) for r in results
        ) / total,
        negotiation_success_rate=calculate_negotiation_success(results),
        roe_compliance_rate=calculate_roe_compliance(results),
        reasoning_quality_score=rate_reasoning_quality(results),
        token_usage=aggregate_token_usage(results),
        cost_usd=calculate_total_cost(results)
    )
````

#### Activities
- ✅ Create comprehensive test suite (30+ cases)
- ✅ Implement automated validator
- ✅ Run full test suite
- ✅ Analyze failure modes
- ✅ Document edge cases

#### Deliverables
- **Test report** with pass rates
- **Performance metrics**
- **Failure analysis**
- **Edge case documentation**

---

### 4.2 LLM Provider Comparison (Week 14-15)

#### Comparison Framework

**evaluation/comparison.py:**
````python
async def compare_llm_providers():
    """
    Run identical test suite with different LLM providers
    """
    
    test_suite = load_test_cases()
    
    providers = [
        ("claude-sonnet-4", registry.get("claude-sonnet-4")),
        ("gpt-4-turbo", registry.get("gpt-4-turbo"))
    ]
    
    results = {}
    
    for provider_name, provider in providers:
        logger.info("testing_provider", provider=provider_name)
        
        # Create agent config with this provider
        agent_config = {
            "llm_provider": provider,
            "embm_url": os.getenv("EMBM_SERVER_URL")
        }
        
        # Run test suite
        validator = WorkflowValidator(embm_client, broker)
        provider_results = await validator.run_test_suite(
            test_suite,
            agent_config
        )
        
        # Calculate metrics
        metrics = calculate_metrics(provider_results["results"])
        
        results[provider_name] = {
            "results": provider_results,
            "metrics": metrics
        }
    
    # Statistical comparison
    comparison = compare_metrics(results)
    
    # Generate report
    report = generate_comparison_report(comparison)
    
    return report

def compare_metrics(results: Dict) -> Dict:
    """
    Statistical comparison of provider metrics
    """
    
    claude = results["claude-sonnet-4"]["metrics"]
    gpt4 = results["gpt-4-turbo"]["metrics"]
    
    return {
        "correctness": {
            "claude": claude.correctness_rate,
            "gpt4": gpt4.correctness_rate,
            "winner": "claude" if claude.correctness_rate > gpt4.correctness_rate else "gpt4",
            "difference_pct": abs(claude.correctness_rate - gpt4.correctness_rate) * 100
        },
        "response_time": {
            "claude": claude.avg_response_time_sec,
            "gpt4": gpt4.avg_response_time_sec,
            "winner": "claude" if claude.avg_response_time_sec < gpt4.avg_response_time_sec else "gpt4",
            "difference_sec": abs(claude.avg_response_time_sec - gpt4.avg_response_time_sec)
        },
        "cost": {
            "claude": claude.cost_usd,
            "gpt4": gpt4.cost_usd,
            "winner": "claude" if claude.cost_usd < gpt4.cost_usd else "gpt4",
            "difference_usd": abs(claude.cost_usd - gpt4.cost_usd)
        },
        "reasoning_quality": {
            "claude": claude.reasoning_quality_score,
            "gpt4": gpt4.reasoning_quality_score,
            "winner": "claude" if claude.reasoning_quality_score > gpt4.reasoning_quality_score else "gpt4"
        }
    }
````

#### Qualitative Analysis

**Comparison Dimensions:**

| Dimension | Measurement Method | Hypothesis |
|-----------|-------------------|------------|
| **Correctness** | % test cases passed | Claude may have edge in reasoning |
| **Response Time** | Average latency | GPT-4 potentially faster API |
| **Cost** | $ per test suite | Claude generally more cost-effective |
| **Reasoning Quality** | Human evaluation (1-5) | Claude may explain decisions better |
| **Tool Use** | % correct MCP calls | Should be similar |
| **Negotiation** | % conflicts resolved | Claude may be more diplomatic |
| **Consistency** | Variance across runs | Measure stability |

#### Activities
- ✅ Run test suite with Claude Sonnet 4
- ✅ Run identical suite with GPT-4
- ✅ Collect detailed metrics
- ✅ Perform statistical analysis
- ✅ Document qualitative differences
- ✅ Create visualization

#### Deliverables
- **Comparison report** with charts
- **Statistical analysis**
- **Provider recommendations**
- **Cost-benefit analysis**

---

### 4.3 Advanced Workflow: Mission Planning (Week 15)

#### Complex Mission Scenario

**"Strike Package Escort" Scenario:**
````python
MISSION_SCENARIO = {
    "name": "Strike Package Escort - Operation Thunderbolt",
    "objectives": [
        "Destroy enemy command center at coordinates [36.2, -118.5]",
        "Minimize friendly casualties",
        "Maintain EMCON until H-hour",
        "Complete mission within 2-hour window"
    ],
    "force_package": {
        "strike": [
            {"asset": "F-35A-01", "role": "strike", "weapons": ["JDAM"]},
            {"asset": "F-35A-02", "role": "strike", "weapons": ["JDAM"]}
        ],
        "escort": [
            {"asset": "EA-18G-01", "role": "jamming", "systems": ["ALQ-99"]},
            {"asset": "EA-18G-02", "role": "jamming", "systems": ["ALQ-99"]}
        ],
        "isr": [
            {"asset": "RQ-4-01", "role": "ISR", "sensors": ["SAR", "SIGINT"]}
        ],
        "c2": [
            {"asset": "E-3-01", "role": "AWACS", "systems": ["radar", "datalink"]}
        ]
    },
    "spectrum_requirements": {
        "F-35A": {"frequency": 300.0, "bandwidth": 25.0, "purpose": "LINK-16"},
        "EA-18G": {"frequency": 2800.0, "bandwidth": 100.0, "purpose": "jamming"},
        "RQ-4": {"frequency": 9500.0, "bandwidth": 500.0, "purpose": "SAR"},
        "E-3": {"frequency": 1090.0, "bandwidth": 10.0, "purpose": "IFF"}
    },
    "complications": [
        "Friendly forces using overlapping frequencies in adjacent AO",
        "Enemy has S-400 SAM with advanced EW capabilities",
        "Weather degrading some sensor performance",
        "Mission timing synchronized with ground operation"
    ],
    "constraints": [
        "No civilian interference",
        "Minimize electronic emissions before H-hour",
        "Coordinate with Navy operations 100 km south"
    ]
}
````

#### Workflow Implementation

**workflows/mission_planning.py:**
````python
async def execute_mission_planning_workflow(scenario: Dict):
    """
    Complex mission planning with full agent coordination
    """
    
    logger.info("mission_planning_started", mission=scenario["name"])
    
    # Phase 1: Requirements Analysis (5 min)
    logger.info("phase_1", name="Requirements Analysis")
    
    # Spectrum Manager analyzes all requirements
    spectrum_analysis = await spectrum_mgr.analyze_mission_requirements(
        scenario["spectrum_requirements"]
    )
    
    # ISR Manager assesses threat environment
    threat_analysis = await isr_mgr.assess_threat_environment(
        target_location=scenario["objectives"][0],
        enemy_capabilities=["S-400 SAM"]
    )
    
    # Phase 2: Initial Allocation Attempt (5 min)
    logger.info("phase_2", name="Initial Allocation")
    
    allocation_requests = []
    for asset, requirements in scenario["spectrum_requirements"].items():
        request = await spectrum_mgr.process_request({
            "asset_id": asset,
            **requirements
        })
        allocation_requests.append(request)
    
    # Check for conflicts
    conflicts = [req for req in allocation_requests if req["status"] == "CONFLICT"]
    
    # Phase 3: Conflict Resolution (10 min)
    if conflicts:
        logger.info("phase_3", name="Conflict Resolution", num_conflicts=len(conflicts))
        
        # Multi-agent negotiation
        resolution = await resolve_mission_conflicts(
            conflicts,
            spectrum_mgr,
            isr_mgr,
            ew_planner
        )
    
    # Phase 4: EW Planning (5 min)
    logger.info("phase_4", name="EW Planning")
    
    ew_plan = await ew_planner.develop_jamming_plan(
        threat_analysis,
        allocated_frequencies=[req["frequency"] for req in allocation_requests]
    )
    
    # Analyze EW plan impact
    coa_analysis = await embm.analyze_coa_impact(
        coa_id="mission-thunderbolt-ew",
        friendly_actions=ew_plan["actions"]
    )
    
    # Phase 5: Final Plan Generation (5 min)
    logger.info("phase_5", name="Final Plan")
    
    final_plan = {
        "mission_id": "thunderbolt-001",
        "spectrum_allocations": allocation_requests,
        "ew_plan": ew_plan,
        "risk_assessment": coa_analysis,
        "timeline": generate_mission_timeline(scenario),
        "contingencies": generate_contingencies(conflicts, ew_plan)
    }
    
    # Phase 6: Validation
    validation = validate_mission_plan(final_plan, scenario["constraints"])
    
    logger.info(
        "mission_planning_completed",
        plan=final_plan,
        validation=validation
    )
    
    return final_plan, validation
````

#### Success Criteria
- ✅ All spectrum needs met without interference
- ✅ Plan generated within 30 minutes
- ✅ ROE violations caught
- ✅ Reasonable justification for all decisions
- ✅ Handles dynamic changes (new threat mid-planning)

#### Activities
- ✅ Implement mission planning workflow
- ✅ Test with realistic scenarios
- ✅ Simulate dynamic changes
- ✅ Record full decision trace
- ✅ Create visualization

#### Deliverables
- **Demo-ready mission planning scenario**
- **Full workflow trace**
- **Visualization of plan**
- **Performance metrics**

---

### 4.4 Methodology Documentation (Week 16)

#### Comprehensive Playbook

**docs/methodology/PLAYBOOK.md:**
````markdown
# AI Agent Prototyping Methodology
## Lessons from EMBM-J DS Multi-Agent System

### 1. Architecture Patterns

#### Pattern 1: External Agents + MCP Integration
**When to use:**
- Need LLM provider flexibility
- Faster prototyping without platform lock-in
- Want to prove concepts before production integration

**Trade-offs:**
- Less integration with platform features
- Manual security/governance implementation
- Separate deployment from main system

**Implementation:**
- Python + LangChain/LangGraph
- MCP for standardized tool calling
- Message broker for agent coordination

#### Pattern 2: LLM Abstraction Layer
**Why essential:**
- Compare providers objectively
- A/B testing in production
- Cost optimization
- Resilience (failover)

**Implementation:**
```python
class LLMProvider(ABC):
    async def complete(self, messages, tools, **kwargs) -> LLMResponse
```

#### Pattern 3: Broker for Multi-Agent
**Advantages:**
- Loose coupling between agents
- Central observability
- Easy to add/remove agents
- Message prioritization

**Disadvantages:**
- Single point of failure (mitigated with resilience patterns)
- Slight latency overhead

### 2. Agent Design Guidelines

#### System Prompt Design
````
✅ DO:
- Define clear role and responsibilities
- Embed domain expertise
- Specify tools available
- Provide decision framework
- Include constraints (ROE, policy)
- Use examples of good reasoning

❌ DON'T:
- Leave role ambiguous
- Assume general knowledge is enough
- Omit tool descriptions
- Be vague about success criteria
````

#### Workflow Design with LangGraph
````
✅ DO:
- Explicit state definition
- Clear node responsibilities
- Deterministic transitions
- Error handling at each node
- Timeout mechanisms
- Human-in-the-loop points

❌ DON'T:
- Rely on implicit state
- Create ambiguous transitions
- Ignore error cases
- Allow infinite loops
````

#### Testing Strategy
````
1. Unit tests: Each tool call, each node
2. Integration tests: Full workflows
3. Ground truth tests: Known correct answers
4. Failure mode tests: Edge cases, errors
5. Performance tests: Latency, cost
````

### 3. Common Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **LLM Hallucination** | Makes up tool responses | Strict tool use, validate all outputs |
| **Infinite Loops** | Agents negotiate forever | Max iteration limits, deadlock detection |
| **Over-prompting** | High costs, slow | Extract deterministic logic to code |
| **Poor Observability** | Can't debug failures | Structured logging, conversation replay |
| **Brittle Prompts** | Small changes break system | Test prompt variations, use structured outputs |
| **State Management** | Agents forget context | Explicit state passing, conversation history |

### 4. LLM Provider Selection

#### Cost vs Performance Trade-offs

| Provider | Best For | Avoid For |
|----------|----------|-----------|
| **Claude Sonnet 4** | Complex reasoning, long context | Simple tasks, cost-sensitive |
| **GPT-4 Turbo** | Fast response, broad knowledge | Deep reasoning, cost control |
| **Claude Haiku** | High-volume, simple tasks | Complex workflows |

#### Provider-Specific Tips

**Anthropic Claude:**
- Excellent at following instructions
- Strong with structured outputs
- Better at explaining reasoning
- Use thinking tags for complex tasks

**OpenAI GPT-4:**
- Faster response times
- Good at creative tasks
- May need more prompt engineering
- Strong function calling

### 5. Migration Path: Prototype → Production

#### Phase 1: External Agents (Current)
✅ Fast development
✅ Provider flexibility
✅ Easy testing
❌ Not integrated with Palantir Ontology
❌ Separate auth/authorization

#### Phase 2: Hybrid Integration
- Move agents to Palantir AIP Agent Studio
- Keep MCP to external systems
- Use Palantir Ontology for state
- Leverage Palantir security

**Migration Steps:**
1. Port agent logic to AIP Agent Studio
2. Replace message broker with AIP Logic orchestration
3. Map state to Ontology objects
4. Integrate with Palantir security model
5. Test equivalence with external version

#### Phase 3: Full Integration
- External systems integrated into Palantir
- Agents interact with Ontology directly
- Unified security and governance
- Production deployment

### 6. Debugging Guide

#### Agent Not Making Progress
````
1. Check conversation history - is agent stuck in loop?
2. Examine LLM prompts - are instructions clear?
3. Review tool calls - are they succeeding?
4. Check state - is information being passed?
````

#### Agent Making Wrong Decisions
````
1. Review system prompt - is domain knowledge sufficient?
2. Test with simpler scenarios - does basic case work?
3. Check training data - did LLM see similar problems?
4. Add more examples to prompt
````

#### Performance Issues
````
1. Count LLM calls - can any be cached/eliminated?
2. Check token usage - are prompts too long?
3. Profile workflow - where's the bottleneck?
4. Consider cheaper LLM for simple steps
````

### 7. Best Practices Summary

**Architecture:**
- Use message broker for multi-agent
- LLM abstraction for flexibility
- MCP for external integration

**Development:**
- Start simple, add complexity gradually
- Test each component in isolation
- Use ground truth test cases
- Measure everything

**Agents:**
- Clear system prompts with domain knowledge
- Explicit state management
- Comprehensive error handling
- Human escalation paths

**Deployment:**
- Structured logging for observability
- Metrics tracking (cost, latency, accuracy)
- Gradual rollout with A/B testing
- Continuous validation against test suite
````

#### Activities
- ✅ Write comprehensive methodology doc
- ✅ Create architecture decision records
- ✅ Document design patterns
- ✅ Write troubleshooting guide
- ✅ Create tutorial for new developers

#### Deliverables
- **Methodology playbook** (50+ pages)
- **Architecture patterns** library
- **Decision records**
- **Troubleshooting guide**

---

### 4.5 Demo & Presentation (Week 16)

#### Demo Package

**1. Live Demo Script:**
````
1. System Overview (2 min)
   - Architecture diagram
   - Agent roles
   - MCP integration

2. Simple Workflow (5 min)
   - Frequency deconfliction request
   - Show agent reasoning
   - Display EMBM interaction
   - Show dashboard

3. Complex Workflow (8 min)
   - Pop-up threat scenario
   - Multi-agent coordination
   - Negotiation example
   - Final plan execution

4. LLM Comparison (3 min)
   - Side-by-side metrics
   - Cost comparison
   - Reasoning quality examples

5. Lessons Learned (2 min)
   - Key insights
   - Path to production
````

**2. Presentation Deck:**
- Problem statement
- Architecture overview
- Agent capabilities
- Results and metrics
- LLM comparison
- Lessons learned
- Next steps

**3. Video Walkthrough:**
- 15-minute narrated demo
- Screen recording with voiceover
- Highlights of key capabilities

**4. Executive Summary:**
- One-page overview
- Key metrics
- Recommendations

#### Deliverables
- ✅ Live demo environment
- ✅ Presentation deck (30 slides)
- ✅ Video walkthrough (15 min)
- ✅ Executive summary (1 page)
- ✅ Technical documentation

**Phase 4 Complete:** System validated, documented, and demo-ready

---

## Resource Requirements

### Team Composition

| Role | Responsibilities | Time Commitment |
|------|------------------|-----------------|
| **Technical Lead** | Architecture, LLM integration, code review | Full-time (16 weeks) |
| **Software Engineer 1** | MCP server, EMBM mock, agents | Full-time (16 weeks) |
| **Software Engineer 2** | Agents, workflows, testing | Full-time (16 weeks) |
| **EMBM/EW SME** | Domain validation, workflow design, testing | Part-time (~20 hours) |
| **Palantir Specialist** | Integration planning, Phase 4 guidance | Consulting (~10 hours) |

### Infrastructure

**Development Environment:**
- Cloud compute: AWS or GCP (3x small instances)
- API Credits:
  - Anthropic: $5,000-$10,000
  - OpenAI: $3,000-$5,000
- GitHub repo with CI/CD
- Development tools: VS Code, PyCharm

**Demo Environment:**
- Persistent demo server
- Domain name + SSL certificate
- Monitoring stack (Grafana, Prometheus)
- Backup and recovery

**Estimated Costs:**
- Infrastructure: $1,000-$2,000
- LLM API: $8,000-$15,000
- Tools/Services: $500-$1,000
- **Total: $10,000-$18,000**

### External Dependencies

**Critical:**
- EMBM-J DS documentation (if available)
- SME availability for Phase 0 and validation
- Anthropic/OpenAI API access

**Nice to Have:**
- Access to real EMBM-J DS for comparison
- Palantir sandbox environment
- Additional SMEs for validation

---

## Risk Management

### High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Insufficient domain knowledge** | Medium | High | Early SME engagement in Phase 0; extensive documentation review; validate workflows iteratively |
| **LLM limitations** | Medium | High | Start with simple workflows; progressive complexity; have human fallback; test with multiple providers |
| **MCP integration complexity** | Low | Medium | Build mock server first; isolate integration layer; use standard JSON-RPC |
| **Agent reasoning failures** | High | Medium | Extensive testing; prompt iteration; clear success criteria; human oversight |
| **Scope creep** | High | Medium | Firm phase gates; prioritize ruthlessly; cut scope not quality |

### Medium-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Provider API outages** | Low | Low | Local model fallback; retry logic; circuit breakers |
| **Team availability** | Medium | Medium | Clear task ownership; documentation; pair programming |
| **Unrealistic expectations** | Medium | Medium | Clear success metrics; demo early and often; manage stakeholder expectations |
| **Technical debt** | Medium | Low | Code reviews; refactoring sprints; documentation |

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Single-agent test pass rate** | >80% | Automated test suite |
| **Multi-agent test pass rate** | >70% | Automated test suite |
| **Average workflow time** | <60 sec | Performance testing |
| **ROE violation detection** | >95% | Compliance tests |
| **Conflict auto-resolution** | >60% | Negotiation tests |
| **MCP call success rate** | >95% | Integration tests |

### Qualitative Metrics

| Metric | Success Criteria |
|--------|------------------|
| **SME Assessment** | "Represents realistic EMBM workflows" |
| **LLM Comparison** | Clear understanding of tradeoffs documented |
| **Demo Quality** | Ready for external stakeholder presentation |
| **Methodology** | Another team can replicate approach |

### Strategic Metrics

| Metric | Success Criteria |
|--------|------------------|
| **Integration Path** | Clear migration to Palantir documented |
| **Reusable Patterns** | Architecture patterns documented and generalized |
| **Lessons Learned** | Comprehensive documentation of insights |
| **Stakeholder Buy-in** | Approval for next phase/production development |

---

## Timeline Summary

### Week-by-Week Breakdown
````
PHASE 0: Foundation & Requirements
├─ Week 1: Domain knowledge, SME interviews, workflow definition
└─ Week 2: Architecture design, environment setup

PHASE 1: Mock EMBM-J DS MCP Server
├─ Week 3: Core MCP server implementation, tool definitions
├─ Week 4: Business logic (deconfliction, ROE, COA analysis)
└─ Week 5: Observability, dashboard, debugging tools

PHASE 2: Agent Foundation & MCP Integration
├─ Week 6: LLM abstraction layer, MCP client library
├─ Week 7: Spectrum Manager agent
├─ Week 8: ISR Collection Manager agent
└─ Week 9: EW Planner agent

PHASE 3: Multi-Agent Collaboration
├─ Week 10: Communication infrastructure, broker, messages
├─ Week 11: Conversation capabilities, Workflow 1 (frequency allocation)
├─ Week 12: Workflow 2 (pop-up threat response)
└─ Week 13: Conflict resolution, negotiation protocols

PHASE 4: Validation, Comparison & Documentation
├─ Week 14: Validation framework, LLM comparison setup
├─ Week 15: Advanced mission planning workflow, comparison analysis
└─ Week 16: Methodology documentation, demo preparation

TOTAL: 16 weeks (4 months)
````

### Milestone Gates

| Week | Milestone | Deliverable | Gate Criteria |
|------|-----------|-------------|---------------|
| **2** | Phase 0 Complete | Requirements & Architecture | Approved by stakeholders |
| **5** | Phase 1 Complete | MCP Server Functional | All tools working, tests passing |
| **9** | Phase 2 Complete | All Agents Working | 3 agents complete independent workflows |
| **13** | Phase 3 Complete | Multi-Agent Workflows | Coordination and negotiation demonstrated |
| **16** | Phase 4 Complete | Final Demo & Docs | System validated, demo-ready |

---

## Next Steps: Transition to Implementation

### When You're Ready to Start:

**1. Open Claude Code**

**2. Navigate to your project directory:**
````bash
cd /path/to/your/projects
````

**3. Share this document:**
Upload `PROJECT_PLAN.md` to Claude Code

**4. Begin Phase 0.3:**
"I have the complete project plan in PROJECT_PLAN.md.
Let's begin Phase 0.3: Development Environment Setup.
Create the project structure in ./embm-agent-prototype/"

### What Claude Code Will Do:

1. Create all directories and files from the project structure
2. Set up `pyproject.toml` with dependencies
3. Create configuration files (`.env.example`, `.gitignore`)
4. Write initial documentation (`README.md`, `ARCHITECTURE.md`)
5. Set up git repository
6. Create skeleton files for Phase 1

### Then Proceed Through Phases:

- **Weeks 1-2:** Complete Phase 0 requirements gathering
- **Week 3:** Begin Phase 1.1 with Claude Code implementing MCP server
- Continue iteratively through all phases

---

## Document Control

**Version:** 1.0  
**Last Updated:** October 16, 2025  
**Authors:** Project Planning Team  
**Status:** Approved for Implementation  

**Revision History:**
- v1.0 (Oct 16, 2025): Initial comprehensive plan

---

**END OF DOCUMENT**