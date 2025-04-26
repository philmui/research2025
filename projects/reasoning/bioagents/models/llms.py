from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
from agents import RunResult, agent
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion
from dataclasses import dataclass
from bioagents.models.citation import Citation
from typing import List
from bioagents.agents.base import AgentResponse

@dataclass
class LLM:
    # Model identifiers
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4O = "gpt-4o"
    
    # Shared OpenAI client instance
    _client: OpenAI | None = None
    _async_client: AsyncOpenAI | None = None
    _model = GPT_4_1_MINI
    _timeout = 60
    
    def __init__(self, model=GPT_4_1_MINI, timeout=60):
        self._model = model
        self._timeout = timeout
        self._client = OpenAI(timeout=self._timeout)
        self._async_client = AsyncOpenAI(timeout=self._timeout)
    
    async def achat_completion(self, query_str: str, **kwargs) -> str:
        """
        Asynchronously chat with the model.
        
        Args:
            query_str: The query string
            **kwargs: Additional parameters for the completion
            
        Returns:
            The content string
        """
        response = await self._async_client.chat.completions.create(
            messages=[{"role": "user", "content": query_str}],
            model=self._model,
            **kwargs
        )
        content = ""
        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
        
        return content


#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    
    gpt41 = LLM(model=LLM.GPT_4_1_MINI)
    # Async example
    async def main():
        response = await gpt41.achat_completion(
            query_str="Hello async world!",
        )
        print(response)
    
    asyncio.run(main())
