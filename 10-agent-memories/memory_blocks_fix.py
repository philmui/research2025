from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory, InsertMethod
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    VectorMemoryBlock,  # Note: it's VectorMemoryBlock, not VectorStoreMemoryBlock
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
    VectorMemoryBlock(  # Fixed: was VectorStoreMemoryBlock
        name="knowledge_base",
        description="Useful for storing and retrieving information from a vector database.",
        priority=2,
        vector_store=vector_store,  # Fixed: added missing vector_store parameter
    ),
]

memory = Memory.from_defaults(
    session_id="my_session", 
    memory_blocks=memory_blocks,  # Fixed: added missing memory_blocks parameter
    token_limit=40000,
    chat_history_token_ratio=0.7,
    token_flush_size=10000,
    insert_method=InsertMethod.SYSTEM,
)

agent = FunctionAgent(llm=llm, tools=[tool])

print("✅ Memory and agent configured successfully!") 