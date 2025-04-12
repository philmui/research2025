import asyncio
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import streamlit as st
from openai import OpenAI
import time

from bioagents.webagent import ReflexiveAgent

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"

MODEL_DESCRIPTIONS = {
    "gpt-4o-mini": "gpt-4o-mini (Fast)",
    "gpt-4o": "gpt-4o (Capable)",
    "o3-mini": "o3-mini (Reasoning)",
    "thinking-agent": "Thinking Agent (Web Search)"
}

# Initialize model selection in session state if not present
if "agent_choice" not in st.session_state:
    st.session_state["agent_choice"] = DEFAULT_MODEL

with st.sidebar:
    "[Mui Group @ ASDRP](https://bit.ly/mui-group)"
    "[Research Repo](https://github.com/philmui/research2025)"
    st.divider()
    st.session_state.agent_choice = st.selectbox(
        "Choose Model:",
        ["gpt-4o-mini", "gpt-4o", "o3-mini", "thinking-agent"],
        help="Select the model to use for generating responses",
        format_func=lambda x: MODEL_DESCRIPTIONS[x]
    )

st.title("💬 Agent Reasoning Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not OPENAI_API_KEY:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    start_time = time.time()
    client = OpenAI(api_key=OPENAI_API_KEY)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message with right alignment
    user_message = st.chat_message("user", avatar="🧑")
    user_message.write(f'<div style="text-align: right;">{prompt}</div>', unsafe_allow_html=True)
    
    response_text = ""
    if st.session_state.agent_choice == "thinking-agent":
        agent = ReflexiveAgent()
        response = asyncio.run(agent.run(prompt))
        response_text = response.output
    
        if response.citations and len(response.citations) > 0:
            response_text += "\n__References__:"
            for citation in response.citations:
                response_text += f"\n- ({citation.title})[{citation.url}]"
    else:
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
    st.markdown(f'<div style="text-align: right; color: #888888; font-size: 0.8em; margin-top: -20px;">Response time: {response_time:.2f}s</div>', unsafe_allow_html=True)
    