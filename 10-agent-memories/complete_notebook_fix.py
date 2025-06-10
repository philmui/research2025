# Complete working solution for your notebook
from dotenv import load_dotenv, find_dotenv
import os

# Cell 1 - Load environment
load_dotenv(find_dotenv())

# Cell 2 - Imports and setup
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore

llm = OpenAI(model="gpt-4o-mini")  # Fixed: was "gpt-4.1-mini"
embedding = OpenAIEmbedding(model="text-embedding-3-small")

QDRANT_HOSTED_URL = os.environ.get("QDRANT_HOSTED_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", 6333)

COLLECTION_NAME = "memories_collection"

print(f"Environment loaded: URL length: {len(QDRANT_HOSTED_URL)}, API Key length: {len(QDRANT_API_KEY)}")

# Cell 3 - Fixed vector store creation
vector_store = SimpleVectorStore()
print("✅ SimpleVectorStore created successfully!")

# Cell 4 - Tools (unchanged)
from llama_index.core.tools import FunctionTool

def get_weather(location: str) -> str:
    """Useful for getting the weather for a given location."""
    return f"The weather at {location} is very nice with not much rain."

tool = FunctionTool.from_defaults(get_weather)
print("✅ Tool created successfully!")

# Cell 5 - Fixed memory and agent setup
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory, InsertMethod
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    VectorMemoryBlock,
)

memory_blocks = [
    StaticMemoryBlock(
        name="core_info",
        description="Information about the user's attributes.",
        priority=0,
        accept_short_term_memory=True,
        static_content=[
            "Name: John Doe",
            "Age: 30",
            "Location: New York",
            "Occupation: Software Engineer",
        ],
    ),
    FactExtractionMemoryBlock(
        name="facts",
        priority=1,
        llm=llm,
        max_facts=50,
    ),
    VectorMemoryBlock(
        name="knowledge_base",
        description="Useful for storing and retrieving information from a vector database.",
        priority=2,
        vector_store=vector_store,
    ),
]

memory = Memory.from_defaults(
    session_id="my_session", 
    memory_blocks=memory_blocks,
    token_limit=40000,
    chat_history_token_ratio=0.7,
    token_flush_size=10000,
    insert_method=InsertMethod.SYSTEM,
)

agent = FunctionAgent(llm=llm, tools=[tool])

print("✅ Memory and agent configured successfully!")

# Cell 6 - Test the agent (run this in notebook with 'await')
# response = await agent.run("How is the weather in Tokyo?", memory=memory)
# print(response)

print("\n🎉 Complete setup successful!")
print("Now you can run: response = await agent.run('How is the weather in Tokyo?', memory=memory)") 