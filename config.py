"""
Configuration Management Module.

PHASE 4 ENHANCEMENT: Centralized configuration with YAML support.

Provides type-safe access to system configuration loaded from config.yaml.
Environment variables can override configuration values.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import structlog


logger = structlog.get_logger(__name__)


@dataclass
class MCPServerConfig:
    """MCP Server configuration."""
    host: str = "localhost"
    port: int = 8000
    url: str = "http://localhost:8000"
    health_check_timeout: int = 10

    def get_url(self) -> str:
        """Get MCP server URL, checking environment variable first."""
        return os.getenv("EMBM_SERVER_URL", self.url)


@dataclass
class AgentConfig:
    """Agent configuration."""
    max_iterations: int = 5
    timeout_seconds: int = 120
    default_provider: str = "anthropic"

    # Individual agent settings
    spectrum_manager: Dict[str, Any] = field(default_factory=dict)
    isr_manager: Dict[str, Any] = field(default_factory=dict)
    ew_planner: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMCacheConfig:
    """LLM cache configuration."""
    enabled: bool = True
    max_size: int = 100
    ttl_seconds: int = 3600


@dataclass
class LLMProviderConfig:
    """LLM provider configuration."""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.0


@dataclass
class LLMConfig:
    """LLM configuration."""
    cache: LLMCacheConfig = field(default_factory=LLMCacheConfig)
    anthropic: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    openai: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    google: LLMProviderConfig = field(default_factory=LLMProviderConfig)


@dataclass
class MessageBrokerConfig:
    """Message broker configuration."""
    max_history: int = 1000
    request_timeout: float = 5.0
    enable_persistence: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"
    max_bytes: int = 10485760  # 10 MB
    backup_count: int = 5
    files: Dict[str, str] = field(default_factory=lambda: {
        "app": "embm_app.log",
        "mcp_server": "embm_mcp_server.log",
        "agents": "embm_agents.log",
        "tests": "embm_tests.log"
    })
    format: str = "json"


@dataclass
class RestrictedZone:
    """Restricted zone configuration."""
    name: str
    center: Dict[str, float]
    radius_km: float
    restricted_actions: List[str]
    priority: str


@dataclass
class FrequencyRestriction:
    """Frequency restriction configuration."""
    name: str
    min_mhz: float
    max_mhz: float
    restriction: str


@dataclass
class ROEConfig:
    """Rules of Engagement configuration."""
    restricted_zones: List[RestrictedZone] = field(default_factory=list)
    frequency_restrictions: List[FrequencyRestriction] = field(default_factory=list)
    power_limits_dbm: Dict[str, int] = field(default_factory=dict)


@dataclass
class DeconflictionConfig:
    """Deconfliction configuration."""
    min_frequency_separation_mhz: float = 10.0
    min_geographic_separation_km: float = 1.0
    min_time_separation_minutes: int = 5
    priority_order: List[str] = field(default_factory=lambda: [
        "FLASH", "IMMEDIATE", "PRIORITY", "ROUTINE"
    ])


@dataclass
class WebSocketConfig:
    """WebSocket configuration."""
    enabled: bool = True
    path: str = "/ws"
    heartbeat_interval: int = 30


@dataclass
class UIConfig:
    """UI configuration."""
    refresh_interval_ms: int = 1000
    max_history_items: int = 100
    theme: str = "dark"


@dataclass
class WebDashboardConfig:
    """Web dashboard configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    ui: UIConfig = field(default_factory=UIConfig)


@dataclass
class PrometheusConfig:
    """Prometheus configuration."""
    enabled: bool = True
    port: int = 9090
    path: str = "/metrics"


@dataclass
class MetricsConfig:
    """Metrics configuration."""
    enabled: bool = True
    prometheus: PrometheusConfig = field(default_factory=PrometheusConfig)
    collect: List[str] = field(default_factory=list)


@dataclass
class DevelopmentConfig:
    """Development configuration."""
    debug_mode: bool = False
    mock_llm_responses: bool = False
    sample_data_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    async_agent_execution: bool = True
    connection_pool_size: int = 10
    request_timeout_seconds: int = 30


