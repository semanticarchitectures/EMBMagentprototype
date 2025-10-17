"""
Base LLM Provider abstraction.

Provides a common interface for different LLM providers (Anthropic, OpenAI, etc.)
allowing agents to switch between providers seamlessly.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolDefinition:
    """Defines a tool that the LLM can call."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


@dataclass
class ToolCall:
    """Represents a tool call made by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    tool_calls: List[ToolCall] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    max_retries: int = 3


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Provides a common interface for different LLM providers,
    allowing seamless switching between Anthropic, OpenAI, etc.
    """

    def __init__(self, api_key: str, config: LLMConfig):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider
            config: Configuration for the LLM
        """
        self.api_key = api_key
        self.config = config

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: Conversation history
            tools: Available tools the LLM can call
            system: System prompt (if supported separately)

        Returns:
            LLMResponse with content and any tool calls
        """
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        system: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream a completion from the LLM.

        Args:
            messages: Conversation history
            tools: Available tools the LLM can call
            system: System prompt (if supported separately)

        Yields:
            Chunks of the response as they arrive
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this provider supports function/tool calling."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass

    def _format_tool_for_provider(self, tool: ToolDefinition) -> Dict[str, Any]:
        """
        Format a tool definition for the specific provider's API.

        Each provider may have different formatting requirements.
        Subclasses should override this if needed.

        Args:
            tool: Tool definition to format

        Returns:
            Formatted tool definition
        """
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }

    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        This is a rough approximation. Subclasses can override
        with provider-specific tokenizers.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def get_max_context_length(self) -> int:
        """
        Get maximum context length for this model.

        Returns:
            Maximum context length in tokens
        """
        # Default values, subclasses should override
        model_limits = {
            "claude-3": 200000,
            "claude-sonnet": 200000,
            "gpt-4": 128000,
            "gpt-3.5": 16385,
        }

        for key, limit in model_limits.items():
            if key in self.config.model.lower():
                return limit

        return 8192  # Conservative default
