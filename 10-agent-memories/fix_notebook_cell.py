# Fix for the failing notebook cell
# Copy and paste this code into your notebook cell to fix the errors

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory, InsertMethod
from llama_index.core.memory import (
    StaticMemoryBlock,
    FactExtractionMemoryBlock,
    # VectorMemoryBlock,  # Commented out - SimpleVectorStore doesn't support stores_text
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

# Create memory blocks list without VectorMemoryBlock for now
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

# Next cell - Test the agent
# response = await agent.run("How is the weather in Tokyo?", memory=memory)
# print(response) 