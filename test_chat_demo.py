#!/usr/bin/env python3
"""
Test script for chat demo - non-interactive version.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_abstraction import get_global_registry
from mcp_client import MCPClient
from agents import SpectrumManagerAgent


async def test_chat_demo():
    """Test the chat demo with predefined queries."""
    
    print("\n" + "="*70)
    print("EMBM-J DS Chat Demo - Test Mode")
    print("="*70 + "\n")
    
    # Initialize
    server_url = os.getenv("EMBM_SERVER_URL", "http://localhost:8000")
    
    print(f"🔌 Connecting to MCP Server: {server_url}")
    mcp_client = MCPClient(server_url)
    
    # Check health
    is_healthy = await mcp_client.health_check()
    if not is_healthy:
        print("❌ MCP server is not responding")
        return
    print("✅ MCP server is healthy")
    
    # Discover tools
    print("🔍 Discovering MCP tools...")
    tools = await mcp_client.discover_tools()
    print(f"✅ Discovered {len(tools)} MCP tools")
    
    # Initialize LLM provider
    print("\n🤖 Initializing LLM Provider...")
    registry = get_global_registry()
    llm_provider = registry.get_provider()
    print(f"✅ Using {llm_provider.__class__.__name__}")
    
    # Create agent
    print("👤 Creating Spectrum Manager Agent...")
    agent = SpectrumManagerAgent(
        llm_provider=llm_provider,
        mcp_client=mcp_client,
        max_iterations=5
    )
    print("✅ Agent ready!\n")
    
    # Test queries
    test_queries = [
        "Can I use 151.5 MHz for a training exercise?",
        "What frequencies are available?",
        "Check interference on 225 MHz",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}: {query}")
        print("="*70)
        
        try:
            print("🤔 Agent is thinking...\n")
            response = await agent.run(query)
            print(f"Agent Response:\n{response}\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_chat_demo())

