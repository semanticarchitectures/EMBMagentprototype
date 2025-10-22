# EMBM-J DS Chat Demo with LLM Integration

An interactive chat interface that demonstrates real-time agent interaction with LLM for spectrum management operations.

## Features

✨ **Interactive Chat Interface**
- Real-time conversation with AI agent
- Multi-turn dialogue support
- Conversation history tracking

🤖 **LLM Integration**
- Powered by Claude (Anthropic) or GPT-4 (OpenAI)
- Intelligent reasoning about spectrum operations
- Natural language understanding and generation

🛠️ **MCP Tool Integration**
- Real tool calling to MCP server
- Frequency allocation queries
- Spectrum planning and deconfliction
- Interference analysis

📊 **Spectrum Management**
- Query available frequencies
- Request frequency allocations
- Check for conflicts
- Analyze electromagnetic impact

## Quick Start

### Prerequisites

1. **MCP Server Running**
   ```bash
   # Terminal 1: Start the MCP server
   python scripts/run_server.py
   ```

2. **Environment Variables**
   ```bash
   # Set your API keys
   export ANTHROPIC_API_KEY="your-key-here"
   export EMBM_SERVER_URL="http://localhost:8000"
   ```

### Option 1: Command-Line Chat Demo

```bash
# Run the interactive chat demo
python scripts/chat_demo.py

# Or specify a different LLM provider
python scripts/chat_demo.py --provider openai
```

**Commands:**
- Type your question and press Enter
- `help` - Show available commands
- `history` - View conversation history
- `exit` - Exit the chat

### Option 2: Streamlit Web Interface

```bash
# Run the Streamlit dashboard
streamlit run dashboard/app.py
```

Then open your browser to `http://localhost:8501`

## Example Conversations

### Example 1: Frequency Allocation Request

```
You: Can I use 151.5 MHz for a training exercise?

Agent: I'll check if 151.5 MHz is available for your training exercise. 
Let me query the spectrum plan and check for conflicts...

[Agent calls MCP tools to check availability]

Agent: Good news! 151.5 MHz appears to be available in your area. 
I can help you allocate this frequency. To proceed, I'll need:
- Asset ID
- Bandwidth requirement
- Power level
- Duration of the exercise
- Location coordinates

Would you like me to process the allocation?
```

### Example 2: Interference Analysis

```
You: Check for interference on 225 MHz

Agent: I'll analyze the interference environment on 225 MHz...

[Agent queries interference report from MCP server]

Agent: The interference analysis for 225 MHz shows:
- Current allocations: 2 active users
- Potential interference sources: 1 detected
- Signal-to-noise ratio: Good
- Recommendation: Frequency is suitable with proper power management

Would you like more detailed analysis?
```

### Example 3: Spectrum Planning

```
You: What frequencies are available in my area?

Agent: I'll retrieve the spectrum plan for your area...

[Agent queries spectrum plan from MCP server]

Agent: Here are the available frequencies in your area:
- 150-152 MHz: Available (25 kHz channels)
- 225-230 MHz: Partially available (some conflicts)
- 400-420 MHz: Available (50 kHz channels)

Each frequency has different characteristics. What's your use case?
```

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│     Chat Interface (CLI or Web)         │
│  - User input processing                │
│  - Conversation management              │
│  - Response display                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     LLM Agent (Claude/GPT-4)            │
│  - Natural language understanding       │
│  - Reasoning about spectrum ops         │
│  - Tool calling decisions               │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     MCP Client                          │
│  - JSON-RPC 2.0 protocol                │
│  - Tool discovery                       │
│  - Tool invocation                      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     MCP Server (EMBM-J DS)              │
│  - Spectrum planning                    │
│  - Frequency deconfliction              │
│  - Interference analysis                │
│  - COA impact assessment                │
└─────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Chat interface receives question
2. **LLM Processing** → Agent analyzes query and decides which tools to use
3. **Tool Calling** → Agent calls MCP tools via JSON-RPC
4. **MCP Execution** → Server processes request and returns results
5. **Response Generation** → Agent synthesizes response from tool results
6. **Display** → Response shown to user in chat interface

## Configuration

### Environment Variables

```bash
# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...          # Anthropic API key
OPENAI_API_KEY=sk-...                 # OpenAI API key (optional)

# MCP Server
EMBM_SERVER_URL=http://localhost:8000 # MCP server URL
EMBM_SERVER_PORT=8000                 # MCP server port

# Agent Configuration
DEFAULT_LLM_PROVIDER=anthropic         # Default LLM provider
DEFAULT_MODEL=claude-sonnet-4          # Default model
MAX_AGENT_ITERATIONS=10                # Max reasoning iterations
AGENT_TIMEOUT_SECONDS=60               # Agent timeout

# Logging
LOG_LEVEL=INFO                         # Logging level
LOG_FORMAT=json                        # Log format
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1976d2"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[client]
showErrorDetails = true
```

## Troubleshooting

### MCP Server Not Responding

```bash
# Check if server is running
curl http://localhost:8000/health

# If not running, start it
python scripts/run_server.py
```

### API Key Issues

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# If not set, add to .env
export ANTHROPIC_API_KEY="your-key-here"
```

### Agent Timeout

- Increase `MAX_AGENT_ITERATIONS` or `AGENT_TIMEOUT_SECONDS`
- Check MCP server performance
- Simplify queries

### Streamlit Issues

```bash
# Clear Streamlit cache
streamlit cache clear

# Run with debug output
streamlit run dashboard/app.py --logger.level=debug
```

## Advanced Usage

### Custom System Prompts

Edit the agent's system prompt in `agents/spectrum_manager/agent.py`:

```python
SYSTEM_PROMPT = """You are an expert spectrum manager...
[Customize for your use case]
"""
```

### Adding New Tools

1. Implement tool in MCP server (`mcp_server/tools.py`)
2. Register in tool registry (`mcp_server/main.py`)
3. Agent will automatically discover and use it

### Integration with External Systems

The chat demo can be extended to:
- Connect to real EMBM-J DS systems
- Integrate with operational databases
- Add authentication and authorization
- Implement audit logging

## Performance Tips

1. **Caching**: Streamlit caches agent initialization
2. **Async**: CLI demo uses async for responsiveness
3. **Tool Optimization**: MCP server caches tool schemas
4. **Batch Operations**: Group related queries

## Security Considerations

⚠️ **Development Only**: This demo is for development/testing

For production:
- ✅ Add authentication to MCP server
- ✅ Restrict CORS origins
- ✅ Validate all inputs
- ✅ Implement rate limiting
- ✅ Use HTTPS/TLS
- ✅ Audit all operations
- ✅ Sanitize LLM outputs

## Next Steps

1. **Extend Conversations**: Add multi-agent coordination
2. **Add Persistence**: Store conversation history
3. **Real Integration**: Connect to actual EMBM-J DS
4. **Advanced Reasoning**: Implement complex workflows
5. **Monitoring**: Add observability and metrics

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs: `tail -f logs/*.log`
3. Check MCP server health: `curl http://localhost:8000/health`
4. Review agent reasoning: Use `history` command in CLI demo

---

**Status**: ✅ Phase 2 Complete - LLM Integration Ready

