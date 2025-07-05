"""
Pytest module for asdrp.agent.summary_agent.SummaryAgent

This module provides comprehensive smoke and functional tests for the SummaryAgent class,
covering chat, memory, tool integration, and error handling. It uses DRY, SOLID, and OOP best practices.
"""
import pytest
from asdrp.agent.summary_agent import SummaryAgent, AgentReply
from llama_index.core.memory import Memory
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM

@pytest.fixture(scope="module")
def llm():
    """Fixture for a shared LLM instance."""
    return OpenAI(model="gpt-4.1-mini")

@pytest.fixture
def memory():
    """Fixture for a fresh Memory instance for each test."""
    return Memory.from_defaults(session_id="pytest_session", token_limit=50)

class BaseTestSummaryAgent:
    """
    Base test class for SummaryAgent. Provides utility methods for agent setup and assertions.
    """
    @staticmethod
    def create_agent(llm=None, memory=None, tools=None):
        return SummaryAgent(llm=llm or OpenAI(model="gpt-4.1-mini"), memory=memory, tools=tools or [])

    @staticmethod
    def assert_reply(reply, expected_type=AgentReply):
        assert isinstance(reply, expected_type), f"Reply is not of type {expected_type}"
        assert hasattr(reply, "response_str"), "Reply missing 'response_str' attribute"
        assert isinstance(reply.response_str, str), "response_str is not a string"

class TestSummaryAgent(BaseTestSummaryAgent):
    """
    Comprehensive tests for SummaryAgent.
    """
    @pytest.mark.asyncio
    async def test_basic_chat(self, llm):
        """
        Test that the agent can respond to a simple message.
        """
        agent = self.create_agent(llm=llm)
        reply = await agent.achat("Hello, agent!")
        self.assert_reply(reply)
        assert "assistant" in reply.response_str.lower() or reply.response_str.strip(), "Reply should not be empty."

    @pytest.mark.asyncio
    async def test_memory_persistence(self, llm, memory):
        """
        Test that the agent's memory stores messages after a chat.
        """
        agent = self.create_agent(llm=llm, memory=memory)
        await agent.achat("Remember this: The sky is blue.")
        mem_items = list(memory.get_all())
        assert len(mem_items) > 0, "Memory should store at least one item after chat."

    @pytest.mark.asyncio
    async def test_custom_tool_invocation(self, llm):
        """
        Test that a custom tool can be registered and invoked by the agent.
        """
        def echo_tool(input_str: str) -> str:
            return f"Echo: {input_str}"
        tool = FunctionTool.from_defaults(fn=echo_tool, name="echo_tool", description="Echo the input string")
        agent = self.create_agent(llm=llm, tools=[tool])
        reply = await agent.achat("Call the echo_tool with input_str='test123'")
        self.assert_reply(reply)
        assert "Echo" in reply.response_str, f"Custom tool reply should contain 'Echo', got: {reply.response_str}"

    @pytest.mark.asyncio
    async def test_error_handling(self, llm):
        """
        Test that the agent handles errors gracefully and returns a fallback message.
        """
        from llama_index.core.llms import LLM
        class BrokenLLM(LLM):
            async def achat(self, *args, **kwargs):
                raise RuntimeError("LLM failure")
            async def acomplete(self, *args, **kwargs):
                raise NotImplementedError()
            async def astream_chat(self, *args, **kwargs):
                raise NotImplementedError()
            async def astream_complete(self, *args, **kwargs):
                raise NotImplementedError()
            def chat(self, *args, **kwargs):
                raise NotImplementedError()
            def complete(self, *args, **kwargs):
                raise NotImplementedError()
            @property
            def metadata(self):
                return {}
            def stream_chat(self, *args, **kwargs):
                raise NotImplementedError()
            def stream_complete(self, *args, **kwargs):
                raise NotImplementedError()
            def __init__(self):
                super().__init__()
        agent = self.create_agent(llm=BrokenLLM())
        reply = await agent.achat("This should fail.")
        self.assert_reply(reply)
        assert "trouble processing" in reply.response_str or "error" in reply.response_str.lower(), "Agent should return error message." 