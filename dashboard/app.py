"""
EMBM-J DS Interactive Chat Demo with LLM Integration.

A Streamlit-based chat interface that demonstrates:
- Real-time agent interaction with LLM
- Spectrum management queries
- Multi-turn conversations
- Tool calling and MCP integration
"""

import streamlit as st
import asyncio
import os
from datetime import datetime, timezone, timedelta
import structlog
import nest_asyncio

from llm_abstraction import get_global_registry, LLMConfig
from mcp_client import MCPClient
from agents import SpectrumManagerAgent

# Allow nested event loops (needed for Streamlit + async code)
nest_asyncio.apply()

logger = structlog.get_logger()

# Configure Streamlit page
st.set_page_config(
    page_title="EMBM-J DS Chat Demo",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .agent-message {
        background-color: #e3f2fd;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #1976d2;
    }
    .user-message {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #666;
    }
    .system-message {
        background-color: #fff3e0;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #f57c00;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_agent():
    """Initialize the agent and MCP client (cached for performance)."""
    try:
        server_url = os.getenv("EMBM_SERVER_URL", "http://localhost:8000")
        
        # Initialize MCP client
        mcp_client = MCPClient(server_url)
        
        # Initialize LLM provider
        registry = get_global_registry()
        llm_provider = registry.get_provider()
        
        # Create Spectrum Manager agent
        agent = SpectrumManagerAgent(
            llm_provider=llm_provider,
            mcp_client=mcp_client,
            max_iterations=10
        )
        
        return agent, mcp_client, llm_provider
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None, None, None


def format_message(role: str, content: str) -> str:
    """Format a message with appropriate styling."""
    if role == "user":
        return f'<div class="user-message"><b>You:</b> {content}</div>'
    elif role == "assistant":
        return f'<div class="agent-message"><b>Agent:</b> {content}</div>'
    else:
        return f'<div class="system-message"><b>System:</b> {content}</div>'


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


def process_user_input(user_input: str, agent, mcp_client):
    """Process user input through the agent (sync wrapper)."""
    try:
        # Use asyncio.run() which properly handles the event loop
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


def main():
    """Main Streamlit app."""
    # Sidebar configuration
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        server_url = st.text_input(
            "MCP Server URL",
            value=os.getenv("EMBM_SERVER_URL", "http://localhost:8000")
        )
        
        st.markdown("---")
        st.subheader("📊 System Status")
        
        agent, mcp_client, llm_provider = initialize_agent()
        
        if agent and mcp_client and llm_provider:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("LLM Provider", llm_provider.get_provider_name())
            with col2:
                st.metric("Model", llm_provider.config.model)
            
            # Health check
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    is_healthy = loop.run_until_complete(mcp_client.health_check())
                else:
                    is_healthy = asyncio.run(mcp_client.health_check())
                status = "🟢 Healthy" if is_healthy else "🔴 Unhealthy"
                st.metric("MCP Server", status)
            except Exception as e:
                st.metric("MCP Server", "🔴 Offline")
        else:
            st.error("Failed to initialize system")
            return
        
        st.markdown("---")
        st.subheader("💡 Example Queries")
        st.markdown("""
        - "Can I use 151.5 MHz for a training exercise?"
        - "What frequencies are available in my area?"
        - "Check for interference on 225 MHz"
        - "Allocate frequency for ISR collection"
        """)
    
    # Main content
    st.title("🛰️ EMBM-J DS Spectrum Management Chat")
    st.markdown("""
    Welcome to the interactive EMBM-J DS chat demo! Ask questions about spectrum allocation,
    frequency management, and electromagnetic operations. The agent will use real MCP tools
    to provide accurate information.
    """)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm the EMBM-J DS Spectrum Manager Agent. I can help you with frequency allocation, spectrum planning, and electromagnetic operations. What would you like to know?"
            }
        ]
    
    # Display chat history
    st.subheader("💬 Conversation")
    chat_container = st.container(height=400)
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    st.markdown("---")
    user_input = st.chat_input("Ask about spectrum allocation, frequencies, or operations...")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
    EMBM-J DS Multi-Agent Prototype | Powered by Claude + MCP
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

