"""
Agent Registry Module

Manages the registration and instantiation of agents using dependency injection.
Follows SOLID principles for clean, maintainable, and extensible code.

Design Principles:
- Single Responsibility: Only manages agent lifecycle
- Open/Closed: Easy to add new agents via configuration
- Liskov Substitution: All agents follow the same interface
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on abstractions (config) not implementations
"""

from abc import ABC, abstractmethod
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Protocol
from functools import partial
from agents import Agent

from asdrp.util.config_loader import AgentConfiguration, ConfigurationError


class AgentFactory(Protocol):
    """
    Protocol defining the interface for agent factory functions.

    Any callable that takes no arguments and returns an Agent
    satisfies this protocol. This follows the Dependency Inversion
    Principle - we depend on the interface, not the implementation.
    """

    def __call__(self) -> Agent:
        """Create and return an Agent instance."""
        ...


class AgentMetadata:
    """
    Metadata about a registered agent.

    Encapsulates all the information needed to describe and instantiate
    an agent. Follows the Information Expert pattern.

    Attributes:
        agent_id: Unique identifier for the agent
        name: Human-readable name
        description: Detailed description of capabilities
        factory: Callable that creates the agent
        capabilities: List of agent capabilities
        keywords: Keywords for routing decisions
        examples: Example queries this agent can handle
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        factory: AgentFactory,
        capabilities: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
    ):
        """
        Initialize agent metadata.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Detailed description
            factory: Function to create the agent
            capabilities: List of capabilities
            keywords: Keywords for matching
            examples: Example queries
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.factory = factory
        self.capabilities = capabilities or []
        self.keywords = keywords or []
        self.examples = examples or []

    def create_agent(self) -> Agent:
        """
        Create an instance of the agent.

        Returns:
            Newly created Agent instance

        Raises:
            Exception: If agent creation fails
        """
        return self.factory()

    def get_routing_description(self) -> str:
        """
        Get a formatted description for routing decisions.

        Returns:
            Formatted string describing the agent for LLM routing
        """
        lines = [
            f"- **{self.name}** (ID: {self.agent_id})",
            f"  {self.description}",
        ]

        if self.capabilities:
            lines.append(f"  Capabilities: {', '.join(self.capabilities[:5])}")

        if self.keywords:
            lines.append(f"  Keywords: {', '.join(self.keywords[:10])}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"AgentMetadata(id={self.agent_id}, name={self.name})"


class IAgentRegistry(ABC):
    """
    Interface for agent registries.

    Defines the contract that all agent registries must follow.
    This enables dependency injection and makes testing easier.
    """

    @abstractmethod
    def register(self, metadata: AgentMetadata) -> None:
        """Register an agent."""
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent instance by ID."""
        pass

    @abstractmethod
    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID."""
        pass

    @abstractmethod
    def get_all_metadata(self) -> List[AgentMetadata]:
        """Get metadata for all registered agents."""
        pass

    @abstractmethod
    def get_agent_ids(self) -> List[str]:
        """Get list of all registered agent IDs."""
        pass


class AgentRegistry(IAgentRegistry):
    """
    Central registry for managing agents.

    This class implements the Registry pattern, providing a centralized
    place to register and retrieve agents. It supports lazy instantiation -
    agents are only created when requested.

    Thread-safety note: This implementation is NOT thread-safe. For
    concurrent use, wrap in appropriate locking mechanisms.

    Example:
        >>> registry = AgentRegistry()
        >>> metadata = AgentMetadata(
        ...     agent_id="finance",
        ...     name="Finance Agent",
        ...     description="Handles financial queries",
        ...     factory=create_finance_agent
        ... )
        >>> registry.register(metadata)
        >>> agent = registry.get_agent("finance")
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._metadata: Dict[str, AgentMetadata] = {}
        self._agents: Dict[str, Agent] = {}  # Cache of instantiated agents

    def register(self, metadata: AgentMetadata) -> None:
        """
        Register an agent with its metadata.

        Args:
            metadata: AgentMetadata object describing the agent

        Raises:
            ValueError: If an agent with this ID is already registered
        """
        if metadata.agent_id in self._metadata:
            raise ValueError(
                f"Agent with ID '{metadata.agent_id}' is already registered"
            )

        self._metadata[metadata.agent_id] = metadata

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent instance by ID.

        Implements lazy instantiation - agents are only created when
        first requested, then cached for subsequent requests.

        Args:
            agent_id: Unique identifier of the agent

        Returns:
            Agent instance, or None if not found

        Raises:
            Exception: If agent creation fails
        """
        if agent_id not in self._metadata:
            return None

        # Return cached instance if available
        if agent_id in self._agents:
            return self._agents[agent_id]

        # Create and cache the agent
        metadata = self._metadata[agent_id]
        agent = metadata.create_agent()
        self._agents[agent_id] = agent

        return agent

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get agent metadata by ID.

        Args:
            agent_id: Unique identifier of the agent

        Returns:
            AgentMetadata object, or None if not found
        """
        return self._metadata.get(agent_id)

    def get_all_metadata(self) -> List[AgentMetadata]:
        """
        Get metadata for all registered agents.

        Returns:
            List of AgentMetadata objects
        """
        return list(self._metadata.values())

    def get_agent_ids(self) -> List[str]:
        """
        Get list of all registered agent IDs.

        Returns:
            List of agent ID strings
        """
        return list(self._metadata.keys())

    def clear_cache(self) -> None:
        """
        Clear the cache of instantiated agents.

        Useful for testing or when agents need to be recreated.
        """
        self._agents.clear()

    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_id in self._metadata:
            del self._metadata[agent_id]
            self._agents.pop(agent_id, None)
            return True
        return False

    def __len__(self) -> int:
        """Return the number of registered agents."""
        return len(self._metadata)

    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._metadata


class AgentRegistryBuilder:
    """
    Builder for constructing an AgentRegistry from configuration.

    This class implements the Builder pattern, separating the construction
    of the registry from its representation. It handles the complex process
    of loading modules and creating factory functions.

    Example:
        >>> builder = AgentRegistryBuilder(config)
        >>> registry = builder.build()
    """

    def __init__(self, config: AgentConfiguration):
        """
        Initialize the builder with configuration.

        Args:
            config: AgentConfiguration object
        """
        self.config = config
        self.registry = AgentRegistry()

    def build(self) -> AgentRegistry:
        """
        Build the agent registry from configuration.

        Returns:
            Populated AgentRegistry

        Raises:
            ConfigurationError: If agent loading fails
        """
        agents_config = self.config.get_agents_config()

        for agent_config in agents_config:
            try:
                metadata = self._create_metadata(agent_config)
                self.registry.register(metadata)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to register agent '{agent_config.get('id', 'unknown')}': {e}"
                )

        return self.registry

    def _create_metadata(self, agent_config: Dict[str, Any]) -> AgentMetadata:
        """
        Create AgentMetadata from configuration.

        Args:
            agent_config: Agent configuration dictionary

        Returns:
            AgentMetadata object

        Raises:
            ImportError: If module or factory cannot be imported
        """
        # Import the module and get the factory function
        module_name = agent_config["module"]
        factory_name = agent_config["factory"]

        module = import_module(module_name)
        base_factory = getattr(module, factory_name)

        if not callable(base_factory):
            raise ConfigurationError(
                f"Factory '{factory_name}' in module '{module_name}' is not callable"
            )

        # Extract configuration parameters
        # These are injected from agents.yaml following Dependency Inversion Principle
        kwargs = {}
        
        # Model configuration
        if agent_config.get("model") is not None:
            kwargs["model"] = agent_config["model"]
        if agent_config.get("temperature") is not None:
            kwargs["temperature"] = agent_config["temperature"]
        
        # Instructions from config (key feature - no hardcoded instructions)
        if agent_config.get("instructions") is not None:
            kwargs["instructions"] = agent_config["instructions"]
        
        # Create a partial function with all config parameters
        if kwargs:
            factory = partial(base_factory, **kwargs)
        else:
            factory = base_factory

        return AgentMetadata(
            agent_id=agent_config["id"],
            name=agent_config["name"],
            description=agent_config["description"],
            factory=factory,
            capabilities=agent_config.get("capabilities", []),
            keywords=agent_config.get("keywords", []),
            examples=agent_config.get("examples", []),
        )


def create_agent_registry(config: AgentConfiguration) -> AgentRegistry:
    """
    Factory function to create an AgentRegistry from configuration.

    This is the primary entry point for creating a registry. It follows
    the Facade pattern to simplify the build process.

    Args:
        config: AgentConfiguration object

    Returns:
        Populated AgentRegistry

    Raises:
        ConfigurationError: If registry creation fails

    Example:
        >>> from asdrp.util.config_loader import load_agent_configuration
        >>> config = load_agent_configuration("config/agents.yaml")
        >>> registry = create_agent_registry(config)
        >>> finance_agent = registry.get_agent("finance")
    """
    builder = AgentRegistryBuilder(config)
    return builder.build()


# Example usage and testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from asdrp.util.config_loader import load_agent_configuration

    # Load configuration
    config_path = Path(__file__).parent.parent.parent / "config" / "agents.yaml"

    try:
        print(f"Loading configuration from: {config_path}")
        config = load_agent_configuration(config_path)

        print("\nBuilding agent registry...")
        registry = create_agent_registry(config)

        print(f"\n✓ Registry created successfully!")
        print(f"  Registered agents: {registry.get_agent_ids()}")
        print(f"  Total agents: {len(registry)}")

        print("\n📋 Agent Metadata:")
        for metadata in registry.get_all_metadata():
            print(f"\n{metadata.get_routing_description()}")

        # Test lazy instantiation
        print("\n🧪 Testing lazy instantiation...")
        print("  Cache before: ", list(registry._agents.keys()))

        finance_agent = registry.get_agent("finance")
        print(f"  Created: {finance_agent.name}")
        print("  Cache after: ", list(registry._agents.keys()))

        # Test cache hit
        finance_agent_2 = registry.get_agent("finance")
        print(f"  Same instance: {finance_agent is finance_agent_2}")

    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
