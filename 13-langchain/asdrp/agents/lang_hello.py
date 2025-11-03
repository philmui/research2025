from langchain.agents import create_agent
from dotenv import load_dotenv, find_dotenv
import asyncio

_ = load_dotenv(find_dotenv())

def say_hello(name: str) -> str:
    """Greet the person `name`."""
    return f"It's nice to meet you, {name}!"

agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[say_hello],
    system_prompt="You are a helpful assistant",
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "Hi, I am Joe."}]}
)

print(response["messages"][-1].content)