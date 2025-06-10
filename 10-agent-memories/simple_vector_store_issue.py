# Why SimpleVectorStore(stores_text=True) doesn't work
# =====================================================

"""
The issue with your approach:

vector_store = SimpleVectorStore(stores_text=True)

is that SimpleVectorStore doesn't accept a `stores_text` parameter in its constructor.
The `stores_text` property is an internal attribute that the VectorMemoryBlock validator checks.

Looking at the VectorMemoryBlock validation:
```python
if not v.stores_text:
    raise ValueError("vector_store must store text to be used as a retrieval memory block")
```

SimpleVectorStore apparently doesn't have `stores_text=True` set internally.
"""

# Alternative Solutions:
# =====================

# Option 1: Skip VectorMemoryBlock (simplest)
from llama_index.core.vector_stores import SimpleVectorStore

vector_store = SimpleVectorStore()  # Don't pass stores_text=True
# But don't use this with VectorMemoryBlock - it will fail

# Option 2: Use a different vector store that supports stores_text
# Most external vector stores like Qdrant, Chroma, etc. support this

# Option 3: Use QdrantVectorStore (recommended if you want VectorMemoryBlock)
"""
# Start Qdrant: docker run -p 6333:6333 qdrant/qdrant
import qdrant_client
from qdrant_client.models import Distance, VectorParams
from llama_index.vector_stores.qdrant import QdrantVectorStore

q_client = qdrant_client.QdrantClient(host="localhost", port=6333)

if not q_client.collection_exists("memories_collection"):
    q_client.create_collection(
        collection_name="memories_collection",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

vector_store = QdrantVectorStore(
    client=q_client,
    collection_name="memories_collection",
    embedding=embedding,
)

# This vector_store WILL work with VectorMemoryBlock
"""

# Option 4: Just fix your current code by removing VectorMemoryBlock
print("Use the code from vector_block_fix.py - Solution 1 for the simplest fix") 