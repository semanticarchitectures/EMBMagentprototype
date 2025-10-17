"""
MCP Client Library.

Provides client functionality for agents to interact with MCP servers.
"""

from .client import MCPClient, MCPTool, MCPError

__all__ = ["MCPClient", "MCPTool", "MCPError"]
