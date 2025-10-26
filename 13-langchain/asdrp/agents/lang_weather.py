from langchain.agents import create_agent
from dotenv import load_dotenv, find_dotenv
import asyncio

_ = load_dotenv(find_dotenv())

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in San Jose, CA?"}]}
)
print(response["messages"][-1].content)