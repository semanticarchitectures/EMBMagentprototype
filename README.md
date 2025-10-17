# EMBM-J DS Multi-Agent Prototype

Demonstration of AI agents collaborating via MCP (Model Context Protocol) to manage electromagnetic spectrum operations for EMBM-J DS (Electromagnetic Battle Management - Joint Decision Support).

## Overview

This prototype demonstrates:
- **MCP Integration** - Agents interact with external systems via standardized protocol
- **Multi-Agent Coordination** - Agents collaborate, negotiate, and resolve conflicts
- **EMBM Workflow Capability** - Realistic spectrum management scenarios
- **LLM Flexibility** - Support for both Anthropic Claude and OpenAI GPT-4

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Agent System                        │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   Spectrum   │  │     ISR      │             │
│  │   Manager    │  │  Collection  │             │
│  │    Agent     │  │    Manager   │             │
│  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                     │
│         └────────┬─────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │  Agent Broker   │                     │
│         └────────┬────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │   EW Planner    │                     │
│         └────────┬────────┘                     │
│                  │                               │
│         ┌────────▼────────┐                     │
│         │   MCP Client    │                     │
│         └────────┬────────┘                     │
└──────────────────┼──────────────────────────────┘
                   │ MCP Protocol (JSON-RPC 2.0)
┌──────────────────▼──────────────────────────────┐
│         Mock EMBM-J DS MCP Server                │
│  - Spectrum Planning                             │
│  - Frequency Deconfliction                       │
│  - COA Impact Analysis                           │
│  - Emitter Detection                             │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Anthropic API key (for Claude)
- OpenAI API key (for GPT-4, optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd EMBMagentprototype

# Run setup script
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### Running the System

```bash
# Terminal 1: Start MCP Server
python scripts/run_server.py

# Terminal 2: Run agents with a workflow
python scripts/run_agents.py --workflow frequency_allocation

# Optional: Start monitoring dashboard
streamlit run dashboard/app.py
```

## Workflows

The prototype demonstrates several realistic electromagnetic spectrum management workflows:

1. **Frequency Deconfliction** - Single agent approves/denies spectrum requests
2. **Pop-up Threat Response** - Multi-agent coordination for ISR retasking
3. **Joint Mission Planning** - Complex negotiation with spectrum constraints
4. **Interference Resolution** - Cross-service conflict resolution
5. **EW COA Planning** - Electronic warfare course of action analysis

## Project Structure

```
embm-agent-prototype/
├── agents/              # AI agent implementations
│   ├── spectrum_manager/
│   ├── isr_manager/
│   └── ew_planner/
├── mcp_server/         # Mock EMBM-J DS MCP server
├── mcp_client/         # MCP client library
├── llm_abstraction/    # LLM provider abstraction layer
├── broker/             # Agent-to-agent message broker
├── workflows/          # Workflow orchestration
├── dashboard/          # Monitoring dashboard
├── tests/              # Test suites
└── evaluation/         # Evaluation and comparison tools
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# With coverage
pytest --cov=agents --cov=mcp_server
```

### Code Quality
```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy agents/ mcp_server/ mcp_client/
```

## Documentation

- [Project Plan](PROJECT.md) - Complete 16-week development plan
- [Architecture](docs/ARCHITECTURE.md) - Detailed system architecture
- [Workflow Specifications](docs/workflow_specs/) - Detailed workflow descriptions
- [ADRs](docs/adr/) - Architecture Decision Records

## Technology Stack

- **Python 3.11+** - Core language
- **LangChain/LangGraph** - Agent orchestration
- **FastAPI** - MCP server implementation
- **Anthropic Claude Sonnet 4** - Primary LLM
- **OpenAI GPT-4 Turbo** - Secondary LLM (for comparison)
- **Pydantic** - Data validation
- **Streamlit** - Dashboard UI

## License

MIT License

## Contributing

This is a prototype project. For questions or contributions, please contact the project team.
