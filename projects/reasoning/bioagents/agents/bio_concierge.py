#------------------------------------------------------------------------------
# bioreasoner.py
# 
# This is a "Bio Reasoning Agent" that triage across multiple agents to answer
# a user's question.  This agent orchestrates across the following subagents:
# 
# 1. Chit Chat Agent
# 2. Web Reasoning Agent
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------

from datetime import datetime
from loguru import logger

from bioagents.agents.base_agent import ReasoningAgent
from bioagents.agents.biomcp_agent import BioMCPAgent
from bioagents.agents.chitchat_agent import ChitChatAgent
from bioagents.agents.common import AgentResponse
from bioagents.models.llms import LLM
from bioagents.agents.web_agent import WebReasoningAgent

class BioConciergeAgent(ReasoningAgent):
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_NANO, 
    ):
        # Initialize sub-agents with lazy loading
        self.chit_chat_agent = ChitChatAgent(name="Chit Chat Agent")
        self.web_agent = WebReasoningAgent(name="Web Reasoning Agent")
        self.biomcp_agent = BioMCPAgent(name="Bio MCP Agent")
        
        instructions = (
            "You are a bio-reasoning agent that routes queries to appropriate specialists. "
            "You analyze the user's query and determine the best way to respond."
        )

        super().__init__(name, model_name, instructions)

    def _classify_query(self, query_str: str) -> str:
        """
        Classify the query to determine which agent should handle it.
        
        Returns:
            'biomcp' - for biomedical/scientific queries
            'web' - for general information/news queries  
            'chitchat' - for casual conversation
        """
        query_lower = query_str.lower()
        
        # Biomedical/scientific keywords
        bio_keywords = [
            'gene', 'protein', 'dna', 'rna', 'variant', 'mutation', 'disease', 'medicine',
            'drug', 'pharmaceutical', 'clinical', 'trial', 'pubmed', 'research', 'study',
            'biomedical', 'biological', 'genetics', 'genomics', 'cancer', 'tumor',
            'alzheimer', 'diabetes', 'heart', 'brain', 'cell', 'molecular', 'biochemistry',
            'rs123', 'rs113', 'pmid', 'doi', 'article', 'paper', 'journal', 'crispr'
        ]
        
        # Casual conversation keywords - check first (highest priority)
        chitchat_keywords = [
            'hello', 'hi', 'how are you', 'good morning', 'good evening', 'thanks', 'thank you',
            'bye', 'goodbye', 'see you', 'nice', 'great', 'awesome', 'cool', 'lol', 'haha',
            'how are you doing', 'how is it going', 'what\'s up', 'hey there'
        ]
        
        # Web/news keywords - check before biomedical
        web_keywords = [
            'news', 'latest', 'recent', 'current', 'today', 'yesterday', 'weather', 'stock',
            'market', 'price', 'trending', 'update', 'what happened', 'breaking', 'current events'
        ]
        
        # Check for chitchat first (highest priority for casual conversation)
        if any(keyword in query_lower for keyword in chitchat_keywords):
            return 'chitchat'
            
        # Check for web/news content (but not if it's biomedical news)
        if any(keyword in query_lower for keyword in web_keywords) and \
           not any(keyword in query_lower for keyword in bio_keywords):
            return 'web'
            
        # Check for biomedical content
        if any(keyword in query_lower for keyword in bio_keywords):
            return 'biomcp'
        
        # Default to biomedical for ambiguous queries (this is a bio-reasoning agent)
        return 'biomcp'

    async def achat(self, query_str: str) -> AgentResponse:
        logger.info(f"-> {self.name}: {query_str}")

        # Classify the query to determine which agent should handle it
        agent_type = self._classify_query(query_str)
        logger.info(f"Routing query to: {agent_type}")
        
        # Route to the appropriate agent with lazy initialization
        if agent_type == 'biomcp':
            return await self.biomcp_agent.achat(query_str)
        elif agent_type == 'web':
            return await self.web_agent.achat(query_str)
        elif agent_type == 'chitchat':
            return await self.chit_chat_agent.achat(query_str)
        else:
            # Fallback to biomcp for unknown types
            return await self.biomcp_agent.achat(query_str)

#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    import time
    
    start_time = time.time()
    agent = BioConciergeAgent(name="Bio")
    response = asyncio.run(agent.achat("How are you?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")
    
    start_time = time.time()
    response = asyncio.run(agent.achat("What is the latest news in the field of genetics?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")

    start_time = time.time()
    response = asyncio.run(agent.achat("How is the weather in Tokyo?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")