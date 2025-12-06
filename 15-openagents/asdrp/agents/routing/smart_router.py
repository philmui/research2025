"""
SmartRouter Agent Implementation

Intelligent routing agent that analyzes queries and delegates to specialized agents.

Design Principles:
- Single Responsibility: Routes queries to appropriate agents
- Open/Closed: Easy to add new agents via configuration
- Liskov Substitution: All specialist agents follow Agent interface
- Interface Segregation: Clean interfaces for routing logic
- Dependency Inversion: Depends on abstractions (registry, config)

Architecture:
    User Query → SmartRouter → Analyze Query → Select Agent → Hand Off
                     ↑                                           ↓
                 Registry                             Specialist Agent
                     ↑                                           ↓
                 Config File                              Execute & Return
"""

from pathlib import Path
from typing import Optional
import asyncio

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from agents import Agent, Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.util.config_loader import load_agent_configuration, AgentConfiguration
from asdrp.util.agent_registry import create_agent_registry, AgentRegistry


class SmartRouterBuilder:
    """
    Builder for constructing a SmartRouter agent.

    This class implements the Builder pattern, handling the complex process
    of creating a router agent with all its specialist agent handoffs.

    The builder separates the construction logic from the router's
    representation, making it easy to modify how routers are built.

    Example:
        >>> builder = SmartRouterBuilder(config, registry)
        >>> router = builder.build()
    """

    def __init__(
        self,
        config: AgentConfiguration,
        registry: AgentRegistry
    ):
        """
        Initialize the builder.

        Args:
            config: Configuration containing router settings
            registry: Registry of available specialist agents
        """
        self.config = config
        self.registry = registry
        self.router_config = config.get_router_config()

    def build(self) -> Agent:
        """
        Build the SmartRouter agent.

        Returns:
            Configured Agent instance that routes to specialists

        Raises:
            ValueError: If configuration is invalid
        """
        # Get all specialist agents for handoffs
        specialist_agents = self._get_specialist_agents()

        # Build instructions with agent descriptions
        instructions = self._build_instructions()

        # Get router settings
        name = self.router_config.get("name", "SmartRouter")
        max_turns = self.router_config.get("max_turns", 10)

        # Create the router agent
        router = Agent(
            name=name,
            instructions=instructions,
            handoffs=specialist_agents,
            # No tools - router only delegates
            tools=[],
        )

        return router

    def _get_specialist_agents(self) -> list[Agent]:
        """
        Get instances of all specialist agents for handoffs.

        Returns:
            List of Agent instances

        Raises:
            ValueError: If no agents are registered
        """
        agent_ids = self.registry.get_agent_ids()

        if not agent_ids:
            raise ValueError("No specialist agents registered")

        # Get agent instances (lazy instantiation)
        specialists = []
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if agent:
                specialists.append(agent)

        return specialists

    def _build_instructions(self) -> str:
        """
        Build the router's instruction prompt.

        Dynamically includes descriptions of all available agents
        from the registry.

        Returns:
            Formatted instruction string
        """
        # Get the instruction template
        template = self.router_config.get(
            "instructions_template",
            self._get_default_template()
        )

        # Build agent descriptions section
        agent_descriptions = self._build_agent_descriptions()

        # Format the template
        instructions = template.format(
            agent_descriptions=agent_descriptions
        )

        return instructions

    def _build_agent_descriptions(self) -> str:
        """
        Build formatted descriptions of all available agents.

        Returns:
            Multi-line string describing each agent
        """
        descriptions = []

        for metadata in self.registry.get_all_metadata():
            descriptions.append(metadata.get_routing_description())

        return "\n\n".join(descriptions)

    def _get_default_template(self) -> str:
        """
        Get default instruction template if none in config.

        Returns:
            Default instruction template string
        """
        return (
            "You are an intelligent routing agent that analyzes user queries "
            "and delegates them to the most appropriate specialized agent.\n\n"
            "Available agents:\n"
            "{agent_descriptions}\n\n"
            "Analyze the query and hand off to the appropriate specialist. "
            "Do not try to answer the query yourself."
        )


