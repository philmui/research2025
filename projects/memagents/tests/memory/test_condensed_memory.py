"""
Pytest module for asdrp.memory.condensed_memory.CondensedMemoryBlock

This module provides comprehensive tests for the CondensedMemoryBlock class,
covering memory storage, token limit enforcement, and tool call handling.
"""
import pytest
import tiktoken
from asdrp.memory.condensed_memory import CondensedMemoryBlock
from llama_index.core.llms import ChatMessage, TextBlock

@pytest.fixture
def token_limit():
    """Fixture for a small token limit to test trimming."""
    return 10

@pytest.fixture
def memory_block(token_limit):
    """Fixture for a fresh CondensedMemoryBlock instance for each test."""
    return CondensedMemoryBlock(name="test_block", token_limit=token_limit)

class BaseTestCondensedMemoryBlock:
    """
    Base test class for CondensedMemoryBlock. Provides utility methods for message creation and assertions.
    """
    @staticmethod
    def make_message(text, **kwargs):
        return ChatMessage(blocks=[TextBlock(text=text)], additional_kwargs=kwargs)

    @staticmethod
    async def get_memory_contents(block):
        return await block._aget()

class TestCondensedMemoryBlock(BaseTestCondensedMemoryBlock):
    """
    Comprehensive tests for CondensedMemoryBlock.
    """
    @pytest.mark.asyncio
    async def test_single_message_storage(self, memory_block):
        """
        Test that a single message is stored in memory.
        """
        msg = self.make_message("Hello, world!")
        await memory_block._aput([msg])
        contents = await self.get_memory_contents(memory_block)
        assert "Hello, world!" in contents

    @pytest.mark.asyncio
    async def test_multiple_message_storage(self, memory_block):
        """
        Test that multiple messages are stored in memory.
        """
        msgs = [self.make_message(f"msg{i}") for i in range(3)]
        await memory_block._aput(msgs)
        contents = await self.get_memory_contents(memory_block)
        for i in range(3):
            assert f"msg{i}" in contents

    @pytest.mark.asyncio
    async def test_token_limit_trimming(self, token_limit):
        """
        Test that memory is trimmed when token limit is exceeded.
        """
        block = CondensedMemoryBlock(name="trim_test", token_limit=5)
        # Add enough messages to exceed the token limit
        for i in range(10):
            msg = self.make_message(f"msg{i}")
            await block._aput([msg])
        contents = await self.get_memory_contents(block)
        # The last message should always be present
        assert "msg9" in contents, f"msg9 should be present. Contents: {contents}"
        # The first message should always be trimmed
        assert "msg0" not in contents, f"msg0 should have been trimmed. Contents: {contents}"
        # The number of messages present should be <= token_limit
        present_msgs = [f"msg{i}" for i in range(10) if f"msg{i}" in contents]
        assert len(present_msgs) <= 5, f"Too many messages present: {present_msgs}. Contents: {contents}"

    @pytest.mark.asyncio
    async def test_tool_call_handling(self, memory_block):
        """
        Test that tool call kwargs are included in memory.
        """
        # Use a higher token limit to ensure message is stored
        block = CondensedMemoryBlock(name="tool_call_test", token_limit=100)
        tool_call = {"function": {"name": "search", "arguments": {"q": "test"}}}
        msg = self.make_message("Tool call message", tool_calls=[tool_call], irrelevant="should be included")
        await block._aput([msg])
        contents = await self.get_memory_contents(block)
        assert "Tool call message" in contents
        assert "search" in contents
        assert "irrelevant" in contents 