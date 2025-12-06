"""
Base Agent Factory Module

Provides base classes and utilities for creating agents with dependency injection.
Follows SOLID principles for clean, maintainable, and extensible code.

Design Principles:
- Single Responsibility: Factory handles only agent creation
- Open/Closed: Easy to extend for new agent types
- Liskov Substitution: All factories produce compatible Agent instances
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on configuration abstractions, not hard-coded values

Usage:
    from asdrp.agents.base import AgentBuilder
    
    # Simple usage with tools list
    agent = AgentBuilder.create(
        name="My Agent",
        instructions="You are a helpful assistant.",
        tools=[my_tool],
        model="gpt-4.1-mini"
    )
    
    # Or use the builder pattern for more control
    builder = AgentBuilder()
    agent = (builder
        .with_name("My Agent")
        .with_instructions("You are a helpful assistant.")
        .with_tools([my_tool])
        .with_model("gpt-4.1-mini", temperature=0.0)
        .build())
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from agents import Agent, ModelSettings


# Models that support temperature parameter
# Reasoning models (o1, o3 series) do NOT support temperature
TEMPERATURE_SUPPORTED_PATTERNS = ["gpt-4o", "gpt-4-turbo", "gpt-3.5", "gpt-4.1"]


def supports_temperature(model: str) -> bool:
    """
    Check if a model supports the temperature parameter.
    
    Args:
        model: The model name/identifier
        
    Returns:
        True if the model supports temperature, False otherwise
    """
    model_lower = model.lower()
    return any(pattern in model_lower for pattern in TEMPERATURE_SUPPORTED_PATTERNS)


def create_model_settings(
    model: str,
    temperature: Optional[float] = None,
    **kwargs
) -> Optional[ModelSettings]:
    """
    Create ModelSettings with intelligent temperature handling.
    
    Only applies temperature for models that support it. This prevents
    errors when using reasoning models (o1, o3 series).
    
    Args:
        model: The model name
        temperature: Temperature setting (0.0-2.0). None to disable.
        **kwargs: Additional ModelSettings parameters
        
    Returns:
        ModelSettings instance or None if no settings needed
    """
    settings_kwargs = {}
    
    # Only apply temperature for models that support it
    if temperature is not None and supports_temperature(model):
        settings_kwargs["temperature"] = temperature
    
    # Add any additional settings
    settings_kwargs.update(kwargs)
    
    # Return None if no settings to apply
    if not settings_kwargs:
        return None
    
    return ModelSettings(**settings_kwargs)


@dataclass
class AgentConfig:
    """
    Configuration data class for agent creation.
    
    Encapsulates all parameters needed to create an agent.
    Uses dataclass for clean, immutable configuration objects.
    
    Attributes:
        name: Agent name
        instructions: System prompt/instructions
        tools: List of tools available to the agent
        model: LLM model to use
        temperature: Temperature setting (None for reasoning models)
        handoffs: List of agents this agent can hand off to
        extra_settings: Additional ModelSettings parameters
    """
    name: str
    instructions: str
    tools: List[Any] = field(default_factory=list)
    model: str = "gpt-4.1-mini"
    temperature: Optional[float] = 0.0
    handoffs: List[Agent] = field(default_factory=list)
    extra_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_agent(self) -> Agent:
        """
        Convert this configuration to an Agent instance.
        
        Returns:
            Configured Agent instance
        """
        model_settings = create_model_settings(
            self.model,
            self.temperature,
            **self.extra_settings
        )
        
        # Build agent kwargs - only include handoffs if non-empty
        agent_kwargs = {
            "name": self.name,
            "instructions": self.instructions,
            "tools": self.tools,
            "model": self.model,
            "model_settings": model_settings,
        }
        
        # Only add handoffs if there are any (Agent doesn't accept empty list or None)
        if self.handoffs:
            agent_kwargs["handoffs"] = self.handoffs
        
        return Agent(**agent_kwargs)


class AgentBuilder:
    """
    Builder for constructing agents with a fluent interface.
    
    Implements the Builder pattern for flexible agent construction.
    Supports both static factory method and fluent builder pattern.
    
    Example (static factory):
        agent = AgentBuilder.create(
            name="My Agent",
            instructions="You are helpful.",
            tools=[my_tool]
        )
    
    Example (fluent builder):
        agent = (AgentBuilder()
            .with_name("My Agent")
            .with_instructions("You are helpful.")
            .with_tools([my_tool])
            .build())
    """
    
    def __init__(self):
        """Initialize a new builder with default values."""
        self._name: str = ""
        self._instructions: str = ""
        self._tools: List[Any] = []
        self._model: str = "gpt-4.1-mini"
        self._temperature: Optional[float] = 0.0
        self._handoffs: List[Agent] = []
        self._extra_settings: Dict[str, Any] = {}
    
    def with_name(self, name: str) -> "AgentBuilder":
        """Set the agent name."""
        self._name = name
        return self
    
    def with_instructions(self, instructions: str) -> "AgentBuilder":
        """Set the agent instructions/system prompt."""
        self._instructions = instructions
        return self
    
    def with_tools(self, tools: List[Any]) -> "AgentBuilder":
        """Set the agent tools."""
        self._tools = tools
        return self
    
    def with_model(
        self,
        model: str,
        temperature: Optional[float] = 0.0
    ) -> "AgentBuilder":
        """Set the model and temperature."""
        self._model = model
        self._temperature = temperature
        return self
    
    def with_handoffs(self, handoffs: List[Agent]) -> "AgentBuilder":
        """Set the agents this agent can hand off to."""
        self._handoffs = handoffs
        return self
    
    def with_extra_settings(self, **kwargs) -> "AgentBuilder":
        """Set additional ModelSettings parameters."""
        self._extra_settings.update(kwargs)
        return self
    
    def build(self) -> Agent:
        """
        Build the agent from the configured parameters.
        
        Returns:
            Configured Agent instance
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not self._name:
            raise ValueError("Agent name is required")
        if not self._instructions:
            raise ValueError("Agent instructions are required")
        
        config = AgentConfig(
            name=self._name,
            instructions=self._instructions,
            tools=self._tools,
            model=self._model,
            temperature=self._temperature,
            handoffs=self._handoffs,
            extra_settings=self._extra_settings,
        )
        
        return config.to_agent()
    
    @staticmethod
    def create(
        name: str,
        instructions: str,
        tools: List[Any] = None,
        model: str = "gpt-4.1-mini",
        temperature: Optional[float] = 0.0,
        handoffs: List[Agent] = None,
        **extra_settings
    ) -> Agent:
        """
        Static factory method for quick agent creation.
        
        This is the simplest way to create an agent when you have
        all parameters ready.
        
        Args:
            name: Agent name
            instructions: System prompt/instructions
            tools: List of tools (default: empty list)
            model: LLM model (default: "gpt-4.1-mini")
            temperature: Temperature (default: 0.0, None for reasoning models)
            handoffs: Agents to hand off to (default: None)
            **extra_settings: Additional ModelSettings parameters
            
        Returns:
            Configured Agent instance
        """
        config = AgentConfig(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model=model,
            temperature=temperature,
            handoffs=handoffs or [],
            extra_settings=extra_settings,
        )
        
        return config.to_agent()
    
    @staticmethod
    def from_config(
        config: Dict[str, Any],
        tools: List[Any] = None,
        handoffs: List[Agent] = None
    ) -> Agent:
        """
        Create an agent from a configuration dictionary.
        
        This method supports dependency injection - the configuration
        comes from external sources (like agents.yaml) rather than
        being hard-coded.
        
        Args:
            config: Configuration dictionary with keys:
                - name: Agent name
                - instructions: System prompt
                - model: LLM model (optional)
                - temperature: Temperature (optional)
            tools: List of tools to attach
            handoffs: Agents to hand off to
            
        Returns:
            Configured Agent instance
            
        Raises:
            KeyError: If required config keys are missing
        """
        return AgentBuilder.create(
            name=config["name"],
            instructions=config["instructions"],
            tools=tools or [],
            model=config.get("model", "gpt-4.1-mini"),
            temperature=config.get("temperature", 0.0),
            handoffs=handoffs or [],
        )


