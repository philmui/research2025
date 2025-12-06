# Multi-Agent System Architecture

## Overview

This repository implements a multi-agent system built on OpenAI's `openai-agents` framework (v0.5.1+). The system follows a modular, domain-specific agent architecture where specialized agents handle specific types of tasks through well-defined tool interfaces.

## System Components

### 1. Core Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│              (CLI, Interactive Loops, Sessions)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      Agent Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Finance    │  │     Geo      │  │     Web      │       │
│  │    Agent     │  │    Agent     │  │    Agent     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐       │
│  │  Wikipedia   │  │   [Future    │  │   [Future    │       │
│  │    Agent     │  │   Agents]    │  │   Agents]    │       │
│  └──────┬───────┘  └──────────────┘  └──────────────┘       │
└─────────┼───────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────┐
│                     Tool/Action Layer                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Finance   │  │    Geo     │  │  Wikipedia │           │
│  │   Tools    │  │   Tools    │  │   Tools    │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
└────────┼───────────────┼───────────────┼──────────────────┘
         │               │               │
┌────────▼───────────────▼───────────────▼──────────────────┐
│               External Service Layer                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  yfinance  │  │  geopy/    │  │ Wikipedia  │           │
│  │    API     │  │  ArcGIS    │  │    API     │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└───────────────────────────────────────────────────────────┘
```

### 2. Directory Structure

```
asdrp/
├── actions/              # Tool implementations organized by domain
│   ├── finance/
│   │   └── finance_tools.py    # Financial data tools (yfinance)
│   ├── geo/
│   │   └── geo_tools.py        # Geocoding tools (geopy/ArcGIS)
│   └── search/
│       ├── __init__.py
│       └── wiki_tools.py       # Wikipedia search tools
├── agents/              # Agent definitions
│   ├── base.py          # ✨ NEW: AgentBuilder for clean construction
│   ├── routing/         # Orchestration agents
│   │   ├── __init__.py
│   │   └── smart_router.py     # ✨ NEW: SmartRouter implementation
│   └── singles/         # Single-purpose specialized agents
│       ├── finance_agent.py    # Stock market analysis agent
│       ├── geo_agent.py        # Geographic information agent
│       ├── web_agent.py        # Web search agent
│       └── wiki_agent.py       # Wikipedia research agent
└── util/                # Shared utilities
    ├── dict_utils.py    # Dictionary/parameter building utilities
    ├── config_loader.py # ✨ NEW: YAML configuration loading
    └── agent_registry.py # ✨ NEW: Agent lifecycle management

config/                  # ✨ NEW: Configuration directory
└── agents.yaml          # Agent definitions with instructions injection
```

## Agent Design Pattern

### Single-Purpose Specialized Agents

Each agent in this system follows a consistent design pattern with **dependency injection**.

#### 1. **Modern Agent Factory Pattern with Dependency Injection**
```python
from typing import Optional
from asdrp.agents.base import AgentBuilder

# Default instructions (fallback)
DEFAULT_INSTRUCTIONS = """
You are a <domain> specialist...
"""

# Tools for this agent
DOMAIN_TOOLS = [tool1, tool2, tool3]

def create_<domain>_agent(
    model: str = "gpt-4.1-mini",
    temperature: Optional[float] = 0.0,
    instructions: Optional[str] = None  # ✨ Injected from config
) -> Agent:
    """
    Create agent with dependency injection support.

    Args:
        model: LLM model (injected from config)
        temperature: Temperature setting (injected from config)
        instructions: System prompt (injected from config, falls back to default)
    """
    return AgentBuilder.create(
        name="<Domain> Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,
        tools=DOMAIN_TOOLS,
        model=model,
        temperature=temperature,
    )
```

#### 2. **Configuration-Driven Agent Components**

- **Name**: Human-readable identifier (in code)
- **Instructions**: System prompt (in `agents.yaml` - **not hardcoded!**)
  - Agent's role and purpose
  - Available capabilities
  - Usage guidelines and tips
  - Expected behavior patterns
- **Tools**: List of function tools from the action layer (in code)
- **Model**: LLM model to use (in `agents.yaml`)
- **Temperature**: Temperature setting (in `agents.yaml`)

#### 3. **Key Innovation: Instructions as Configuration**

**Before (hardcoded):**
```python
def create_finance_agent():
    return Agent(
        name="Finance Agent",
        instructions="You are a financial analyst...",  # ❌ Hardcoded
        tools=[...],
    )
```

**After (injected):**
```python
def create_finance_agent(instructions: Optional[str] = None):
    return AgentBuilder.create(
        name="Finance Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,  # ✅ Injected
        tools=FINANCE_TOOLS,
    )
```

**Configuration (`config/agents.yaml`):**
```yaml
- id: finance
  instructions: |
    You are a financial analyst...
    [Full prompt here - easy to modify!]
