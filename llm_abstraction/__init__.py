"""
LLM Provider Abstraction Layer.

Provides a common interface for different LLM providers (Anthropic, OpenAI)
allowing agents to switch between them seamlessly.
"""

from .provider import (
    LLMProvider,
    LLMConfig,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    LLMResponse
)
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .registry import (
    ProviderRegistry,
    get_global_registry,
    create_provider
)
from .cache import (
    LRUCache,
    get_global_cache,
    configure_global_cache,
    clear_global_cache
)

__all__ = [
    # Base classes
    "LLMProvider",
    "LLMConfig",
    "Message",
    "MessageRole",
    "ToolDefinition",
    "ToolCall",
    "LLMResponse",
    # Providers
    "AnthropicProvider",
    "OpenAIProvider",
    # Registry
    "ProviderRegistry",
    "get_global_registry",
    "create_provider",
    # Cache
    "LRUCache",
    "get_global_cache",
    "configure_global_cache",
    "clear_global_cache",
]
