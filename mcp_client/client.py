"""
MCP Client implementation.

Provides a client for agents to interact with MCP servers using JSON-RPC 2.0.
"""

from typing import Dict, Any, Optional, List
import httpx
import uuid
import structlog
from dataclasses import dataclass


logger = structlog.get_logger()


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPError(Exception):
    """Exception raised for MCP errors."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


class MCPClient:
    """
    Client for interacting with MCP servers.

    Implements JSON-RPC 2.0 protocol for tool calls.
    """

    def __init__(self, server_url: str, timeout: int = 60):
        """
        Initialize MCP client.

        Args:
            server_url: URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._tools: Optional[List[MCPTool]] = None

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool result

        Raises:
            MCPError: If the tool call fails
        """
        # Create JSON-RPC 2.0 request
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": parameters,
            "id": request_id
        }

        logger.info(
            "mcp_tool_call",
            tool=tool_name,
            params=parameters,
            request_id=request_id
        )

        try:
            # Send request
            response = await self._client.post(
                f"{self.server_url}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Check for errors
            if "error" in response_data:
                error = response_data["error"]
                logger.error(
                    "mcp_tool_error",
                    tool=tool_name,
                    error_code=error.get("code"),
                    error_message=error.get("message")
                )
                raise MCPError(
                    code=error.get("code", -1),
                    message=error.get("message", "Unknown error"),
                    data=error.get("data")
                )

            # Extract result
            result = response_data.get("result")

            logger.info(
                "mcp_tool_success",
                tool=tool_name,
                request_id=request_id
            )

            return result

        except httpx.HTTPError as e:
            logger.error("mcp_http_error", tool=tool_name, error=str(e))
            raise MCPError(
                code=-32603,
                message=f"HTTP error: {str(e)}"
            )

    async def discover_tools(self) -> List[MCPTool]:
        """
        Discover available tools from the MCP server.

        Returns:
            List of available tools

        Raises:
            MCPError: If discovery fails
        """
        logger.info("mcp_discovering_tools")

        try:
            response = await self._client.get(f"{self.server_url}/mcp/tools")
            response.raise_for_status()

            data = response.json()
            tools_data = data.get("tools", [])

            tools = [
                MCPTool(
                    name=tool["name"],
                    description=tool["description"],
                    input_schema=tool["input_schema"]
                )
                for tool in tools_data
            ]

            self._tools = tools

            logger.info("mcp_tools_discovered", count=len(tools))

            return tools

        except httpx.HTTPError as e:
            logger.error("mcp_discovery_error", error=str(e))
            raise MCPError(
                code=-32603,
                message=f"Failed to discover tools: {str(e)}"
            )

    async def get_tools(self) -> List[MCPTool]:
        """
        Get cached tools or discover them.

        Returns:
            List of available tools
        """
        if self._tools is None:
            await self.discover_tools()

        return self._tools

    async def health_check(self) -> bool:
        """
        Check if the MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get(f"{self.server_url}/health")
            response.raise_for_status()

            data = response.json()
            return data.get("status") == "healthy"

        except httpx.HTTPError:
            return False

    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        if self._tools is None:
            return None

        for tool in self._tools:
            if tool.name == name:
                return tool

        return None

    def format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Format tools for LLM provider.

        Returns:
            List of tool definitions in LLM format
        """
        if self._tools is None:
            return []

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
            for tool in self._tools
        ]
