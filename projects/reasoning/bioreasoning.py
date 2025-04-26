#------------------------------------------------------------------------------
# bioreasoning.py
# 
# This is the main web app for the BioReasoning Project. It allows users to
# interact with the BioReasoning Agent and its sub-agents.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------


from dotenv import load_dotenv, find_dotenv
import streamlit as st
from openai import OpenAI
import os
import asyncio
from bioagents.models.llms import LLM
from bioagents.agents.base import AgentResponse
from bioagents.agents.bioreasoner import BioReasoningAgent
from bioagents.agents.chitchat_agent import ChitChatAgent
from bioagents.agents.webreasoner import WebReasoningAgent

load_dotenv(find_dotenv())
st.set_page_config(
    page_title="BioReasoning Agent",
    page_icon="🧬",
    layout="wide"
)

# Initialize LLM client in session state if not already present
if "llm_client" not in st.session_state:
    st.session_state.llm_client = LLM(model=LLM.GPT_4_1_NANO)
if "reasoner" not in st.session_state:
    st.session_state.reasoner = BioReasoningAgent(name="Bio Reasoner")

#------------------------------------------------
# Sidebar for user customizations
#------------------------------------------------
with st.sidebar:
    st.title("Settings")
    st.write("Ask me anything about medicine, genetics, drug design, and clinical trials!")

    model_options = {
        "GPT-4.1 Mini": LLM.GPT_4_1_MINI,
        "GPT-4.1 Nano": LLM.GPT_4_1_NANO,
        "GPT-4.1": LLM.GPT_4_1,
        "GPT-4o": LLM.GPT_4O
    }
    
    model_selection = st.selectbox(
        "Select LLM Model",
        list(model_options.keys()),
        index=0  # Default to GPT-4.1 Mini
    )
    
    # Update the model in the LLM client when changed
    model = model_options[model_selection]
    if st.session_state.llm_client._model != model:
        st.session_state.llm_client._model = model

#------------------------------------------------
# Main app interface
#------------------------------------------------
st.title("BioReasoning Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "citations" in message and message["citations"]:
            with st.expander("Citations", expanded=False):
                for citation in message["citations"]:
                    st.markdown(f"[{citation.title}]({citation.url})")
                    if citation.snippet:
                        st.markdown(f"{citation.snippet}")
                    st.markdown("---")

if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("agent"):
        with st.spinner("Thinking..."):
            reasoner = st.session_state.reasoner
            agent_response: AgentResponse = asyncio.run(reasoner.achat(prompt))
            st.write(agent_response.response_str)
            
            if agent_response.citations:
                with st.expander("## Citations", expanded=False):
                    for i, citation in enumerate(agent_response.citations):
                        st.markdown(f"**{i+1}.**  [{citation.title}]({citation.url})")

            st.session_state.messages.append(
                {
                    "role": "assistant", 
                    "content": agent_response.response_str,
                    "citations": agent_response.citations,
                    "route": agent_response.route
                }
            )
