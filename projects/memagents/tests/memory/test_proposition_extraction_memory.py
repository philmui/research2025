"""
Pytest module for asdrp.memory.proposition_extraction_memory.PropositionExtractionMemoryBlock

This module provides comprehensive tests for the PropositionExtractionMemoryBlock class,
covering proposition extraction, duplicate filtering, and XML parsing.
"""
import pytest
from asdrp.memory.proposition_extraction_memory import PropositionExtractionMemoryBlock
from llama_index.core.llms import ChatMessage, TextBlock
from llama_index.llms.openai import OpenAI

@pytest.fixture
def llm():
    """Fixture for a shared LLM instance."""
    return OpenAI(model="gpt-4.1-mini")

@pytest.fixture
def memory_block(llm):
    """Fixture for a fresh PropositionExtractionMemoryBlock instance for each test."""
    return PropositionExtractionMemoryBlock(llm=llm, max_propositions=5)

class BaseTestPropositionExtractionMemoryBlock:
    """
    Base test class for PropositionExtractionMemoryBlock. Provides utility methods for message creation and assertions.
    """
    @staticmethod
    def make_message(text):
        return ChatMessage(blocks=[TextBlock(text=text)], additional_kwargs={})

class TestPropositionExtractionMemoryBlock(BaseTestPropositionExtractionMemoryBlock):
    """
    Comprehensive tests for PropositionExtractionMemoryBlock.
    """
    @pytest.mark.asyncio
    async def test_proposition_extraction(self, memory_block):
        """
        Test that propositions are extracted from a message.
        """
        msg = self.make_message("I believe the sky is blue.")
        await memory_block._aput([msg])
        contents = await memory_block._aget()
        assert "proposition" in contents
        assert "sky is blue" in contents or "Sky is blue" in contents

    @pytest.mark.asyncio
    async def test_duplicate_filtering(self, memory_block):
        """
        Test that duplicate propositions are not added.
        """
        msg1 = self.make_message("I believe the sky is blue.")
        msg2 = self.make_message("I believe the sky is blue.")
        await memory_block._aput([msg1])
        await memory_block._aput([msg2])
        contents = await memory_block._aget()
        # Should only appear once
        assert contents.count("proposition") == 1 or contents.lower().count("sky is blue") == 1

    def test_parse_propositions_xml(self, memory_block):
        """
        Test the XML parsing utility for extracting propositions.
        """
        xml = """
        <proposition>The sky is blue.</proposition>
        <proposition>Water is wet.</proposition>
        """
        props = memory_block._parse_propositions_xml(xml)
        assert "The sky is blue." in props
        assert "Water is wet." in props 