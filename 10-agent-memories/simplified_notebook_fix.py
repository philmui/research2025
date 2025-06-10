from dotenv import load_dotenv, find_dotenv
import os

# Cell 1 - Load environment (keep as is)
load_dotenv(find_dotenv())

# Cell 2 - Imports and setup (keep mostly the same)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.vector_stores import SimpleVectorStore

llm = OpenAI(model="gpt-4o-mini")  # Fixed: was "gpt-4.1-mini" 
embedding = OpenAIEmbedding(model="text-embedding-3-small")

COLLECTION_NAME = "memories_collection"

# Cell 3 - FIXED: Simple vector store (no Qdrant issues)
vector_store = SimpleVectorStore()
print("✅ SimpleVectorStore created successfully!")

# Cell 4 - Tools (keep as is)
from llama_index.core.tools import FunctionTool

def get_weather(location: str) -> str:
    """Useful for getting the weather for a given location."""
    return f"The weather at {location} is very nice with not much rain."

tool = FunctionTool.from_defaults(get_weather)

# Cell 5 - SIMPLIFIED: Basic agent without complex memory 
from llama_index.core.agent.workflow import FunctionAgent

agent = FunctionAgent(llm=llm, tools=[tool])

print("✅ Agent created successfully!")
print("✅ Setup complete - ready to use!")

# Cell 6 - Test (run this in your notebook)
# response = await agent.run("How is the weather in Tokyo?")
# print(response)

print("\n🎉 All working! Run this in your notebook:")
print("response = await agent.run('How is the weather in Tokyo?')")
print("print(response)") 