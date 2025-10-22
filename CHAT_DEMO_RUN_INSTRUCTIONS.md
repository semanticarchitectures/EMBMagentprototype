# Chat Demo - Run Instructions

## ✅ What Was Completed

The LLM integration into the chat demo is **100% complete**. Two fully functional interfaces have been created:

### 1. **CLI Chat Demo** (`scripts/chat_demo.py`)
- Interactive command-line chat interface
- Real-time LLM agent interaction
- Multi-turn conversation support
- Conversation history tracking
- Help system and commands

### 2. **Web Dashboard** (`dashboard/app.py`)
- Streamlit-based web interface
- Beautiful, responsive UI
- Real-time chat with sidebar configuration
- System status monitoring
- MCP server health checks

## 🚀 How to Run

### Prerequisites
Make sure you have:
- ✅ Python 3.10+
- ✅ All dependencies installed (`pip install -r requirements.txt`)
- ✅ API keys set in `.env` file (ANTHROPIC_API_KEY or OPENAI_API_KEY)
- ✅ MCP server running on port 8000

### Step 1: Start the MCP Server

Open a terminal and run:

```bash
python scripts/run_server.py
```

You should see:
```
==================================================
EMBM-J DS MCP Server
==================================================
Starting server at http://0.0.0.0:8000
...
```

### Step 2: Run the Chat Demo

Open a **new terminal** and run:

```bash
# CLI version (recommended for testing)
python scripts/chat_demo.py

# OR web version (for visual interface)
streamlit run dashboard/app.py
```

### Step 3: Interact with the Agent

For CLI version, you'll see:
```
======================================================================
EMBM-J DS Spectrum Management Chat Demo
======================================================================

Type 'help' for commands, 'exit' to quit

Agent: Hello! I'm the EMBM-J DS Spectrum Manager Agent...

You: 
```

Type your question and press Enter!

## 💬 Example Queries to Try

```
You: Can I use 151.5 MHz for a training exercise?
You: What frequencies are available?
You: Check interference on 225 MHz
You: Allocate 151.5 MHz for ISR collection
You: URGENT: Need frequency now!
```

## 🎯 What Happens Behind the Scenes

1. **You ask a question** → Chat interface captures input
2. **LLM processes it** → Claude/GPT-4 understands your request
3. **Agent decides tools** → Determines which MCP tools to call
4. **Tools execute** → Calls spectrum management functions
5. **Response synthesized** → Agent creates intelligent answer
6. **You get result** → Response displayed in chat

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (CLI or Streamlit Web)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              LLM Agent (Claude/GPT-4)                    │
│         - Understands user queries                       │
│         - Decides which tools to use                     │
│         - Synthesizes responses                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              MCP Client (JSON-RPC 2.0)                   │
│         - Calls MCP tools                                │
│         - Handles tool responses                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              MCP Server (FastAPI)                        │
│         - Spectrum Planning                              │
│         - Frequency Deconfliction                        │
│         - Interference Analysis                          │
│         - COA Impact Assessment                          │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Troubleshooting

### Issue: "MCP server is not responding"
**Solution**: Make sure the server is running in another terminal:
```bash
python scripts/run_server.py
```

### Issue: "API key not found"
**Solution**: Check that `.env` file has your API key:
```bash
echo $ANTHROPIC_API_KEY
```

### Issue: Agent hangs or times out
**Solution**: Check the server logs for errors:
```bash
tail -f logs/embm_agents.log
```

### Issue: "Connection refused"
**Solution**: Make sure port 8000 is not in use:
```bash
lsof -i :8000
```

## 📚 Documentation

For more detailed information, see:

- **[CHAT_DEMO_START_HERE.md](CHAT_DEMO_START_HERE.md)** - Quick entry point
- **[CHAT_DEMO_QUICKSTART.md](CHAT_DEMO_QUICKSTART.md)** - 5-minute setup
- **[CHAT_DEMO_EXAMPLES.md](CHAT_DEMO_EXAMPLES.md)** - Real examples
- **[CHAT_DEMO.md](CHAT_DEMO.md)** - Full documentation
- **[CHAT_DEMO_INTEGRATION.md](CHAT_DEMO_INTEGRATION.md)** - Architecture

## ✨ Features

✅ **Real LLM Integration**
- Anthropic Claude (default)
- OpenAI GPT-4 (optional)

✅ **Real Tool Calling**
- Actual MCP tool invocation
- JSON-RPC 2.0 protocol
- Real spectrum management operations

✅ **Multi-turn Conversations**
- Maintains context
- Understands follow-ups
- Complex reasoning

✅ **Two Interfaces**
- CLI for quick queries
- Web for demonstrations

✅ **Production Ready**
- Error handling
- Logging
- Health checks

## 🎓 Learning Path

1. **Start the server** (Terminal 1)
   ```bash
   python scripts/run_server.py
   ```

2. **Run the chat demo** (Terminal 2)
   ```bash
   python scripts/chat_demo.py
   ```

3. **Try example queries** (in chat)
   ```
   Can I use 151.5 MHz?
   What frequencies are available?
   ```

4. **Read the documentation**
   - See [CHAT_DEMO_EXAMPLES.md](CHAT_DEMO_EXAMPLES.md) for more examples
   - See [CHAT_DEMO.md](CHAT_DEMO.md) for full documentation

## 📞 Commands (CLI Version)

```
help     - Show help message
history  - Show conversation history
exit     - Exit the chat
```

## 🎉 Success Criteria

You'll know it's working when:

✅ Server starts without errors
✅ Chat demo connects to server
✅ You can type a question
✅ Agent responds with intelligent answer
✅ Agent calls MCP tools
✅ Conversation history is maintained

## 🚀 Next Steps

1. **Try the CLI version first** - It's simpler and faster
2. **Ask the example queries** - See how the agent responds
3. **Try the web version** - For a more visual experience
4. **Customize the system prompt** - Modify agent behavior
5. **Add your own queries** - Test with your own questions

## 📝 Files Created

- `scripts/chat_demo.py` - CLI chat interface (211 lines)
- `dashboard/app.py` - Web dashboard (233 lines)
- `test_chat_demo.py` - Test script (non-interactive)
- `test_llm_simple.py` - LLM provider test
- 9 documentation files (~1,700 lines)

## ✅ Status

**LLM Integration: COMPLETE ✅**

The chat demo is fully functional and ready to use!

---

**Ready to chat? Start with:**
```bash
python scripts/run_server.py  # Terminal 1
python scripts/chat_demo.py   # Terminal 2
```

Enjoy! 🎉

