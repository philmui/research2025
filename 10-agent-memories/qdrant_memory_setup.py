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

# Get environment variables
QDRANT_HOSTED_URL = os.environ.get("QDRANT_HOSTED_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", 6333)

COLLECTION_NAME = "memories_collection"

print(f"Qdrant URL length: {len(QDRANT_HOSTED_URL)}")
print(f"Qdrant API Key length: {len(QDRANT_API_KEY)}")
print(f"Qdrant Port: {QDRANT_PORT}")

# Create Qdrant client
q_client = qdrant_client.QdrantClient(
    url=QDRANT_HOSTED_URL,
    api_key=QDRANT_API_KEY,
)

# Check if collection exists, create if it doesn't
try:
    collection_exists = q_client.collection_exists(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' exists: {collection_exists}")
except Exception as e:
    print(f"Error checking collection existence: {e}")
    collection_exists = False

if not collection_exists:
    print(f"Creating collection '{COLLECTION_NAME}'...")
    try:
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),  # text-embedding-3-small has 1536 dimensions
        )
        print(f"Collection '{COLLECTION_NAME}' created successfully!")
    except Exception as e:
        print(f"Error creating collection: {e}")
        raise e

# Now create the vector store
try:
    vector_store = QdrantVectorStore(
        client=q_client,
        embedding=embedding,
        collection_name=COLLECTION_NAME,
        parallel=8,
        enable_hybrid=False
    )
    print("QdrantVectorStore initialized successfully!")
except Exception as e:
    print(f"Error initializing QdrantVectorStore: {e}")
    raise e

# Test the connection
try:
    # Get collection info
    collection_info = q_client.get_collection(COLLECTION_NAME)
    print(f"Collection info: {collection_info}")
except Exception as e:
    print(f"Error getting collection info: {e}") 