from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import asyncio
import os
from tavily import AsyncTavilyClient

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    AgentStream,
)
from llama_index.core.workflow import (
    Context,
    InputRequiredEvent,
    HumanResponseEvent,
)

llm = Ollama(model="llama3.2:3b-instruct-q8_0", temperature=0.01, timeout=120)
embedding = OllamaEmbedding(model_name="mxbai-embed-large")

async def say_hello(name: str) -> str:
    """
    Use this function to say hello to the user as a form of greeting.
    """
    return f"Hello, {name}!"

async def say_bye(name: str) -> str:
    """
    Use this function to say goodbye or farewell as the user is leaving or exiting the conversation.
    """
    return f"See you next time, {name}!"

async def say_hello_with_llm(name: str) -> str:
    return llm.complete(f"Hello, {name}!")

async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_AI_API_KEY"))
    return str(await client.search(query))

async def set_name(ctx: Context, name: str) -> str:
    """Use this function to set the name of the user."""
    state = await ctx.get("state")
    state["name"] = name
    await ctx.set("state", state)
    return f"Name set to {name}."

async def main():
    agent = AgentWorkflow.from_tools_or_functions(
        [say_hello, say_bye, search_web, set_name],
        llm=llm,
        system_prompt=(
            "You are a helpful assistant that can answer questions and help with tasks."
        ),
        initial_state={"name": "unset"}
    )
    context = Context(agent)
    
    query_string = input("Enter your query: ")
    while query_string != "":
        response = await agent.run(user_msg=query_string, ctx=context)
        print(f"RESPONSE: {response.response.content}")
        # print(f"\tstate: {await context.get('state')}")
        query_string = input("Enter your query: ")


if __name__ == "__main__":
    asyncio.run(main())