class SmartRouter:
    """
    Facade for the SmartRouter system.

    This class provides a clean, simple interface for creating and using
    the router agent. It hides the complexity of configuration loading,
    registry management, and agent building.

    This follows the Facade pattern - simplifying a complex subsystem
    with a unified interface.

    Example:
        >>> router_system = SmartRouter.from_config("config/agents.yaml")
        >>> result = await router_system.route("What's AAPL stock price?")
        >>> print(result.final_output)
    """

    def __init__(
        self,
        router_agent: Agent,
        registry: AgentRegistry,
        config: AgentConfiguration
    ):
        """
        Initialize the router system.

        Args:
            router_agent: The configured router Agent
            registry: Agent registry
            config: Configuration object
        """
        self.router = router_agent
        self.registry = registry
        self.config = config

    @classmethod
    def from_config(cls, config_path: str | Path) -> "SmartRouter":
        """
        Create a SmartRouter system from configuration file.

        This is the primary factory method for creating routers.
        It handles all the setup complexity.

        Args:
            config_path: Path to agents.yaml configuration file

        Returns:
            Configured SmartRouter instance

        Raises:
            ConfigurationError: If configuration is invalid
            Exception: If router creation fails

        Example:
            >>> router = SmartRouter.from_config("config/agents.yaml")
        """
        # Load configuration
        config = load_agent_configuration(config_path)

        # Build agent registry
        registry = create_agent_registry(config)

        # Build router agent
        builder = SmartRouterBuilder(config, registry)
        router_agent = builder.build()

        return cls(router_agent, registry, config)

    async def route(
        self,
        query: str,
        session: Optional[SQLiteSession] = None
    ) -> any:
        """
        Route a query to the appropriate specialist agent.

        Args:
            query: User's query string
            session: Optional session for conversation continuity

        Returns:
            RunResult from the specialist agent

        Example:
            >>> result = await router.route("What's the weather?")
            >>> print(result.final_output)
        """
        if session is None:
            session = SQLiteSession(session_id="default")

        result = await Runner.run(
            self.router,
            input=query,
            session=session
        )

        return result

    def get_registry(self) -> AgentRegistry:
        """
        Get the underlying agent registry.

        Returns:
            AgentRegistry instance
        """
        return self.registry

    def get_specialist_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get a specific specialist agent directly.

        Useful for testing or direct access to specialists.

        Args:
            agent_id: ID of the agent to retrieve

        Returns:
            Agent instance, or None if not found
        """
        return self.registry.get_agent(agent_id)

    def list_available_agents(self) -> list[str]:
        """
        Get list of available specialist agent IDs.

        Returns:
            List of agent ID strings
        """
        return self.registry.get_agent_ids()


def create_smart_router(config_path: Optional[str | Path] = None) -> SmartRouter:
    """
    Factory function to create a SmartRouter.

    This is the simplest way to create a router - just provide a config path
    (or use the default location).

    Args:
        config_path: Path to configuration file. If None, uses default location.

    Returns:
        Configured SmartRouter instance

    Raises:
        ConfigurationError: If configuration is invalid
        Exception: If router creation fails

    Example:
        >>> router = create_smart_router()
        >>> result = await router.route("Tell me about Python")
    """
    if config_path is None:
        # Default to config/agents.yaml in project root
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "agents.yaml"

    return SmartRouter.from_config(config_path)


# ------------------------------------------------------------
# Main tests and interactive usage
# ------------------------------------------------------------

async def main():
    """
    Interactive test of the SmartRouter system.

    Demonstrates:
    - Router creation from config
    - Query routing to specialists
    - Session continuity
    - Interactive usage
    """
    print("=" * 60)
    print("SmartRouter Interactive Test")
    print("=" * 60)

    # Create router from configuration
    print("\n📋 Loading configuration and creating router...")
    try:
        router = create_smart_router()
        print(f"✓ Router created successfully!")
        print(f"  Available agents: {router.list_available_agents()}")
    except Exception as e:
        print(f"❌ Failed to create router: {e}")
        return

    # Create session for conversation continuity
    session = SQLiteSession(session_id="smart_router_test")

    # Test queries for different agents
    test_queries = [
        ("What is the stock price of AAPL?", "finance"),
        ("Where is the Eiffel Tower?", "geo/wiki"),
        ("Tell me about Albert Einstein", "wiki"),
        ("What's the weather in Tokyo?", "web"),
    ]

    print("\n🧪 Testing routing with sample queries...")
    for query, expected_domain in test_queries:
        print(f"\n{'─' * 60}")
        print(f"Query: {query}")
        print(f"Expected domain: {expected_domain}")

        try:
            result = await router.route(query, session=session)
            print(f"✓ Response: {result.final_output[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Interactive loop
    print("\n" + "=" * 60)
    print("Interactive Mode - Enter queries to test routing")
    print("Empty line to quit")
    print("=" * 60)

    user_input = input("\nQuery: ")
    while user_input.strip():
        try:
            result = await router.route(user_input, session=session)
            print(f"\n📤 Response:\n{result.final_output}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

        user_input = input("Query: ")

    print("\n✨ SmartRouter test completed!")


if __name__ == "__main__":
    asyncio.run(main())
