"""
Configuration Loader Module

Provides utilities for loading and parsing YAML configuration files.
Follows the Single Responsibility Principle - handles only configuration loading.

Design Principles:
- Single Responsibility: Only loads and validates configuration
- Dependency Inversion: Returns data structures, doesn't create agents
- Open/Closed: Easy to extend with new config types
- Interface Segregation: Focused interfaces for specific config types
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ConfigLoader:
    """
    Loads and validates YAML configuration files.

    This class is responsible solely for reading configuration files
    and ensuring they have the expected structure. It does NOT create
    agents or instantiate objects - that's the job of other classes.

    Examples:
        >>> loader = ConfigLoader("config/agents.yaml")
        >>> config = loader.load()
        >>> agents_config = config.get_agents_config()
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            ConfigurationError: If the file doesn't exist
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )

        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> "AgentConfiguration":
        """
        Load the configuration file.

        Returns:
            AgentConfiguration object containing the parsed config

        Raises:
            ConfigurationError: If the file cannot be parsed or is invalid
        """
        try:
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f)

            if not self._config:
                raise ConfigurationError("Configuration file is empty")

            return AgentConfiguration(self._config)

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")


class AgentConfiguration:
    """
    Encapsulates agent configuration data.

    Provides a clean interface to access configuration sections without
    exposing the raw dictionary structure. This follows the Facade pattern.

    Attributes:
        _config: Raw configuration dictionary
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with parsed configuration.

        Args:
            config: Dictionary containing the configuration
        """
        self._config = config
        self._validate()

    def _validate(self) -> None:
        """
        Validate the configuration structure.

        Raises:
            ConfigurationError: If required fields are missing
        """
        if "agents" not in self._config:
            raise ConfigurationError("Configuration missing 'agents' section")

        if not isinstance(self._config["agents"], list):
            raise ConfigurationError("'agents' must be a list")

        if len(self._config["agents"]) == 0:
            raise ConfigurationError("'agents' list is empty")

        # Validate each agent entry
        for i, agent in enumerate(self._config["agents"]):
            self._validate_agent_entry(agent, i)

    def _validate_agent_entry(self, agent: Dict[str, Any], index: int) -> None:
        """
        Validate a single agent configuration entry.

        Args:
            agent: Agent configuration dictionary
            index: Index in the agents list (for error messages)

        Raises:
            ConfigurationError: If required fields are missing
        """
        required_fields = ["id", "name", "module", "factory", "description"]
        for field in required_fields:
            if field not in agent:
                raise ConfigurationError(
                    f"Agent at index {index} missing required field: '{field}'"
                )

    def get_agents_config(self) -> List[Dict[str, Any]]:
        """
        Get the list of agent configurations.

        Returns:
            List of agent configuration dictionaries
        """
        return self._config["agents"]

    def get_router_config(self) -> Dict[str, Any]:
        """
        Get the router configuration.

        Returns:
            Router configuration dictionary, or empty dict if not present
        """
        return self._config.get("router", {})

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific agent configuration by ID.

        Args:
            agent_id: The agent's unique identifier

        Returns:
            Agent configuration dictionary, or None if not found
        """
        for agent in self._config["agents"]:
            if agent["id"] == agent_id:
                return agent
        return None

    def get_agent_ids(self) -> List[str]:
        """
        Get list of all agent IDs.

        Returns:
            List of agent ID strings
        """
        return [agent["id"] for agent in self._config["agents"]]

    @property
    def raw_config(self) -> Dict[str, Any]:
        """
        Get the raw configuration dictionary.

        Use sparingly - prefer the specific getter methods.

        Returns:
            Raw configuration dictionary
        """
        return self._config


def load_agent_configuration(config_path: str | Path) -> AgentConfiguration:
    """
    Convenience function to load agent configuration.

    This is the primary entry point for loading configuration. It follows
    the Facade pattern to simplify the loading process.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        AgentConfiguration object

    Raises:
        ConfigurationError: If loading or validation fails

    Example:
        >>> config = load_agent_configuration("config/agents.yaml")
        >>> agents = config.get_agents_config()
        >>> print(f"Found {len(agents)} agents")
    """
    loader = ConfigLoader(config_path)
    return loader.load()


# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        # Default to the expected location
        config_path = Path(__file__).parent.parent.parent / "config" / "agents.yaml"

    try:
        print(f"Loading configuration from: {config_path}")
        config = load_agent_configuration(config_path)

        print(f"\n✓ Configuration loaded successfully!")
        print(f"  Agent IDs: {config.get_agent_ids()}")

        print("\n📋 Agent Details:")
        for agent_config in config.get_agents_config():
            print(f"\n  • {agent_config['name']} (ID: {agent_config['id']})")
            print(f"    Module: {agent_config['module']}")
            print(f"    Factory: {agent_config['factory']}")
            print(f"    Description: {agent_config['description'][:80]}...")

        router_config = config.get_router_config()
        if router_config:
            print(f"\n🔀 Router Configuration:")
            print(f"  Name: {router_config.get('name', 'N/A')}")
            print(f"  Max Turns: {router_config.get('max_turns', 'N/A')}")
            print(f"  Default Agent: {router_config.get('default_agent', 'N/A')}")

    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)
