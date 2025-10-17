"""
Anthropic Claude LLM Provider implementation.

Provides access to Claude models (Claude 3, Claude Sonnet, etc.)
"""

from typing import List, Optional, AsyncIterator, Dict, Any
import json
import anthropic
from anthropic.types import Message as AnthropicMessage, MessageStreamEvent

from .provider import (
    LLMProvider,
    LLMConfig,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    LLMResponse
)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude LLM provider.

    Supports Claude 3 models with function calling capabilities.
    """

    def __init__(self, api_key: str, config: LLMConfig):
        """Initialize the Anthropic provider."""
        super().__init__(api_key, config)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a completion using Claude.

        Args:
            messages: Conversation history
            tools: Available tools
            system: System prompt

        Returns:
            LLMResponse with content and tool calls
        """
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }

        # Add system prompt if provided
        if system:
            request_params["system"] = system

        # Add tools if provided
        if tools:
            request_params["tools"] = [self._format_tool_for_provider(tool) for tool in tools]

        # Make API call
        response: AnthropicMessage = await self.client.messages.create(**request_params)

        # Convert response to our format
        return self._convert_response(response)

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream a completion using Claude.

        Args:
            messages: Conversation history
            tools: Available tools
            system: System prompt

        Yields:
            Chunks of the response
        """
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }

        # Add system prompt if provided
        if system:
            request_params["system"] = system

        # Add tools if provided
        if tools:
            request_params["tools"] = [self._format_tool_for_provider(tool) for tool in tools]

        # Stream response
        async with self.client.messages.stream(**request_params) as stream:
            async for event in stream:
                if isinstance(event, MessageStreamEvent):
                    if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                        yield event.delta.text

    def supports_tools(self) -> bool:
        """Anthropic Claude 3+ supports function calling."""
        return True

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert our Message format to Anthropic's format.

        Args:
            messages: Our message format

        Returns:
            Anthropic message format
        """
        anthropic_messages = []

        for msg in messages:
            # Skip system messages (handled separately in Anthropic)
            if msg.role == MessageRole.SYSTEM:
                continue

            # Convert role
            role = "user" if msg.role == MessageRole.USER else "assistant"

            # Build message
            anthropic_msg: Dict[str, Any] = {
                "role": role,
                "content": msg.content
            }

            anthropic_messages.append(anthropic_msg)

        return anthropic_messages

    def _convert_response(self, response: AnthropicMessage) -> LLMResponse:
        """
        Convert Anthropic response to our format.

        Args:
            response: Anthropic API response

        Returns:
            Our LLMResponse format
        """
        # Extract text content
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                # Convert tool use to our format
                tool_call = ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                )
                tool_calls.append(tool_call)

        # Extract usage info
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage=usage,
            model=response.model
        )

    def _format_tool_for_provider(self, tool: ToolDefinition) -> Dict[str, Any]:
        """
        Format tool definition for Anthropic API.

        Args:
            tool: Our tool definition

        Returns:
            Anthropic-formatted tool definition
        """
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters
        }

    def get_max_context_length(self) -> int:
        """Get maximum context length for Claude models."""
        # Claude 3 models have 200K context window
        if "claude-3" in self.config.model.lower() or "sonnet" in self.config.model.lower():
            return 200000

        return 100000  # Default for older Claude models
