"""
OpenAI LLM Provider implementation.

Provides access to GPT models (GPT-4, GPT-3.5, etc.)
"""

from typing import List, Optional, AsyncIterator, Dict, Any
import json
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .provider import (
    LLMProvider,
    LLMConfig,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    LLMResponse
)


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT LLM provider.

    Supports GPT-4 and GPT-3.5 models with function calling.
    """

    def __init__(self, api_key: str, config: LLMConfig):
        """Initialize the OpenAI provider."""
        super().__init__(api_key, config)
        self.client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a completion using GPT.

        Args:
            messages: Conversation history
            tools: Available tools
            system: System prompt

        Returns:
            LLMResponse with content and tool calls
        """
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages, system)

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }

        # Add tools if provided
        if tools:
            request_params["tools"] = [self._format_tool_for_provider(tool) for tool in tools]
            request_params["tool_choice"] = "auto"

        # Make API call
        response: ChatCompletion = await self.client.chat.completions.create(**request_params)

        # Convert response to our format
        return self._convert_response(response)

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream a completion using GPT.

        Args:
            messages: Conversation history
            tools: Available tools
            system: System prompt

        Yields:
            Chunks of the response
        """
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages, system)

        # Prepare request parameters
        request_params: Dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": True,
        }

        # Add tools if provided
        if tools:
            request_params["tools"] = [self._format_tool_for_provider(tool) for tool in tools]
            request_params["tool_choice"] = "auto"

        # Stream response
        stream = await self.client.chat.completions.create(**request_params)

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

    def supports_tools(self) -> bool:
        """OpenAI GPT-4 and GPT-3.5-turbo support function calling."""
        return True

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    def _convert_messages(
        self,
        messages: List[Message],
        system: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert our Message format to OpenAI's format.

        Args:
            messages: Our message format
            system: System prompt to prepend

        Returns:
            OpenAI message format
        """
        openai_messages = []

        # Add system message first if provided
        if system:
            openai_messages.append({
                "role": "system",
                "content": system
            })

        for msg in messages:
            # Convert role
            role_map = {
                MessageRole.SYSTEM: "system",
                MessageRole.USER: "user",
                MessageRole.ASSISTANT: "assistant",
                MessageRole.TOOL: "tool"
            }
            role = role_map.get(msg.role, "user")

            # Build message
            openai_msg: Dict[str, Any] = {
                "role": role,
                "content": msg.content
            }

            # Add tool-specific fields if present
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            if msg.name:
                openai_msg["name"] = msg.name

            openai_messages.append(openai_msg)

        return openai_messages

    def _convert_response(self, response: ChatCompletion) -> LLMResponse:
        """
        Convert OpenAI response to our format.

        Args:
            response: OpenAI API response

        Returns:
            Our LLMResponse format
        """
        choice = response.choices[0]
        message = choice.message

        # Extract content
        content = message.content or ""

        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_call = ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                )
                tool_calls.append(tool_call)

        # Extract usage info
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage,
            model=response.model
        )

    def _format_tool_for_provider(self, tool: ToolDefinition) -> Dict[str, Any]:
        """
        Format tool definition for OpenAI API.

        Args:
            tool: Our tool definition

        Returns:
            OpenAI-formatted tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }

    def get_max_context_length(self) -> int:
        """Get maximum context length for GPT models."""
        model_limits = {
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
        }

        for model_prefix, limit in model_limits.items():
            if model_prefix in self.config.model.lower():
                return limit

        return 8192  # Conservative default
