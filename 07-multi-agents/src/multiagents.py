from dotenv import load_dotenv, find_dotenv

import asyncio
import os
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from tavily import AsyncTavilyClient

load_dotenv(find_dotenv())
async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return str(await client.search(query))


async def record_notes(ctx: Context, notes: str) -> str:
    """Record research notes for later use."""
    current_state = await ctx.get("state")
    current_state["research_notes"].append(notes)
    await ctx.set("state", current_state)
    return "Notes recorded."


async def main():
    llm = OpenAI(model="gpt-4o", temperature=0.01)
    workflow = AgentWorkflow.from_tools_or_functions(
        [search_web],
        llm=llm,
        system_prompt="You are a helpful assistant that can search the web for information.",
    )
    ctx = Context(workflow)
    input_prompt = input("Enter a question: ")
    while input_prompt != "exit":
        result = await workflow.run(user_msg=input_prompt, ctx=ctx)
        print(str(result))
        input_prompt = input("Enter a question: ")

if __name__ == "__main__":
    asyncio.run(main())
