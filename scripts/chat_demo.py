#!/usr/bin/env python3
"""
Interactive Chat Demo with LLM Integration.

A command-line chat interface that demonstrates:
- Real-time agent interaction with LLM
- Spectrum management queries
- Multi-turn conversations
- Tool calling and MCP integration

Usage:
    python scripts/chat_demo.py [--provider anthropic|openai]
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_abstraction import get_global_registry
from mcp_client import MCPClient
from agents import SpectrumManagerAgent

logger = structlog.get_logger()


class ChatDemo:
    """Interactive chat demo with LLM agent."""
    
    def __init__(self, provider: str = "anthropic"):
        """Initialize the chat demo."""
        self.provider = provider
        self.agent = None
        self.mcp_client = None
        self.llm_provider = None
        self.conversation_history = []
    
    async def initialize(self) -> bool:
        """Initialize agent and MCP client."""
        try:
            server_url = os.getenv("EMBM_SERVER_URL", "http://localhost:8000")
            
            print(f"\n🔌 Connecting to MCP Server: {server_url}")
            self.mcp_client = MCPClient(server_url)
            
            # Check server health
            is_healthy = await self.mcp_client.health_check()
            if not is_healthy:
                print("❌ MCP server is not responding!")
                return False
            print("✅ MCP server is healthy")
            
            # Discover tools
            tools = await self.mcp_client.discover_tools()
            print(f"✅ Discovered {len(tools)} MCP tools")
            
            # Initialize LLM provider
            print(f"\n🤖 Initializing LLM Provider: {self.provider}")
            registry = get_global_registry()
            self.llm_provider = registry.get_provider()
            print(f"✅ Using {self.llm_provider.get_provider_name()}")
            print(f"   Model: {self.llm_provider.config.model}")
            
            # Create agent
            print("\n👤 Creating Spectrum Manager Agent...")
            self.agent = SpectrumManagerAgent(
                llm_provider=self.llm_provider,
                mcp_client=self.mcp_client,
                max_iterations=10
            )
            print("✅ Agent ready!")
            
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            logger.error("init_error", error=str(e))
            return False
    
    async def process_input(self, user_input: str) -> str:
        """Process user input through the agent."""
        try:
            # Check server health
            is_healthy = await self.mcp_client.health_check()
            if not is_healthy:
                return "⚠️ MCP server is not responding."
            
            # Run agent
            response = await self.agent.run(user_input)
            return response
        except Exception as e:
            logger.error("process_error", error=str(e))
            return f"Error: {str(e)}"
    
    async def run(self):
        """Run the interactive chat loop."""
        print("\n" + "="*70)
        print("EMBM-J DS Spectrum Management Chat Demo")
        print("="*70)
        print("\nType 'help' for commands, 'exit' to quit\n")
        
        # Welcome message
        welcome = "Hello! I'm the EMBM-J DS Spectrum Manager Agent. I can help you with frequency allocation, spectrum planning, and electromagnetic operations. What would you like to know?"
        print(f"Agent: {welcome}\n")
        self.conversation_history.append(("assistant", welcome))
        
        # Chat loop
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    print("\nGoodbye! 👋")
                    break
                
                if user_input.lower() == "help":
                    self.show_help()
                    continue
                
                if user_input.lower() == "history":
                    self.show_history()
                    continue
                
                # Process input
                print("\n🤔 Agent is thinking...\n")
                response = await self.process_input(user_input)
                
                print(f"Agent: {response}\n")
                self.conversation_history.append(("user", user_input))
                self.conversation_history.append(("assistant", response))
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {str(e)}\n")
                logger.error("chat_error", error=str(e))
    
    def show_help(self):
        """Show help message."""
        print("""
Commands:
  help     - Show this help message
  history  - Show conversation history
  exit     - Exit the chat

Example queries:
  - "Can I use 151.5 MHz for a training exercise?"
  - "What frequencies are available in my area?"
  - "Check for interference on 225 MHz"
  - "Allocate frequency for ISR collection"
        """)
    
    def show_history(self):
        """Show conversation history."""
        print("\n" + "="*70)
        print("Conversation History")
        print("="*70 + "\n")
        
        for role, message in self.conversation_history:
            prefix = "You" if role == "user" else "Agent"
            print(f"{prefix}: {message}\n")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive chat demo with LLM agent"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider to use"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    
    # Run demo
    demo = ChatDemo(provider=args.provider)
    
    if await demo.initialize():
        await demo.run()
    else:
        print("Failed to initialize chat demo")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

