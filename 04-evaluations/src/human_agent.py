from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import asyncio

from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import (
    Context,
    InputRequiredEvent,
    HumanResponseEvent,
)

# llm = Ollama(model="llama3.2:3b-instruct-q8_0", temperature=0.01, timeout=120)
llm = OpenAI(model="gpt-4o-mini", temperature=0.01, timeout=120)

async def dangerous_task(ctx: Context) -> str:
    """A dangerous task that requires human confirmation."""
    ctx.write_event_to_stream(
        InputRequiredEvent(
            prefix="Are you sure you want to proceed? ",
            user_name="Logan",
        )
    )

    response = await ctx.wait_for_event(
        HumanResponseEvent, requirements={"user_name": "Logan"}
    )
    if response.response == "yes":
        return "Dangerous task completed successfully."
    else:
        return "Dangerous task aborted."

async def main():
    agent = AgentWorkflow.from_tools_or_functions(
        [dangerous_task],
        llm=llm,
        system_prompt="You are a helpful assistant that can perform dangerous tasks.",
    )
    context = Context(agent)
    
    handler = agent.run(user_msg="I want to proceed with the dangerous task.")
    async for event in handler.stream_events():
        if isinstance(event, InputRequiredEvent):
            response = input(event.prefix).strip().lower()
            handler.ctx.send_event(
                HumanResponseEvent(
                    response=response,
                    user_name=event.user_name,
                )
            )
    response = await handler
    print(response.response.content)

if __name__ == "__main__":
    asyncio.run(main())
