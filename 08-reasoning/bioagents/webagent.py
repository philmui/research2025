import asyncio
from agents import Agent, Runner, RunResult
from agents.tool import WebSearchTool
from agents.tracing import set_tracing_disabled
from dataclasses import dataclass
from pydantic import BaseModel

set_tracing_disabled(disabled=True)

TOOL_AGENT_INSTRUCTIONS = """
You are a helpful assistant that can search the web for specific information.
You should only search the web for information that is relevant to the user's query.
Your repsonse should contain specific references to the information that you found.

## Inline Citations

Your response should contain inline citations to the information that you found.
The citations should be formatted inline with reference numbers corresponding to 
the references below.

## Response Format

Your response should be structured with clear headings and subheadings and 
end with a list of references.  Do not use "#" or "##" as level of headings.  

## References

[1] - [Reference 1](https://www.google.com)
[2] - [Reference 2](https://www.google.com)
[3] - [Reference 3](https://www.google.com)
"""

@dataclass
class Citation:
    url: str
    title: str
    snippet: str

@dataclass
class AgentResponse:
    output: str
    citations: list[Citation]

@dataclass
class ThinkingAgent:
    agent: Agent
    def __init__(self, name: str = "ThinkingAgent"):
        self.agent = self.create_agent(name)

    def create_agent(self, name: str):
        tool_agent = Agent(
            name=name, 
            instructions=TOOL_AGENT_INSTRUCTIONS,
            tools=[
                WebSearchTool(
                    search_context_size="low",
                    user_location={
                        "type": "approximate",
                        "country": "US",
                    }
                )
            ],
        )
        return tool_agent

    async def run(self, query_str: str) -> AgentResponse:
        response_obj = await Runner.run(starting_agent=self.agent, input=query_str, max_turns=3)
        return await self.construct_response(response_obj)
        
    async def construct_response(self, response_obj: RunResult) -> AgentResponse:
        # Extract citations from the message output item's annotations
        citations = []
        for item in response_obj.new_items:
            if item.type == 'message_output_item':
                for content in item.raw_item.content:
                    if hasattr(content, 'annotations'):
                        for annotation in content.annotations:
                            if annotation.type == 'url_citation':
                                citations.append(Citation(
                                    url=annotation.url,
                                    title=annotation.title,
                                    snippet=content.text[annotation.start_index:annotation.end_index]
                                ))
        return AgentResponse(
            output=response_obj.final_output,
            citations=citations
        )

async def run_agent(query_str: str):
    agent = ThinkingAgent()
    
    while query_str != "":
        try:
            result = await agent.run(query_str)
            print(f"\n{result.output}")
            if result.citations and len(result.citations) > 0:
                print("\nREFERENCES:")
                for citation in result.citations:
                    print(f"- {citation.title} [{citation.url}]")
        except Exception as e:
            print(f"Error: {e}")
        query_str = input("\nEnter a query (or press Enter to quit): ")

if __name__ == "__main__":
    query_str = "Should I be concerned about persistent lower back pain?"
    asyncio.run(run_agent(query_str))
    print("Good bye!")