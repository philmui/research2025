"""
Pytest module for asdrp.agent.reductive_agent.ReductiveAgent
Focus: PropositionExtractionMemoryBlock integration and behavior.
"""
import pytest
from asdrp.agent.reductive_agent import ReductiveAgent as ReductiveAgent, AgentReply
from asdrp.memory.proposition_extraction_memory import PropositionExtractionMemoryBlock
from llama_index.core.memory import Memory
from llama_index.llms.openai import OpenAI
import re

@pytest.fixture(scope="module")
def llm():
    """Fixture for a shared LLM instance."""
    return OpenAI(model="gpt-4.1-mini")

@pytest.fixture
def memory_with_proposition_block(llm):
    """Fixture for a Memory instance with a PropositionExtractionMemoryBlock."""
    block = PropositionExtractionMemoryBlock(
        name="proposition_extraction_memory",
        llm=llm,
        max_propositions=10,
    )
    return Memory.from_defaults(
        session_id="test_session",
        token_limit=50,
        memory_blocks=[block],
    )

class BaseTestReductiveAgent:
    """Base test class for ReductiveAgent and proposition memory logic."""
    @staticmethod
    def create_agent(llm=None, memory=None, tools=None):
        return ReductiveAgent(llm=llm or OpenAI(model="gpt-4.1-mini"), memory=memory, tools=tools or [])

    @staticmethod
    def get_proposition_block(memory):
        for block in getattr(memory, "memory_blocks", []):
            if isinstance(block, PropositionExtractionMemoryBlock):
                return block
        return None

    @staticmethod
    def extract_propositions(props: str):
        """Extract proposition text from XML string."""
        return [match.strip().lower().rstrip('.') for match in re.findall(r"<proposition>(.*?)</proposition>", props, re.DOTALL)]

class TestReductiveAgent(BaseTestReductiveAgent):
    """
    Comprehensive tests for ReductiveAgent with proposition extraction memory.
    """
    @pytest.mark.asyncio
    async def test_proposition_extraction(self, llm, memory_with_proposition_block):
        """
        Test that propositions are extracted and stored from user input.
        """
        agent = self.create_agent(llm=llm, memory=memory_with_proposition_block)
        await agent.achat("I believe the sky is blue.")
        block = self.get_proposition_block(memory_with_proposition_block)
        props = await block._aget()
        assert "sky is blue" in props or "Sky is blue" in props

    @pytest.mark.asyncio
    async def test_proposition_deduplication(self, llm, memory_with_proposition_block):
        """
        Test that duplicate propositions are not stored multiple times.
        """
        agent = self.create_agent(llm=llm, memory=memory_with_proposition_block)
        await agent.achat("I believe the sky is blue.")
        await agent.achat("I believe the sky is blue.")
        block = self.get_proposition_block(memory_with_proposition_block)
        props = await block._aget()
        # Should only appear once
        count = props.count("sky is blue") + props.count("Sky is blue")
        assert count == 1

    @pytest.mark.asyncio
    async def test_multiple_propositions(self, llm, memory_with_proposition_block):
        """
        Test that multiple distinct propositions are extracted and stored.
        """
        agent = self.create_agent(llm=llm, memory=memory_with_proposition_block)
        await agent.achat("The sky is blue. Water is wet.")
        block = self.get_proposition_block(memory_with_proposition_block)
        props = await block._aget()
        extracted = self.extract_propositions(props)
        assert any("sky is blue" in p for p in extracted)
        assert any("water is wet" in p for p in extracted)

    @pytest.mark.asyncio
    async def test_proposition_limit(self, llm):
        """
        Test that the max_propositions limit is respected.
        The LLM may return fewer than the limit if it merges or drops facts.
        """
        block = PropositionExtractionMemoryBlock(
            name="proposition_extraction_memory",
            llm=llm,
            max_propositions=2,
        )
        memory = Memory.from_defaults(
            session_id="test_session",
            token_limit=50,
            memory_blocks=[block],
        )
        agent = self.create_agent(llm=llm, memory=memory)
        await agent.achat("Fact one.")
        await agent.achat("Fact two.")
        await agent.achat("Fact three.")
        props = await block._aget()
        num_props = props.count("<proposition>")
        # Accept 1 or 2, since the LLM may merge facts
        assert 1 <= num_props <= 2
        extracted = self.extract_propositions(props)
        assert any("fact three" in p for p in extracted)

    @pytest.mark.asyncio
    async def test_agent_reply_includes_propositions(self, llm, memory_with_proposition_block):
        """
        Test that the agent can reference extracted propositions in its reply.
        """
        agent = self.create_agent(llm=llm, memory=memory_with_proposition_block)
        await agent.achat("I believe the sky is blue.")
        reply = await agent.achat("What do you know about the sky?")
        assert isinstance(reply, AgentReply)
        # The reply should reference the extracted proposition
        assert "sky is blue" in reply.response_str or "Sky is blue" in reply.response_str 