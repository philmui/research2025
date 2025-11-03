from langchain.agents import create_agent
from dotenv import load_dotenv, find_dotenv
import asyncio

_ = load_dotenv(find_dotenv())

def say_hello(name: str) -> str:
    """Greet the person `name`."""
    print(f"==> Greeting {name}...")
    return f"It's nice to meet you, {name}!"

# Creating a "System 1" reasoning agent
agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[say_hello],
    system_prompt="You are a helpful assistant",
)

async def main():
    
    user_input = input("How can I help you? ")
    while user_input != "":
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        print(response["messages"][-1].content)
        user_input = input("How can I help you? ")
    
if __name__ == "__main__":
    asyncio.run(main())