import asyncio
from agents import Agent, Runner, RunResult, trace, gen_trace_id
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from agents.tool import WebSearchTool
from agents.tracing import set_tracing_disabled
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel
import datetime
import pytz

from loguru import logger
from .base import Citation, AgentResponse, DEFAULT_THINKING_MODEL
from .schemas import ReflexiveResponse
from .prompts import RESPONSE_JUDGE_SYSTEM_PROMPT_TMPL
from pprint import pprint

set_tracing_disabled(disabled=True)

TOOL_AGENT_INSTRUCTIONS = """
You are a helpful assistant that can search the web for up-to-date  and specific information.
You should only search the web for information that is relevant to the user's query.
If you are able to find specific information, your repsonse should contain specific references 
to the information that you found.

Today's date is {today}.
Right now, the time is {time}.

## Inline Citations

Your response should contain inline citations to the information that you found.
The citations should be formatted inline with numbers corresponding to 
the references in your repsonse "References" section.

## Response Format

Your response should be structured with clear headings and subheadings and 
end with a list of references.

Your response should use the same language as the user's query.

## References

Use Markdown formatting for bulleted list of hyperlinked titles for each reference.

1. [Reference 1 title](https://www.google.com)
2. [Reference 2 title](https://www.google.com)
3. [Reference 3 title](https://www.google.com)

"""

@dataclass
class ReflexiveAgent:
    agent: Agent
    def __init__(self, name: str = "ReflexiveAgent", model: str = DEFAULT_THINKING_MODEL):
        self.agent = self.create_agent(name, model)
        self.judge_agent = self.create_judge_agent(name, model)

    def create_judge_agent(self, name: str, model: str):
        """Create an agent that evaluates responses and provides reflective critique"""
        judge = Agent(
            name=f"{name}_Reflexive",
            instructions=RESPONSE_JUDGE_SYSTEM_PROMPT_TMPL,
            model=model,
            output_type=ReflexiveResponse
        )
        logger.info(f"Created judge agent {name} with model {model}")
        return judge

    def create_agent(self, name: str, model: str):
        # Get current date and time
        now = datetime.datetime.now(pytz.timezone('UTC'))
        today_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S %Z")
        
        # Format the instructions with current date and time
        formatted_instructions = TOOL_AGENT_INSTRUCTIONS.format(
            today=today_str,
            time=time_str
        )
        
        self.biomcp_server = MCPServerStdio(
            cache_tools_list=True,
            params=MCPServerStdioParams(
                command="biomcp",
                args=["run"],
            ),
            name="biomcp",
        )
        tool_agent = Agent(
            name=name,
            instructions=formatted_instructions,
            model=model,
            mcp_servers=[self.biomcp_server],
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
        logger.info(f"Created {name} with model {model}:\n{tool_agent.instructions}")
        return tool_agent

    async def run(self, query_str: str) -> AgentResponse:
        """Run a query using the configured agent and server."""
        if not self.biomcp_server or not self.agent:
            raise RuntimeError("Agent not properly initialized")

        try:
            # Connect before running
            await self.biomcp_server.connect()
            
            # Run the query with the primary agent
            agent_response = await Runner.run(
                starting_agent=self.agent, 
                input=query_str, 
                max_turns=2,
            )
            
            # Run the reflective agent with the primary output as input
            judge_prompt = ("Please evaluate the following response to a user query:\n"
                            f"USER QUERY: {query_str}\n"
                            f"RESPONSE TO EVALUATE: {agent_response.final_output}\n"
                            "Provide a detailed evaluation following the specified schema.")            
            try:
                judge_response = await Runner.run(
                    starting_agent=self.judge_agent,
                    input=judge_prompt,
                    max_turns=1,
                )
                # Log the reflective analysis
                print(f"{10*'='}> Judge response\n\n")
                pprint(judge_response.final_output, indent=2)
                
                # Construct response with reflexive analysis
                total_response = await self.construct_response(
                    agent_response, 
                    judge_response=judge_response
                )
            except Exception as e:
                logger.warning(f"Error in reflexive analysis: {str(e)}")
                # Fall back to just the primary response if reflexive analysis fails
                total_response = await self.construct_response(agent_response)
            
            return total_response
            
        except Exception as e:
            logger.error(f"Error during query execution: {str(e)}")
            raise
        finally:
            try:
                await self.biomcp_server.cleanup()
            except Exception as e:
                logger.warning(f"Error during server cleanup: {str(e)}")
        
    async def construct_response(
        self, 
        agent_response: RunResult, 
        judge_response: ReflexiveResponse = None
    ) -> AgentResponse:
        # Extract citations from the message output item's annotations
        citations = []
        for item in agent_response.new_items:
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
            output=agent_response.final_output,
            citations=citations,
            judge_response=judge_response
        )

#------------------------------------------------------------------------------
# Smoke tests
#------------------------------------------------------------------------------
async def run_agent(query_str: str):
    agent = ReflexiveAgent()
    
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