```

#### 4. **Session Management**
```python
session = SQLiteSession(session_id="<id>")
```
- Persistent conversation state
- Enables multi-turn interactions
- Maintains context across requests

#### 5. **Execution Pattern**
```python
result = await Runner.run(
    agent,
    input=<user_query>,
    session=session
)
```

### Current Agent Implementations

#### Finance Agent (`finance_agent.py`)
- **Purpose**: Stock market data retrieval and analysis
- **Tools**: 7 financial data functions
  - `get_ticker_info` - Company information and metrics
  - `get_historical_data` - Price history with customizable periods
  - `get_financials` - Income statement, balance sheet, cash flow
  - `get_recommendations` - Analyst recommendations
  - `get_calendar` - Earnings calendar
  - `get_news` - Latest news articles
  - `download_market_data` - Multi-ticker data download
- **External API**: yfinance (Yahoo Finance)

#### Geo Agent (`geo_agent.py`)
- **Purpose**: Geocoding and reverse geocoding
- **Tools**: 2 geographic functions
  - `get_coordinates_by_address` - Address → coordinates
  - `get_address_by_coordinates` - Coordinates → address
- **External API**: geopy with ArcGIS geocoder

#### Web Agent (`web_agent.py`)
- **Purpose**: General web search
- **Tools**: Built-in OpenAI `WebSearchTool`
- **Use Cases**: News, weather, current events

#### Wikipedia Agent (`wiki_agent.py`)
- **Purpose**: Wikipedia research and information retrieval
- **Tools**: 4 Wikipedia functions
  - `search_wikipedia` - Search for matching pages
  - `get_page_summary` - Quick article summaries
  - `get_page_content` - Full article with metadata
  - `get_geosearch` - Find articles near coordinates
- **External API**: Wikipedia Python library

## Tool Implementation Pattern

### Function Tool Decorator

All tools use the `@function_tool` decorator from OpenAI's agents framework:

```python
from agents import function_tool

