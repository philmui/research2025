from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory, InsertMethod
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    # VectorMemoryBlock,  # Skip for now - SimpleVectorStore doesn't support stores_text
)

# Fixed StaticMemoryBlock with required parameters
static_memory_block = StaticMemoryBlock(
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
)

fact_extraction_memory_block = FactExtractionMemoryBlock(
    name="facts",
    priority=1,
    llm=llm,
    max_facts=50,
)

# Create memory blocks list (without VectorMemoryBlock for now)
memory_blocks = [
    static_memory_block,
    fact_extraction_memory_block,
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
print("Note: VectorMemoryBlock is skipped because SimpleVectorStore doesn't support stores_text")

# ============================================================================
# Solution 2: Complete Fix with QdrantVectorStore (if you have Qdrant running)
# ============================================================================

"""
# If you want to use VectorMemoryBlock, you need a vector store that supports stores_text=True
# Here's how to set up QdrantVectorStore:

# First, start local Qdrant:
# docker run -p 6333:6333 qdrant/qdrant

# Then use this code instead:
import qdrant_client
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "memories_collection"

try:
    # Create local Qdrant client
    q_client = qdrant_client.QdrantClient(host="localhost", port=6333)
    
    # Check if collection exists
    if not q_client.collection_exists(COLLECTION_NAME):
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    
    # Create QdrantVectorStore (this supports stores_text=True)
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    vector_store = QdrantVectorStore(
        client=q_client,
        collection_name=COLLECTION_NAME,
        embedding=embedding,
    )
    
    # Now you can create VectorMemoryBlock
    from llama_index.core.memory import VectorMemoryBlock
    vector_memory_block = VectorMemoryBlock(
        name="knowledge_base",
        description="Useful for storing and retrieving information from a vector database.",
        priority=2,
        vector_store=vector_store,
        embed_model=embedding,
        similarity_top_k=2,
    )
    
    # Add it to memory blocks
    memory_blocks = [
        static_memory_block,
        fact_extraction_memory_block,
        vector_memory_block,  # Now this works!
    ]
    
    print("✅ QdrantVectorStore with VectorMemoryBlock configured successfully!")
    
except Exception as e:
    print(f"❌ Qdrant not available: {e}")
    print("Falling back to SimpleVectorStore without VectorMemoryBlock")
    # Use the memory_blocks from Solution 1 above
""" 