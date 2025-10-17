"""
LLM Provider Registry.

Manages multiple LLM providers and allows easy switching between them.
"""

from typing import Dict, Optional
import os
from dotenv import load_dotenv

from .provider import LLMProvider, LLMConfig
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider


class ProviderRegistry:
    """
    Registry for managing LLM providers.

    Handles provider initialization, caching, and retrieval.
    """

    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider: Optional[str] = None

        # Load environment variables
        load_dotenv()

    def register_provider(
        self,
        name: str,
        provider: LLMProvider,
        set_as_default: bool = False
    ) -> None:
        """
        Register a provider.

        Args:
            name: Unique name for the provider
            provider: Provider instance
            set_as_default: Whether to set as default provider
        """
        self._providers[name] = provider

        if set_as_default or self._default_provider is None:
            self._default_provider = name

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """
        Get a provider by name.

        Args:
            name: Provider name (uses default if None)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_name = name or self._default_provider

        if provider_name is None:
            raise ValueError("No default provider set and no name provided")

        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        return self._providers[provider_name]

    def create_anthropic_provider(
        self,
        name: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        set_as_default: bool = False
    ) -> AnthropicProvider:
        """
        Create and register an Anthropic provider.

        Args:
            name: Provider name
            model: Model to use
            api_key: API key (uses env var if None)
            config: Configuration (uses defaults if None)
            set_as_default: Whether to set as default

        Returns:
            Created provider
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")

        # Create config if not provided
        if config is None:
            config = LLMConfig(model=model)
        else:
            config.model = model

        # Create provider
        provider = AnthropicProvider(api_key, config)

        # Register it
        self.register_provider(name, provider, set_as_default)

        return provider

    def create_openai_provider(
        self,
        name: str = "openai",
        model: str = "gpt-4-turbo",
        api_key: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        set_as_default: bool = False
    ) -> OpenAIProvider:
        """
        Create and register an OpenAI provider.

        Args:
            name: Provider name
            model: Model to use
            api_key: API key (uses env var if None)
            config: Configuration (uses defaults if None)
            set_as_default: Whether to set as default

        Returns:
            Created provider
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

        # Create config if not provided
        if config is None:
            config = LLMConfig(model=model)
        else:
            config.model = model

        # Create provider
        provider = OpenAIProvider(api_key, config)

        # Register it
        self.register_provider(name, provider, set_as_default)

        return provider

    def list_providers(self) -> Dict[str, str]:
        """
        List all registered providers.

        Returns:
            Dict mapping provider name to provider type
        """
        return {
            name: provider.get_provider_name()
            for name, provider in self._providers.items()
        }

    def get_default_provider_name(self) -> Optional[str]:
        """Get the name of the default provider."""
        return self._default_provider

    def set_default_provider(self, name: str) -> None:
        """
        Set the default provider.

        Args:
            name: Provider name

        Raises:
            ValueError: If provider not found
        """
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found")

        self._default_provider = name


# Global registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_global_registry() -> ProviderRegistry:
    """
    Get the global provider registry.

    Returns:
        Global registry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ProviderRegistry()

        # Auto-register providers if API keys are available
        try:
            _global_registry.create_anthropic_provider(set_as_default=True)
        except ValueError:
            pass  # API key not available

        try:
            _global_registry.create_openai_provider()
        except ValueError:
            pass  # API key not available

    return _global_registry


def create_provider(
    provider_type: str,
    model: str,
    **kwargs
) -> LLMProvider:
    """
    Convenience function to create a provider.

    Args:
        provider_type: "anthropic" or "openai"
        model: Model name
        **kwargs: Additional arguments

    Returns:
        Created provider
    """
    registry = get_global_registry()

    if provider_type.lower() == "anthropic":
        return registry.create_anthropic_provider(model=model, **kwargs)
    elif provider_type.lower() == "openai":
        return registry.create_openai_provider(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