# Convenience type alias for tool lists
ToolList = List[Any]


def create_agent_factory(
    tools: ToolList,
    default_instructions: str = ""
) -> Callable[..., Agent]:
    """
    Higher-order function that creates a configurable agent factory.
    
    This enables creating specialized agent factories that have their
    tools pre-configured but accept instructions and model settings
    from configuration.
    
    Args:
        tools: List of tools for the agent
        default_instructions: Fallback instructions if none provided
        
    Returns:
        Factory function that creates agents
        
    Example:
        # Create a factory with pre-configured tools
        finance_factory = create_agent_factory(
            tools=[get_ticker_info, get_historical_data],
            default_instructions="You are a finance agent."
        )
        
        # Use the factory (instructions from config override default)
        agent = finance_factory(
            name="Finance Agent",
            instructions="Custom instructions from config.",
            model="gpt-4.1-mini"
        )
    """
    def factory(
        name: str,
        instructions: Optional[str] = None,
        model: str = "gpt-4.1-mini",
        temperature: Optional[float] = 0.0,
        **kwargs
    ) -> Agent:
        """
        Factory function for creating agents.
        
        Args:
            name: Agent name
            instructions: System prompt (uses default if None)
            model: LLM model
            temperature: Temperature setting
            **kwargs: Additional settings
            
        Returns:
            Configured Agent instance
        """
        return AgentBuilder.create(
            name=name,
            instructions=instructions or default_instructions,
            tools=tools,
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    return factory


# ------------------------------------------------------------
# Module self-test
# ------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Base Agent Factory Module Test")
    print("=" * 60)
    
    # Test temperature support detection
    print("\n🔧 Testing temperature support detection:")
    test_models = [
        ("gpt-5", True),
        ("gpt-5-mini", True),
        ("gpt-4.1-mini", True),
        ("gpt-4o-mini", True),
        ("o1-mini", False),
        ("o1-preview", False),
        ("o3-mini", False),
    ]
    for model, expected in test_models:
        result = supports_temperature(model)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {model}: {result} (expected: {expected})")
    
    # Test AgentConfig
    print("\n📋 Testing AgentConfig:")
    config = AgentConfig(
        name="Test Agent",
        instructions="You are a test agent.",
        model="gpt-4.1-mini",
        temperature=0.5
    )
    print(f"  Config: {config}")
    agent = config.to_agent()
    print(f"  Agent created: {agent.name}")
    
    # Test AgentBuilder fluent interface
    print("\n🔨 Testing AgentBuilder fluent interface:")
    agent = (AgentBuilder()
        .with_name("Builder Test")
        .with_instructions("Created with builder pattern.")
        .with_model("gpt-4.1-mini", temperature=0.3)
        .build())
    print(f"  Agent: {agent.name}")
    print(f"  Model: {agent.model}")
    
    # Test static factory
    print("\n🏭 Testing AgentBuilder.create():")
    agent = AgentBuilder.create(
        name="Static Factory Test",
        instructions="Created with static factory.",
        model="gpt-4.1-mini"
    )
    print(f"  Agent: {agent.name}")
    
    # Test from_config
    print("\n📄 Testing AgentBuilder.from_config():")
    test_config = {
        "name": "Config Agent",
        "instructions": "Created from config dictionary.",
        "model": "gpt-4.1-mini",
        "temperature": 0.0
    }
    agent = AgentBuilder.from_config(test_config)
    print(f"  Agent: {agent.name}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