@function_tool
async def tool_name(param: Type, ...) -> ReturnType:
    """
    Tool description for LLM.

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    # Implementation
    pass
```

### Key Design Principles

1. **Async by Default**: All tools are asynchronous
2. **Type Hints**: Full type annotations for LLM understanding
3. **Comprehensive Docstrings**: LLM uses these to understand tool usage
4. **Error Handling**: Robust error handling with meaningful messages
5. **Parameter Validation**: Validate inputs before API calls
6. **Executor Pattern**: Use `loop.run_in_executor()` for blocking operations

### Example: Finance Tool Pattern

```python
@function_tool
async def get_ticker_info(symbol: str) -> Dict[str, Any]:
    # 1. Validate parameters
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")

    # 2. Execute in thread pool (blocking I/O)
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        info = await loop.run_in_executor(None, lambda: ticker.info)
        return info if info else {}

    # 3. Handle errors gracefully
    except Exception as e:
        raise Exception(f"Failed to get ticker info for '{symbol}': {e}")
```

## Session and State Management

### SQLiteSession
- Provided by OpenAI agents framework
- Persists conversation history
- Enables context continuity across interactions
- Thread-safe for concurrent access

### Session Usage Pattern
```python
# Create or retrieve session
session = SQLiteSession(session_id="unique_id")

# Run agent with session
result = await Runner.run(agent, input=query, session=session)

# Session automatically tracks:
# - Conversation history
# - Tool call results
# - Agent handoffs (if any)
```

## Runner and Execution Flow

### Runner.run() Workflow

```
1. User Input
   ↓
2. Agent receives input with instructions
   ↓
3. LLM generates response
   ↓
4. Decision point:
   ├─ Final output? → Return result
   ├─ Tool calls? → Execute tools → Loop to step 3
   └─ Handoff? → Switch agent → Loop to step 2
   ↓
5. Max turns check (default: 10)
   ↓
6. Return RunResult with final_output
```

### RunResult Object
```python
result = await Runner.run(...)
result.final_output  # Final text response
result.agent        # Final agent that produced output
result.metadata     # Additional execution metadata
```

## SmartRouter System (NEW)

### Overview

The SmartRouter provides intelligent query routing to specialized agents through a configuration-driven, dependency-injection-based architecture.

### Components

#### 1. **ConfigLoader (`util/config_loader.py`)**
- Loads and validates `agents.yaml`
- Provides clean access to configuration
- Validates required fields
- Returns structured configuration objects

```python
from asdrp.util.config_loader import load_agent_configuration

config = load_agent_configuration("config/agents.yaml")
agents_config = config.get_agents_config()
```

#### 2. **AgentRegistry (`util/agent_registry.py`)**
- Manages agent lifecycle
- Implements lazy instantiation
- Caches agent instances
- Injects configuration parameters (model, temperature, **instructions**)

```python
from asdrp.util.agent_registry import create_agent_registry

registry = create_agent_registry(config)
agent = registry.get_agent("finance")  # Created and cached
```

**Key Feature - Parameter Injection:**
```python
# Registry reads config and creates partial function
kwargs = {
    "model": agent_config["model"],
    "temperature": agent_config["temperature"],
    "instructions": agent_config["instructions"]  # ✨ Instructions injected!
}
factory = partial(base_factory, **kwargs)
```

#### 3. **AgentBuilder (`agents/base.py`)**
- Provides builder pattern for agent construction
- Handles temperature intelligence (reasoning models)
- Creates proper ModelSettings
- Static factory methods for convenience

```python
from asdrp.agents.base import AgentBuilder

agent = AgentBuilder.create(
    name="My Agent",
    instructions=instructions,  # From config or default
    tools=tools,
    model="gpt-4.1-mini",
    temperature=0.0
)
```

#### 4. **SmartRouter (`agents/routing/smart_router.py`)**
- Routes queries to appropriate specialist agents
- Uses LLM to analyze queries
- Dynamically builds routing instructions
- Supports handoffs between agents

```python
from asdrp.agents.routing import create_smart_router

router = create_smart_router()
result = await router.route("What's AAPL stock price?")
```

### Configuration Flow

```
agents.yaml
    ↓
ConfigLoader (validate & parse)
    ↓
AgentConfiguration (structured data)
    ↓
AgentRegistry (inject parameters)
    ↓
AgentFactory (with model, temp, instructions)
    ↓
AgentBuilder (construct agent)
    ↓
Agent Instance (ready to use)
```

### Benefits

1. **Instructions as Data**: System prompts in configuration, not code
2. **Zero-Code Updates**: Change agent behavior via YAML
3. **A/B Testing**: Easy to test different prompts
4. **Environment-Specific**: Different configs for dev/staging/prod
5. **Version Control**: Track prompt changes in git
6. **Centralized Management**: All configurations in one place

## Utility Systems

### DictUtils (`util/dict_utils.py`)

A comprehensive utility class for building clean parameter dictionaries:

#### Key Methods

1. **`build_params(**kwargs)`**: Filter out None and falsy values
   - Configurable via `include_zero`, `include_false`, `include_empty_string`
   - Custom filter functions supported

2. **`filter_none(**kwargs)`**: Keep all values except None

3. **`filter_falsy(**kwargs)`**: Remove all falsy values

#### Usage in Tools
```python
# Build clean API parameters
params = DictUtils.build_params(
    period=period,
    interval=interval,
    start=start,      # None values automatically filtered
    end=end,
    prepost=prepost,
)

# Pass to API
data = api_call(**params)
```

## Configuration and Environment

### Environment Variables (.env)
```bash
OPENAI_API_KEY=<key>          # Required for OpenAI agents
# Domain-specific keys as needed
```

### Python Requirements (pyproject.toml)
- **openai-agents>=0.5.1**: Core framework
- **yfinance>=0.2.66**: Financial data
- **geopy>=2.4.1**: Geocoding
- **wikipedia>=1.4.0**: Wikipedia access
- **googlemaps>=4.10.0**: Google Maps (future use)
- **python-dotenv>=1.2.1**: Environment management

## Tracing and Debugging

### Tracing Control
```python
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)  # Disable for cleaner output
```

### Interactive Testing Pattern
```python
async def main():
    agent = create_agent()

    # Initial test query
    result = await Runner.run(agent, input="test query", session=session)
    print(result.final_output)

    # Interactive loop
    user_input = input("Ask Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Agent: ")

if __name__ == "__main__":
    asyncio.run(main())
```

## Extension Points

### 1. Adding New Agents
1. Create new tool file in `asdrp/actions/<domain>/`
2. Implement tools with `@function_tool` decorator
3. Create agent file in `asdrp/agents/singles/`
4. Define agent with factory pattern
5. Add interactive testing loop

### 2. Multi-Agent Orchestration (Future)
- Use `asdrp/agents/routing/` for orchestrator agents
- Implement handoff patterns with `handoffs` parameter
- Use `handoff_description` for agent discovery

### 3. Advanced Features
- **Input Guardrails**: Validate/filter inputs before processing
- **Output Guardrails**: Validate/filter outputs before returning
- **Custom Hooks**: Inject logic at execution points
- **Output Types**: Structured outputs with Pydantic models
- **Model Settings**: Temperature, max tokens, etc.

## Performance Considerations

### Async Execution
- All I/O operations are non-blocking
- Tools run in thread pool for CPU-bound work
- Multiple agents can run concurrently

### Session Management
- SQLite sessions are lightweight
- Consider session cleanup for long-running systems
- Use unique session IDs per conversation thread

### API Rate Limiting
- yfinance: Rate limits vary by endpoint
- Wikipedia: Requests should be throttled (set user agent)
- Geopy: ArcGIS has service limits

## Security Considerations

1. **API Key Management**: Never commit `.env` to version control
2. **Input Validation**: All tools validate parameters
3. **Error Handling**: Avoid exposing internal details in errors
4. **Rate Limiting**: Implement for production use
5. **User Agent**: Set proper user agent for API calls
