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
from ragas.metrics import AgentGoalAccuracyWithoutReference, AgentGoalAccuracyWithReference
from ragas.dataset_schema import SingleTurnSample, MultiTurnSample
from ragas.llms import LlamaIndexLLMWrapper
from ragas.messages import ToolCall as RagasToolCall, HumanMessage, AIMessage, ToolMessage

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def convert_llamaindex_events_to_ragas(events, user_msg: str):
    """
    Convert LlamaIndex events to a MultiTurnSample suitable for ragas evaluation.
    
    Args:
        events: List of LlamaIndex workflow events
        user_msg: Original user message
    
    Returns:
        MultiTurnSample: Ragas MultiTurnSample object with conversation flow
    """
    try:
        messages = []
        current_response_content = ""
        current_tool_calls = []
        
        # Start with the user message
        messages.append(HumanMessage(content=user_msg))
        
        for event in events:
            if isinstance(event, AgentInput):
                # AgentInput contains the user's message - already added above
                pass
                
            elif isinstance(event, AgentOutput):
                # Extract AI response content
                if hasattr(event, 'response') and hasattr(event.response, 'message'):
                    current_response_content = str(event.response.message.content)
                elif hasattr(event, 'response'):
                    current_response_content = str(event.response)
                    
            elif isinstance(event, ToolCallResult):
                # Create tool call for AI message
                tool_call = RagasToolCall(
                    name=event.tool_name,
                    args=event.tool_kwargs
                )
                current_tool_calls.append(tool_call)
                
                # Add tool result as ToolMessage
                messages.append(ToolMessage(
                    content=str(event.tool_output)
                ))
        
        # Add the final AI response with any tool calls
        if current_response_content or current_tool_calls:
            ai_message = AIMessage(
                content=current_response_content,
                tool_calls=current_tool_calls if current_tool_calls else None
            )
            # Insert AI message before tool messages (if any)
            if current_tool_calls and len(messages) > 1:
                # Insert AI message before the last tool message(s)
                insert_index = len(messages) - len(current_tool_calls)
                messages.insert(insert_index, ai_message)
            else:
                messages.append(ai_message)
        
        # Create MultiTurnSample
        sample = MultiTurnSample(
            user_input=messages
        )
        
        return sample
        
    except Exception as e:
        print(f"⚠️  Error converting to ragas format: {e}")
        return None

def get_current_time() -> str:
    """
    Get the current date and time to the second
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def invoke_agent(user_msg: str):    
    # Create agent workflow using the new API
    workflow = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[get_current_time],
        llm=OpenAI(model="gpt-4.1-mini"),
        system_prompt="You are a simple agent that can answer questions. You can use the get_current_time function to get the current time."
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
    
    await handler  # may be redundant
    ragas_sample = convert_llamaindex_events_to_ragas(events, user_msg)
    return response_content, ragas_sample

async def evaluate_agent_without_reference(ragas_sample: MultiTurnSample):
    llm = OpenAI(model="gpt-4.1-mini")
    evaluator_llm = LlamaIndexLLMWrapper(llm=llm)
    accuracy_without_reference = AgentGoalAccuracyWithoutReference(llm=evaluator_llm)
    score = await accuracy_without_reference.multi_turn_ascore(sample = ragas_sample)
    print(f"Accuracy w/o reference: {score}")
    
async def evaluate_agent_with_reference(ragas_sample: MultiTurnSample):
    llm = OpenAI(model="gpt-4.1-mini")
    evaluator_llm = LlamaIndexLLMWrapper(llm=llm)
    accuracy_with_reference = AgentGoalAccuracyWithReference(llm=evaluator_llm)
    score = await accuracy_with_reference.multi_turn_ascore(sample = ragas_sample)
    print(f"Accuracy w/ reference: {score}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--user_msg", type=str, help="How are you?")
    args = parser.parse_args()
    
    if not args.user_msg:
        print("Error: Please provide a --user_msg argument")
        print("Example: python simple_agent.py --user_msg 'Hello!'")
    else:
        response_str, ragas_sample = asyncio.run(invoke_agent(args.user_msg))
        print(f"\n\nRAGAS MultiTurnSample created with {len(ragas_sample.user_input) if ragas_sample else 0} messages")
        if ragas_sample:
            print("Message types:", [type(msg).__name__ for msg in ragas_sample.user_input])
            asyncio.run(evaluate_agent_without_reference(ragas_sample))
            
            ragas_sample.reference = ragas_sample.user_input[-1].content
            asyncio.run(evaluate_agent_with_reference(ragas_sample))