#!/usr/bin/env python3
"""
Simple test to verify LLM provider works.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_abstraction import get_global_registry, Message, MessageRole


async def test_llm():
    """Test the LLM provider."""
    
    print("Testing LLM Provider...")
    print("="*50)
    
    # Get LLM provider
    registry = get_global_registry()
    provider = registry.get_provider()
    
    print(f"Provider: {provider.__class__.__name__}")
    print(f"Model: {provider.model}")
    
    # Create a simple message
    messages = [
        Message(role=MessageRole.USER, content="What is 2+2?")
    ]
    
    print("\nSending request to LLM...")
    print("Message: What is 2+2?")
    print("-"*50)
    
    try:
        response = await provider.complete(
            messages=messages,
            tools=[],
            system="You are a helpful assistant."
        )
        
        print(f"Response: {response.content}")
        print("="*50)
        print("✅ LLM Provider works!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm())

