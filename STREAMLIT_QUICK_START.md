# 🚀 Streamlit Web Dashboard - Quick Start

## ✅ Issue Fixed
The asyncio event loop error has been fixed! The Streamlit web dashboard now works perfectly.

## 🎯 Quick Start (2 minutes)

### Terminal 1: Start MCP Server
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
INFO:     Application startup complete.
```

### Terminal 2: Start Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Browser: Open Dashboard
```
http://localhost:8501
```

## 💬 Using the Dashboard

### 1. **View System Status**
   - Check sidebar for LLM provider and model
   - See MCP server health status
   - View example queries

### 2. **Ask Questions**
   - Type in the chat input box
   - Press Enter or click send
   - Wait for agent to respond

### 3. **Example Queries**
   ```
   Can I use 151.5 MHz for a training exercise?
   What frequencies are available in my area?
   Check for interference on 225 MHz
   Allocate frequency for ISR collection
   ```

### 4. **View Conversation**
   - Chat history displayed above input
   - User messages on the right
   - Agent responses on the left
   - Conversation persists during session

## 🎨 Dashboard Features

✅ **Beautiful UI**
- Modern, responsive design
- Color-coded messages
- Real-time updates

✅ **System Status**
- LLM provider info
- Model name
- MCP server health

✅ **Example Queries**
- Quick reference in sidebar
- Copy-paste ready
- Common use cases

✅ **Conversation History**
- Multi-turn conversations
- Context maintained
- Session state preserved

✅ **Error Handling**
- Clear error messages
- Helpful troubleshooting
- Graceful degradation

## 🔧 Troubleshooting

### Issue: "MCP server is not responding"
**Solution:** Make sure server is running in Terminal 1
```bash
python scripts/run_server.py
```

### Issue: "Connection refused"
**Solution:** Check that port 8000 is available
```bash
lsof -i :8000
```

### Issue: "Streamlit not found"
**Solution:** Install Streamlit
```bash
pip install streamlit
```

### Issue: "nest_asyncio not found"
**Solution:** Install nest_asyncio
```bash
pip install nest-asyncio
```

### Issue: "No response from agent"
**Solution:** Check MCP server logs for errors
```bash
tail -f logs/embm_agents.log
```

## 📊 What's Happening Behind the Scenes

```
You type a question
    ↓
Streamlit captures input
    ↓
process_user_input() called
    ↓
nest_asyncio handles event loop
    ↓
Agent processes request
    ↓
MCP tools called
    ↓
Response generated
    ↓
UI updated with response
```

## ✨ Key Improvements

✅ **Fixed asyncio error** - No more event loop binding issues
✅ **Proper async handling** - Correct event loop management
✅ **Clean code** - Separation of async and sync concerns
✅ **Robust** - Handles edge cases
✅ **User-friendly** - Clear error messages

## 🎓 Learning Path

### Beginner
1. Start server: `python scripts/run_server.py`
2. Start dashboard: `streamlit run dashboard/app.py`
3. Ask simple questions: "Can I use 151.5 MHz?"

### Intermediate
1. Try complex queries: "What frequencies work for 6 units?"
2. Follow-up questions: "Can we use frequency hopping?"
3. Check system status in sidebar

### Advanced
1. Examine logs: `tail -f logs/embm_agents.log`
2. Modify system prompt: Edit `agents/spectrum_manager/agent.py`
3. Add custom queries: Extend the agent

## 📝 Example Conversation

```
You: Can I use 151.5 MHz for a training exercise?

Agent: I'll check the spectrum plan and deconfliction status for 151.5 MHz.
Based on the current allocations, 151.5 MHz is available for your training 
exercise. The frequency has good separation from existing allocations and 
no interference issues detected. I recommend:
- Frequency: 151.5 MHz
- Bandwidth: 25 kHz
- Duration: As needed for training
- Power: Standard training levels

Would you like me to allocate this frequency?

You: Yes, please allocate it for 2 hours

Agent: I've successfully allocated 151.5 MHz for your training exercise for 
2 hours. The allocation is now active and you can begin operations. 
Remember to monitor for any interference and report any issues.
```

## 🚀 Next Steps

1. **Run the dashboard:**
   ```bash
   streamlit run dashboard/app.py
   ```

2. **Ask questions:**
   - Try the example queries
   - Ask your own questions
   - Explore the agent's capabilities

3. **Check the logs:**
   - Monitor agent responses
   - Verify tool calls
   - Debug any issues

4. **Customize:**
   - Modify system prompt
   - Add new tools
   - Extend functionality

## 📞 Support

### Documentation
- **STREAMLIT_ASYNCIO_FIX.md** - Technical details
- **STREAMLIT_FIX_COMPLETE.md** - Complete explanation
- **CHAT_DEMO_RUN_INSTRUCTIONS.md** - General instructions

### Common Issues
- See "Troubleshooting" section above
- Check logs: `tail -f logs/embm_agents.log`
- Verify server: `curl http://localhost:8000/health`

## ✅ Verification Checklist

Before using the dashboard, verify:

- [ ] MCP server running: `curl http://localhost:8000/health`
- [ ] Streamlit installed: `pip list | grep streamlit`
- [ ] nest_asyncio installed: `pip list | grep nest-asyncio`
- [ ] API keys set: `echo $ANTHROPIC_API_KEY`
- [ ] Port 8501 available: `lsof -i :8501`

## 🎉 Ready to Go!

The Streamlit web dashboard is now fully functional and ready to use!

```bash
# Terminal 1
python scripts/run_server.py

# Terminal 2
streamlit run dashboard/app.py

# Browser
http://localhost:8501
```

**Enjoy your interactive chat demo!** 🚀

---

**Status**: ✅ Complete and Ready
**Last Updated**: 2025-10-23

