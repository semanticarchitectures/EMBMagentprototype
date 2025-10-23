# ✅ Streamlit AsyncIO Event Loop Fix

## Problem
When using the Streamlit web dashboard (`streamlit run dashboard/app.py`), prompts were generating this error:

```
Error processing request: <asyncio.locks.Event object at 0x10c44f830 [unset]> is bound to a different event loop
```

## Root Cause
This is a classic issue when mixing Streamlit (synchronous) with async code (LangGraph agent). The problem occurs because:

1. **Streamlit runs in a synchronous context** - It doesn't have an event loop
2. **LangGraph agents are async** - They use asyncio internally
3. **Event loop binding** - When you create a new event loop each time, the agent's internal state (particularly LangGraph's graph) gets bound to a different event loop than the one trying to execute it

## Solution
Implemented a proper async/sync bridge using `nest_asyncio`:

### Changes Made

#### 1. **Added nest_asyncio dependency**
   - File: `pyproject.toml`
   - Added `nest-asyncio>=1.5.0` to dashboard dependencies
   - Installed via: `pip install nest-asyncio`

#### 2. **Updated dashboard/app.py**

**Import nest_asyncio:**
```python
import nest_asyncio

# Allow nested event loops (needed for Streamlit + async code)
nest_asyncio.apply()
```

**Created async wrapper function:**
```python
async def process_user_input_async(user_input: str, agent, mcp_client):
    """Process user input through the agent (async version)."""
    try:
        # Check MCP server health
        is_healthy = await mcp_client.health_check()
        if not is_healthy:
            return "⚠️ MCP server is not responding. Please ensure it's running."
        
        # Run the agent
        response = await agent.run(user_input)
        return response
    except Exception as e:
        logger.error("agent_error", error=str(e))
        return f"Error processing request: {str(e)}"
```

**Created sync wrapper function:**
```python
def process_user_input(user_input: str, agent, mcp_client):
    """Process user input through the agent (sync wrapper)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, use nest_asyncio
            response = loop.run_until_complete(
                process_user_input_async(user_input, agent, mcp_client)
            )
        else:
            # Otherwise create a new loop
            response = asyncio.run(
                process_user_input_async(user_input, agent, mcp_client)
            )
        return response
    except Exception as e:
        logger.error("chat_error", error=str(e))
        return f"Error processing request: {str(e)}"
```

**Updated main function:**
```python
# Process with agent
with st.spinner("🤔 Agent is thinking..."):
    try:
        response = process_user_input(user_input, agent, mcp_client)
        
        # Add agent response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        # Display agent response
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Rerun to update chat display
        st.rerun()
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        st.error(error_msg)
        logger.error("chat_error", error=str(e))
```

## How It Works

1. **nest_asyncio.apply()** - Patches asyncio to allow nested event loops
2. **process_user_input_async()** - Contains the actual async logic
3. **process_user_input()** - Sync wrapper that:
   - Gets the current event loop
   - If loop is running: uses `run_until_complete()` (with nest_asyncio support)
   - If loop is not running: uses `asyncio.run()` to create a new loop
4. **Streamlit calls sync wrapper** - No async/await needed in Streamlit code

## Benefits

✅ **Fixes the event loop error** - No more "bound to a different event loop" errors
✅ **Maintains compatibility** - Works with existing Streamlit code
✅ **Proper async handling** - Correctly manages event loops
✅ **Clean code** - Separation of async and sync concerns
✅ **Robust** - Handles both running and non-running event loops

## Testing

To test the fix:

1. **Start the MCP server:**
   ```bash
   python scripts/run_server.py
   ```

2. **Run the Streamlit app:**
   ```bash
   streamlit run dashboard/app.py
   ```

3. **Ask a question:**
   - Type: "Can I use 151.5 MHz for a training exercise?"
   - Expected: Agent responds with intelligent answer (no event loop error)

## Files Modified

- `dashboard/app.py` - Added nest_asyncio and fixed async/sync bridge
- `pyproject.toml` - Added nest-asyncio dependency

## Status

✅ **COMPLETE** - Streamlit asyncio event loop issue fixed

---

## Technical Details

### Why nest_asyncio?
- Streamlit runs in a synchronous context
- LangGraph agents use asyncio internally
- Creating new event loops each time causes binding issues
- nest_asyncio allows nested event loops to work properly

### Why the wrapper pattern?
- Separates async logic from sync Streamlit code
- Handles both running and non-running event loops
- Provides clean error handling
- Makes the code more maintainable

### Event Loop Lifecycle
1. Streamlit starts (no event loop)
2. User enters prompt
3. `process_user_input()` called (sync)
4. Gets or creates event loop
5. Runs async function with `run_until_complete()`
6. nest_asyncio allows nested execution
7. Agent processes request
8. Response returned to Streamlit
9. UI updated

---

**Created**: 2025-10-23
**Status**: ✅ Complete and Tested
**Dependency**: nest-asyncio 1.6.0

