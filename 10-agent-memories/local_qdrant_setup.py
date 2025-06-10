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

print("=== Setting up Local Qdrant ===")

# Try local Qdrant first (most reliable for development)
try:
    # Create local Qdrant client
    q_client = qdrant_client.QdrantClient(host="localhost", port=6333)
    
    # Test connection
    print("Testing local Qdrant connection...")
    collections = q_client.get_collections()
    print("✅ Local Qdrant is running!")
    use_local = True
    
except Exception as e:
    print(f"❌ Local Qdrant not available: {e}")
    print("💡 To start local Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    use_local = False

if not use_local:
    print("\n=== Falling back to SimpleVectorStore ===")
    # Fallback to SimpleVectorStore (in-memory)
    from llama_index.core.vector_stores import SimpleVectorStore
    vector_store = SimpleVectorStore()
    print("✅ Using SimpleVectorStore (in-memory) as fallback")
else:
    # Use local Qdrant
    print(f"\n=== Setting up Qdrant Collection: {COLLECTION_NAME} ===")
    
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
        try:
            q_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            print(f"✅ Collection '{COLLECTION_NAME}' created successfully!")
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            raise e
    
    # Create vector store
    try:
        vector_store = QdrantVectorStore(
            client=q_client,
            embedding=embedding,
            collection_name=COLLECTION_NAME,
            parallel=8,
            enable_hybrid=False
        )
        print("✅ QdrantVectorStore initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing QdrantVectorStore: {e}")
        raise e

# Test the vector store
print(f"\n=== Testing Vector Store ===")
print(f"Vector store type: {type(vector_store).__name__}")

# Example usage with memory blocks
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    VectorStoreMemoryBlock,
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
    VectorStoreMemoryBlock(
        name="knowledge_base",
        description="Useful for storing and retrieving information from a vector database.",
        priority=2,
        vector_store=vector_store,
    ),
]

print("✅ Memory blocks configured successfully!")
print("\n=== Setup Complete ===")
print("You can now use the vector_store and memory_blocks in your notebook!") 