@dataclass
class Config:
    """
    Main configuration class.

    PHASE 4 ENHANCEMENT: Centralized configuration management.

    Loads configuration from config.yaml and provides type-safe access
    to all system settings. Environment variables override config file values.
    """
    mcp_server: MCPServerConfig = field(default_factory=MCPServerConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    message_broker: MessageBrokerConfig = field(default_factory=MessageBrokerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    roe: ROEConfig = field(default_factory=ROEConfig)
    deconfliction: DeconflictionConfig = field(default_factory=DeconflictionConfig)
    web_dashboard: WebDashboardConfig = field(default_factory=WebDashboardConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str = "config.yaml") -> "Config":
        """
        Load configuration from YAML file.

        Args:
            yaml_path: Path to config.yaml file

        Returns:
            Config object with loaded settings
        """
        config_file = Path(yaml_path)

        if not config_file.exists():
            logger.warning(
                "config_file_not_found",
                path=str(config_file),
                message="Using default configuration"
            )
            return cls()

        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            logger.info(
                "config_loaded",
                path=str(config_file),
                sections=list(config_data.keys())
            )

            return cls._from_dict(config_data)

        except Exception as e:
            logger.error(
                "config_load_error",
                path=str(config_file),
                error=str(e),
                message="Using default configuration"
            )
            return cls()

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()

        # MCP Server
        if "mcp_server" in data:
            config.mcp_server = MCPServerConfig(**data["mcp_server"])

        # Agents
        if "agents" in data:
            config.agents = AgentConfig(**data["agents"])

        # LLM
        if "llm" in data:
            llm_data = data["llm"]
            config.llm = LLMConfig(
                cache=LLMCacheConfig(**llm_data.get("cache", {})),
                anthropic=LLMProviderConfig(**llm_data.get("anthropic", {})),
                openai=LLMProviderConfig(**llm_data.get("openai", {})),
                google=LLMProviderConfig(**llm_data.get("google", {}))
            )

        # Message Broker
        if "message_broker" in data:
            config.message_broker = MessageBrokerConfig(**data["message_broker"])

        # Logging
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])

        # ROE
        if "roe" in data:
            roe_data = data["roe"]
            config.roe = ROEConfig(
                restricted_zones=[
                    RestrictedZone(**zone)
                    for zone in roe_data.get("restricted_zones", [])
                ],
                frequency_restrictions=[
                    FrequencyRestriction(**freq)
                    for freq in roe_data.get("frequency_restrictions", [])
                ],
                power_limits_dbm=roe_data.get("power_limits_dbm", {})
            )

        # Deconfliction
        if "deconfliction" in data:
            config.deconfliction = DeconflictionConfig(**data["deconfliction"])

        # Web Dashboard
        if "web_dashboard" in data:
            dash_data = data["web_dashboard"]
            config.web_dashboard = WebDashboardConfig(
                enabled=dash_data.get("enabled", True),
                host=dash_data.get("host", "0.0.0.0"),
                port=dash_data.get("port", 8080),
                websocket=WebSocketConfig(**dash_data.get("websocket", {})),
                ui=UIConfig(**dash_data.get("ui", {}))
            )

        # Metrics
        if "metrics" in data:
            metrics_data = data["metrics"]
            config.metrics = MetricsConfig(
                enabled=metrics_data.get("enabled", True),
                prometheus=PrometheusConfig(**metrics_data.get("prometheus", {})),
                collect=metrics_data.get("collect", [])
            )

        # Development
        if "development" in data:
            config.development = DevelopmentConfig(**data["development"])

        # Performance
        if "performance" in data:
            config.performance = PerformanceConfig(**data["performance"])

        return config

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of agent (spectrum_manager, isr_manager, ew_planner)

        Returns:
            Agent-specific configuration dictionary
        """
        agent_configs = {
            "spectrum_manager": self.agents.spectrum_manager,
            "isr_manager": self.agents.isr_manager,
            "ew_planner": self.agents.ew_planner
        }

        config = agent_configs.get(agent_name, {})

        # Merge with defaults
        return {
            "max_iterations": config.get("max_iterations", self.agents.max_iterations),
            "role": config.get("role", "Agent"),
            "provider": self.agents.default_provider
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.

    Loads configuration from config.yaml on first call.
    Subsequent calls return cached instance.

    Returns:
        Config object
    """
    global _config

    if _config is None:
        _config = Config.from_yaml()

    return _config


def reload_config() -> Config:
    """
    Reload configuration from config.yaml.

    Forces reload of configuration file, discarding cached instance.

    Returns:
        Newly loaded Config object
    """
    global _config
    _config = Config.from_yaml()
    return _config


# Example usage
if __name__ == "__main__":
    # Test configuration loading
    config = get_config()

    print("=== EMBM-J DS Configuration ===")
    print()
    print(f"MCP Server: {config.mcp_server.get_url()}")
    print(f"Agent Max Iterations: {config.agents.max_iterations}")
    print(f"LLM Cache Enabled: {config.llm.cache.enabled}")
    print(f"LLM Cache Size: {config.llm.cache.max_size}")
    print(f"Message Broker Max History: {config.message_broker.max_history}")
    print(f"Log Level: {config.logging.level}")
    print(f"Web Dashboard Enabled: {config.web_dashboard.enabled}")
    print(f"Web Dashboard Port: {config.web_dashboard.port}")
    print(f"Async Agent Execution: {config.performance.async_agent_execution}")
    print()

    # Test agent-specific config
    print("Spectrum Manager Config:")
    print(config.get_agent_config("spectrum_manager"))
    print()

    # Test ROE config
    print(f"Restricted Zones: {len(config.roe.restricted_zones)}")
    for zone in config.roe.restricted_zones:
        print(f"  - {zone.name}: {zone.center} ({zone.radius_km} km)")
    print()

    # Test deconfliction config
    print(f"Min Frequency Separation: {config.deconfliction.min_frequency_separation_mhz} MHz")
    print(f"Priority Order: {config.deconfliction.priority_order}")
