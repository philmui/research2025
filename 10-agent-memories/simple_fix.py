from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Initialize LLM and embedding
llm = OpenAI(model="gpt-4o-mini")
embedding = OpenAIEmbedding(model="text-embedding-3-small")

# Simple solution: Use SimpleVectorStore instead of Qdrant
vector_store = SimpleVectorStore()

print("✅ SimpleVectorStore created successfully!")
print("This is a reliable in-memory vector store that will work immediately.")

# Create tool
def get_weather(location: str) -> str:
    """Useful for getting the weather for a given location."""
    return f"The weather at {location} is very nice with not much rain."

tool = FunctionTool.from_defaults(get_weather)

# Create agent
agent = FunctionAgent(llm=llm, tools=[tool])

print("✅ Agent created successfully!")
print("\nNow you can use the agent:")
print("# response = await agent.run('How is the weather in Tokyo?')")
print("# print(response)")

# Export variables for use
globals().update({
    'vector_store': vector_store,
    'agent': agent,
    'llm': llm,
    'embedding': embedding,
    'tool': tool
}) 