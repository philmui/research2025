#########################################################################
# thinking_streamlit.py
#
# A streamlit app for the thinking agent.
#
# Author: Phil Mui
# Date: 2025-04-19
#########################################################################

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import streamlit as st
from openai import OpenAI
import time

from bioagents.webagent import ThinkingAgent
from bioagents.base import DEFAULT_THINKING_MODEL

USER_AVATAR = "https://api.dicebear.com/7.x/bottts/svg?seed=friend"

# Initialize the ReflexiveAgent as a singleton in session state
if "thinking_agent" not in st.session_state:
    st.session_state.thinking_agent = ThinkingAgent()
    print("Initialized ReflexiveAgent singleton")


#--------------------------------------------------
# Sidebar setup
#--------------------------------------------------

MODEL_DESCRIPTIONS = {
    "thinking-agent": "Thinking Agent (Reflexive)",
    "gpt-4.1-nano": "gpt-4.1-nano (Fast)",
    "gpt-4.1": "gpt-4.1 (Capable)",
    "o4-mini": "o4-mini (Reasoning)",
}

# Initialize model selection in session state if not present
if "agent_choice" not in st.session_state:
    st.session_state["agent_choice"] = DEFAULT_THINKING_MODEL

with st.sidebar:
    "[Mui Group @ ASDRP](https://bit.ly/mui-group)"
    "[Research Repo](https://github.com/philmui/research2025)"
    st.divider()
    st.session_state.agent_choice = st.selectbox(
        "Choose Model:",
        MODEL_DESCRIPTIONS.keys(),
        help="Select the model to use for generating responses",
        format_func=lambda x: MODEL_DESCRIPTIONS[x]
    )


#-------------------------------------------------- 
# Main content
#--------------------------------------------------

st.title("💬 Agent Reasoning Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Display message history with right alignment for user messages
for msg in st.session_state.messages:
    # Handle different styling for user vs assistant messages
    if msg["role"] == "user":
        # Create columns for user message - reverse order for right-side avatar
        cols = st.columns([0.85, 0.15])  # Avatar on right
        with cols[0]:  # Text column
            st.markdown(f'<div style="width:100%; text-align:right; padding-right:10px;">{msg["content"]}</div>', unsafe_allow_html=True)
        with cols[1]:  # Avatar column
            st.image(USER_AVATAR, width=40)
    else:
        # Normal display for assistant messages
        message = st.chat_message(msg["role"])
        message.write(msg["content"])


#-------------------------------------------------- 
# Chat input
#--------------------------------------------------

if prompt := st.chat_input():
    start_time = time.time()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message with avatar on right
    cols = st.columns([0.85, 0.15])  # Avatar on right
    with cols[0]:  # Text column
        st.markdown(f'<div style="width:100%; text-align:right; padding-right:10px;">{prompt}</div>', unsafe_allow_html=True)
    with cols[1]:  # Avatar column
        st.image(USER_AVATAR, width=40)
    
    response_text = ""
    if st.session_state.agent_choice == "thinking-agent":
        agent = st.session_state.thinking_agent
        response = asyncio.run(agent.run(prompt))
        response_text = response.output
    else:
        client = OpenAI()
        response = client.chat.completions.create(
            model=st.session_state.agent_choice,
            messages=st.session_state.messages
        )
        response_text = response.choices[0].message.content
        
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.chat_message("assistant").write(response_text)
    
    # Calculate and display response time
    end_time = time.time()
    response_time = end_time - start_time
    st.markdown(f'<div style="text-align: right; color: #888888; font-size: 0.8em; margin-top: -20px;">Response time: {response_time:.2f}s</div>', 
                unsafe_allow_html=True)
    