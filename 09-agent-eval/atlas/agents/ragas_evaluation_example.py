"""
Example of using MultiTurnSample with ragas evaluation for LlamaIndex agents
"""

import asyncio
import os
import sys

# Add the parent directory to path to import simple_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_agent import invoke_agent
from ragas.metrics import AgentGoalAccuracyWithoutReference, AgentGoalAccuracyWithReference, ToolCallAccuracy
from ragas.llms import LlamaIndexLLMWrapper
from ragas.messages import ToolCall as RagasToolCall
from llama_index.llms.openai import OpenAI

async def evaluate_agent_with_ragas(user_msg: str, reference_answer: str = None):
    """
    Comprehensive example of evaluating a LlamaIndex agent using ragas MultiTurnSample
    
    Args:
        user_msg: User's question/message
        reference_answer: Optional reference answer for comparison
    """
    print(f"🤖 Evaluating agent for: '{user_msg}'")
    print("=" * 50)
    
    # Get agent response and ragas sample
    response_content, ragas_sample = await invoke_agent(user_msg)
    
    if not ragas_sample:
        print("❌ Failed to create ragas sample")
        return
    
    # Display the conversation structure
    print(f"📝 Response: {response_content}")
    print(f"📊 MultiTurnSample created with {len(ragas_sample.user_input)} messages:")
    
    for i, msg in enumerate(ragas_sample.user_input):
        msg_type = type(msg).__name__
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {i+1}. {msg_type}: {content}")
        
        # Show tool calls if present (for AIMessage)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for j, tool_call in enumerate(msg.tool_calls):
                print(f"     🛠️  Tool {j+1}: {tool_call.name}({tool_call.args})")
    
    print("\n🔍 Running Ragas Evaluations...")
    
    # Set up evaluator LLM
    evaluator_llm = LlamaIndexLLMWrapper(OpenAI(model="gpt-4o-mini"))
    
    # 1. Agent Goal Accuracy (Without Reference)
    try:
        goal_accuracy_metric = AgentGoalAccuracyWithoutReference(llm=evaluator_llm)
        goal_score = await goal_accuracy_metric.multi_turn_ascore(ragas_sample)
        print(f"✅ Agent Goal Accuracy (No Ref): {goal_score}")
    except Exception as e:
        print(f"❌ Agent Goal Accuracy error: {e}")
    
    # 2. Agent Goal Accuracy (With Reference) - if reference provided
    if reference_answer:
        try:
            # Create sample with reference
            sample_with_ref = ragas_sample.model_copy()
            sample_with_ref.reference = reference_answer
            
            goal_accuracy_ref_metric = AgentGoalAccuracyWithReference(llm=evaluator_llm)
            goal_score_ref = await goal_accuracy_ref_metric.multi_turn_ascore(sample_with_ref)
            print(f"✅ Agent Goal Accuracy (With Ref): {goal_score_ref}")
        except Exception as e:
            print(f"❌ Agent Goal Accuracy (Ref) error: {e}")
    
    # 3. Tool Call Accuracy - if there are expected tool calls
    try:
        # Extract actual tool calls from the conversation
        actual_tool_calls = []
        for msg in ragas_sample.user_input:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                actual_tool_calls.extend(msg.tool_calls)
        
        if actual_tool_calls:
            # For this example, we'll assume the tool calls are correct
            # In practice, you'd define expected tool calls
            sample_with_tools = ragas_sample.model_copy()
            sample_with_tools.reference_tool_calls = actual_tool_calls
            
            tool_accuracy_metric = ToolCallAccuracy()
            tool_score = await tool_accuracy_metric.multi_turn_ascore(sample_with_tools)
            print(f"✅ Tool Call Accuracy: {tool_score}")
        else:
            print("ℹ️  No tool calls to evaluate")
            
    except Exception as e:
        print(f"❌ Tool Call Accuracy error: {e}")
    
    print(f"\n📋 Evaluation Summary:")
    print(f"   User Query: {user_msg}")
    print(f"   Agent Response: {response_content}")
    print(f"   Messages in Conversation: {len(ragas_sample.user_input)}")
    print(f"   Tool Calls Made: {sum(1 for msg in ragas_sample.user_input if hasattr(msg, 'tool_calls') and msg.tool_calls)}")

async def run_evaluation_examples():
    """Run multiple evaluation examples"""
    
    examples = [
        {
            "user_msg": "What time is it?",
            "reference": "The current time should be provided using the get_current_time function"
        },
        {
            "user_msg": "Hello, how are you?", 
            "reference": "A polite greeting response"
        },
        {
            "user_msg": "Can you tell me the exact time right now?",
            "reference": "The current time in YYYY-MM-DD HH:MM:SS format"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*60}")
        print(f"EXAMPLE {i}")
        print(f"{'='*60}")
        await evaluate_agent_with_ragas(
            example["user_msg"], 
            example.get("reference")
        )
        print("\n")

if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("❌ Please set your OPENAI_API_KEY in the .env file")
        exit(1)
    
    print("🚀 Starting Ragas Evaluation Examples with MultiTurnSample")
    asyncio.run(run_evaluation_examples()) 