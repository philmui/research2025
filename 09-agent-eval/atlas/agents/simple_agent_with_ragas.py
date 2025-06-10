from argparse import ArgumentParser

import asyncio
from datetime import datetime
import os
from llama_index.core.agent.workflow import (
    AgentInput,
    AgentOutput,
    AgentStream, 
    ToolCall as LlamaToolCall,
    ToolCallResult,
    AgentWorkflow,
)
from llama_index.llms.openai import OpenAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def get_current_time():
    """
    Get the current date and time to the second
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def convert_llamaindex_events_to_ragas(events):
    """
    Convert LlamaIndex events to a format suitable for ragas evaluation.
    This is a custom implementation since the official converter may not be available.
    """
    try:
        from ragas.dataset_schema import SingleTurnSample
        
        # Extract user input
        user_input = ""
        response = ""
        retrieved_contexts = []
        
        for event in events:
            if isinstance(event, AgentInput):
                # Extract user input from the first event
                if hasattr(event, 'input') and event.input:
                    user_input = str(event.input)
            elif isinstance(event, AgentOutput):
                # Extract response content
                if hasattr(event, 'response'):
                    response = str(event.response)
            elif isinstance(event, ToolCallResult):
                # Add tool results as context
                retrieved_contexts.append(f"Tool: {event.tool_name}, Result: {event.tool_output}")
        
        # Create a ragas sample
        sample = SingleTurnSample(
            user_input=user_input,
            response=response,
            retrieved_contexts=retrieved_contexts if retrieved_contexts else None
        )
        
        return sample
    except ImportError:
        print("⚠️  Ragas not properly installed. Skipping ragas conversion.")
        return None

async def invoke_agent(user_msg: str, include_ragas: bool = False):
    # Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        return "Error: Please set your OPENAI_API_KEY in the .env file. Get your API key from: https://platform.openai.com/api-keys"
    
    # Create agent workflow using the new API
    workflow = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[get_current_time],
        llm=OpenAI(model="gpt-4o-mini"),
        system_prompt="You are a helpful assistant that can answer questions. You can use the get_current_time function to get the current time."
    )
    
    # Run the workflow with the correct parameter
    handler = workflow.run(user_msg=user_msg)
    
    # Process events and collect response
    response_content = ""
    events = []
    async for event in handler.stream_events():
        if isinstance(event, (AgentInput, AgentOutput)):
            events.append(event)
        elif isinstance(event, AgentStream):
            print(f"{event.delta}", end="", flush=True)
            if event.delta:
                response_content += event.delta
        elif isinstance(event, ToolCallResult):
            events.append(event)
            print(
                f"\n\t🛠️ {event.tool_name} with {event.tool_kwargs} => {event.tool_output}\n"
            )
    
    # Get the final response
    result = await handler
    
    if include_ragas:
        ragas_sample = convert_llamaindex_events_to_ragas(events)
        return response_content, ragas_sample
    else:
        return response_content


async def evaluate_with_ragas(user_msg: str):
    """
    Example of how to use ragas evaluation with the agent
    """
    try:
        from ragas.metrics import Faithfulness, AnswerRelevancy
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI
        
        print(f"🔍 Evaluating agent response for: '{user_msg}'")
        
        # Get agent response with ragas data
        response_content, ragas_sample = await invoke_agent(user_msg, include_ragas=True)
        
        if ragas_sample is None:
            print("❌ Could not create ragas sample for evaluation")
            return response_content
        
        # Set up evaluator
        evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
        
        # Note: For a full evaluation, you'd typically need reference answers
        # This is a simplified example
        print(f"\n📊 Ragas Sample Created:")
        print(f"  User Input: {ragas_sample.user_input[:100]}...")
        print(f"  Response: {ragas_sample.response[:100]}...")
        print(f"  Contexts: {len(ragas_sample.retrieved_contexts or [])}")
        
        return response_content
        
    except ImportError as e:
        print(f"⚠️  Ragas evaluation not available: {e}")
        return response_content
    except Exception as e:
        print(f"❌ Error during ragas evaluation: {e}")
        return response_content


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--user_msg", type=str, help="Your message to the agent")
    parser.add_argument("--evaluate", action="store_true", help="Include ragas evaluation")
    args = parser.parse_args()
    
    if not args.user_msg:
        print("Error: Please provide a --user_msg argument")
        print("Example: python simple_agent_with_ragas.py --user_msg 'Hello!'")
        print("Example with evaluation: python simple_agent_with_ragas.py --user_msg 'Hello!' --evaluate")
    else:
        if args.evaluate:
            response_str = asyncio.run(evaluate_with_ragas(args.user_msg))
        else:
            response_str = asyncio.run(invoke_agent(args.user_msg))
        print(f"\n\n📝 Final Response: {response_str}") 