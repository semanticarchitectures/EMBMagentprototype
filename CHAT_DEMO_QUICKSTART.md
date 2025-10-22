# Chat Demo - Quick Start Guide

Get the LLM-powered chat demo running in 5 minutes!

## 1. Prerequisites

✅ Python 3.11+
✅ Anthropic API key (or OpenAI key)
✅ Project dependencies installed

```bash
# If not already done, install dependencies
pip install -e .
```

## 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-...
# EMBM_SERVER_URL=http://localhost:8000
```

Or set environment variables directly:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export EMBM_SERVER_URL="http://localhost:8000"
```

## 3. Start MCP Server

In **Terminal 1**:

```bash
python scripts/run_server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's working:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

## 4. Run Chat Demo

### Option A: Command-Line Chat

In **Terminal 2**:

```bash
python scripts/chat_demo.py
```

You'll see:
```
======================================================================
EMBM-J DS Spectrum Management Chat Demo
======================================================================

🔌 Connecting to MCP Server: http://localhost:8000
✅ MCP server is healthy
✅ Discovered 6 MCP tools
🤖 Initializing LLM Provider: anthropic
✅ Using Anthropic
   Model: claude-sonnet-4-20250514
👤 Creating Spectrum Manager Agent...
✅ Agent ready!

Type 'help' for commands, 'exit' to quit

Agent: Hello! I'm the EMBM-J DS Spectrum Manager Agent...

You: 
```

Now type your questions!

### Option B: Web Interface

In **Terminal 2**:

```bash
streamlit run dashboard/app.py
```

Open your browser to: `http://localhost:8501`

## 5. Try Some Queries

### Query 1: Check Frequency Availability

```
You: Can I use 151.5 MHz for a training exercise?

Agent: I'll check if 151.5 MHz is available for your training exercise...
[Agent queries MCP server]
Agent: Good news! 151.5 MHz appears to be available...
```

### Query 2: Get Spectrum Plan

```
You: What frequencies are available in my area?

Agent: I'll retrieve the spectrum plan for your area...
[Agent queries spectrum plan]
Agent: Here are the available frequencies...
```

### Query 3: Check Interference

```
You: Check for interference on 225 MHz

Agent: I'll analyze the interference environment on 225 MHz...
[Agent queries interference report]
Agent: The interference analysis shows...
```

### Query 4: Allocate Frequency

```
You: Allocate frequency for ISR collection

Agent: I'll help you allocate a frequency for ISR collection...
[Agent processes allocation request]
Agent: Frequency allocation successful...
```

## 6. Available Commands (CLI Only)

```
help     - Show available commands
history  - View conversation history
exit     - Exit the chat
```

## 7. Troubleshooting

### "MCP server is not responding"

```bash
# Check if server is running
curl http://localhost:8000/health

# If not, start it in Terminal 1
python scripts/run_server.py
```

### "API key not found"

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="your-key-here"
```

### "Connection refused"

```bash
# Make sure MCP server is running on port 8000
lsof -i :8000

# If nothing is running, start the server
python scripts/run_server.py
```

### Streamlit not found

```bash
# Install Streamlit
pip install streamlit

# Or install with dashboard dependencies
pip install -e ".[dashboard]"
```

## 8. Next Steps

### Explore More Features

- **Multi-turn conversations**: Ask follow-up questions
- **Tool integration**: Watch the agent call MCP tools
- **Spectrum operations**: Try different frequency scenarios
- **Workflow coordination**: See agents working together

### Customize the Demo

1. **Change LLM Provider**:
   ```bash
   python scripts/chat_demo.py --provider openai
   ```

2. **Modify Agent Behavior**:
   Edit `agents/spectrum_manager/agent.py` and change the `SYSTEM_PROMPT`

3. **Add Custom Tools**:
   Add new tools to `mcp_server/tools.py` and they'll be auto-discovered

### Run Full Workflows

```bash
# Run frequency allocation workflow
python scripts/run_agents.py --workflow frequency_allocation

# Run other workflows
python scripts/run_agents.py --workflow popup_threat
python scripts/run_agents.py --workflow mission_planning
```

## 9. Understanding the Architecture

```
Your Question
    ↓
Chat Interface (CLI or Web)
    ↓
LLM Agent (Claude/GPT-4)
    ↓
MCP Client (JSON-RPC)
    ↓
MCP Server (EMBM-J DS)
    ↓
Business Logic (Deconfliction, ROE, etc.)
    ↓
Response Back to You
```

## 10. Tips for Best Results

✅ **Be specific**: "Allocate 151.5 MHz for training" works better than "allocate frequency"

✅ **Ask follow-ups**: "What about 225 MHz?" builds on previous context

✅ **Check status**: Use `history` command to see what the agent has done

✅ **Watch the logs**: Check terminal output to see MCP tool calls

✅ **Be patient**: First query may take a few seconds as agent initializes

## 11. Common Queries

| Query | Purpose |
|-------|---------|
| "What frequencies are available?" | Get spectrum plan |
| "Can I use X MHz?" | Check availability |
| "Allocate frequency for Y" | Request allocation |
| "Check interference on X MHz" | Analyze interference |
| "What's the status?" | Get system status |

## 12. Getting Help

- **Chat Demo Docs**: See [CHAT_DEMO.md](CHAT_DEMO.md)
- **Project Docs**: See [README.md](README.md)
- **Architecture**: See [PROJECT.md](PROJECT.md)
- **Logs**: Check `logs/` directory

---

**Ready to chat?** Run `python scripts/chat_demo.py` now! 🚀

