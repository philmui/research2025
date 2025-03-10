from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import asyncio
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import Context

llm = Ollama(model="llama3.2:3b-instruct-q8_0", temperature=0.01, timeout=120)
embedding = OllamaEmbedding(model_name="mxbai-embed-large")

def say_hello(name: str) -> str:
    """
    Use this function to say hello to the user as a form of greeting.
    """
    return f"Hello, {name}!"

def say_bye(name: str) -> str:
    """
    Use this function to say goodbye or farewell as the user is leaving or exiting the conversation.
    """
    return f"See you next time, {name}!"

def say_hello_with_llm(name: str) -> str:
    return llm.complete(f"Hello, {name}!")

async def main():
    agent = AgentWorkflow.from_tools_or_functions(
        [say_hello, say_bye],
        llm=llm,
        system_prompt=(
            "You are a helpful assistant that can answer questions and help with tasks."
            "You can use the following functions to help with the user's query:"
            "1. say_hello(name: str) -> str: Use this function to say hello to the user as a form of greeting."
            "2. say_bye(name: str) -> str: Use this function to say goodbye or farewell as the user is leaving or exiting the conversation."
        )
    )
    context = Context(agent)
    
    query_string = input("Enter your query: ")
    while query_string != "":
        response = await agent.run(query_string, ctx=context)
        print(str(response))
        query_string = input("Enter your query: ")


if __name__ == "__main__":
    asyncio.run(main())
