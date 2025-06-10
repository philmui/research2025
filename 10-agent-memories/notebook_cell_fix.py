# Replace your failing Cell 3 with this code:

# Simple working solution - no external dependencies
vector_store = SimpleVectorStore()
print("✅ SimpleVectorStore created successfully!")
print("This replaces Qdrant and works immediately.")

# Optional: If you want to try Qdrant later, uncomment this fallback approach:
"""
# Fallback approach that tries Qdrant first, then SimpleVectorStore
try:
    # Try local Qdrant (if you have it running)
    import qdrant_client
    from qdrant_client.models import Distance, VectorParams
    
    q_client = qdrant_client.QdrantClient(host="localhost", port=6333)
    
    # Test connection
    collections = q_client.get_collections()
    print("✅ Local Qdrant is running!")
    
    # Create collection if needed
    if not q_client.collection_exists(COLLECTION_NAME):
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    
    # Create Qdrant vector store
    vector_store = QdrantVectorStore(
        client=q_client,
        embedding=embedding,
        collection_name=COLLECTION_NAME,
        parallel=8,
        enable_hybrid=False
    )
    print("✅ QdrantVectorStore (local) initialized!")
    
except Exception as e:
    print(f"❌ Qdrant not available: {e}")
    print("Using SimpleVectorStore fallback...")
    vector_store = SimpleVectorStore()
    print("✅ SimpleVectorStore initialized!")
""" 