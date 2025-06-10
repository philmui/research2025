import os
import qdrant_client
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Initialize LLM and embedding
llm = OpenAI(model="gpt-4o-mini")
embedding = OpenAIEmbedding(model="text-embedding-3-small")

COLLECTION_NAME = "memories_collection"

print("=== Setting up Vector Store ===")

# Try local Qdrant first (most reliable for development)
vector_store = None
try:
    # Create local Qdrant client
    q_client = qdrant_client.QdrantClient(host="localhost", port=6333)
    
    # Test connection
    print("Testing local Qdrant connection...")
    collections = q_client.get_collections()
    print("✅ Local Qdrant is running!")
    
    # Check if collection exists
    try:
        collection_exists = q_client.collection_exists(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' exists: {collection_exists}")
    except Exception as e:
        print(f"Error checking collection: {e}")
        collection_exists = False
    
    # Create collection if it doesn't exist
    if not collection_exists:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created successfully!")
    
    # Create vector store
    vector_store = QdrantVectorStore(
        client=q_client,
        embedding=embedding,
        collection_name=COLLECTION_NAME,
        parallel=8,
        enable_hybrid=False
    )
    print("✅ QdrantVectorStore initialized successfully!")
    
except Exception as e:
    print(f"❌ Local Qdrant not available: {e}")
    print("💡 To start local Qdrant: docker run -p 6333:6333 qdrant/qdrant")

# Fallback to SimpleVectorStore if Qdrant fails
if vector_store is None:
    print("\n=== Using SimpleVectorStore Fallback ===")
    from llama_index.core.vector_stores import SimpleVectorStore
    vector_store = SimpleVectorStore()
    print("✅ Using SimpleVectorStore (in-memory) as fallback")

print(f"\n=== Testing Vector Store ===")
print(f"Vector store type: {type(vector_store).__name__}")

# Set up memory system with correct imports
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory, InsertMethod
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    VectorMemoryBlock,  # Correct import name
)

# Create memory blocks
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
    VectorMemoryBlock(  # Correct class name
        name="knowledge_base",
        description="Useful for storing and retrieving information from a vector database.",
        priority=2,
        vector_store=vector_store,
    ),
]

# Create memory
memory = Memory.from_defaults(
    session_id="my_session", 
    memory_blocks=memory_blocks,
    token_limit=40000,
    chat_history_token_ratio=0.7,
    token_flush_size=10000,
    insert_method=InsertMethod.SYSTEM,
)

print("✅ Memory blocks configured successfully!")

# Create a simple tool for testing
from llama_index.core.tools import FunctionTool

def get_weather(location: str) -> str:
    """Useful for getting the weather for a given location."""
    return f"The weather at {location} is very nice with not much rain."

tool = FunctionTool.from_defaults(get_weather)

# Create agent
agent = FunctionAgent(llm=llm, tools=[tool])

print("✅ Agent created successfully!")
print("\n=== Setup Complete ===")
print("You can now use:")
print("- vector_store")
print("- memory")  
print("- agent")
print("\nExample usage:")
print("response = await agent.run('How is the weather in Tokyo?', memory=memory)")

# Export for use in notebook
globals().update({
    'vector_store': vector_store,
    'memory': memory,
    'agent': agent,
    'llm': llm,
    'embedding': embedding,
}) 