import asyncio
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import streamlit as st
from openai import OpenAI
import time

from bioagents.reflexive_agent import ReflexiveAgent
from bioagents.base import DEFAULT_THINKING_MODEL, AgentResponse

FRIEND_AVATAR = "https://api.dicebear.com/7.x/bottts/svg?seed=friend"

# Initialize the ReflexiveAgent as a singleton in session state
if "reflexive_agent" not in st.session_state:
    st.session_state.reflexive_agent = ReflexiveAgent()
    print("Initialized ReflexiveAgent singleton")


#--------------------------------------------------
# Utility functions
#--------------------------------------------------

def render_evaluation_details(message, judge_data):
    """Render the evaluation details in a collapsible section"""
    with message.expander("View Evaluation", expanded=False):
        # Score with colored background based on value
        score = judge_data.score
        score_color = "#5FD068" if score >= 0.7 else "#F7DC6F" if score >= 0.4 else "#FF6B6B"
        st.markdown(f"<div style='background-color:{score_color}; padding:10px; border-radius:5px;'><b>Score:</b> {score:.2f}</div>", unsafe_allow_html=True)
        
        # Critique
        if hasattr(judge_data, 'critique') and judge_data.critique:
            st.markdown("#### Critique")
            st.markdown(judge_data.critique)
        
        # Reflection
        if hasattr(judge_data, 'reflection'):
            reflection = judge_data.reflection
            st.markdown("#### Reflection")
            
            if hasattr(reflection, 'missing') and reflection.missing:
                st.markdown("**Missing:**")
                st.markdown(reflection.missing)
            
            if hasattr(reflection, 'superfluous') and reflection.superfluous:
                st.markdown("**Superfluous:**")
                st.markdown(reflection.superfluous)
        
        # Suggested follow-up queries
        if hasattr(judge_data, 'subqueries') and judge_data.subqueries:
            st.markdown("#### Suggested Follow-up Queries")
            for i, query in enumerate(judge_data.subqueries, 1):
                st.markdown(f"{i}. {query}")


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
            st.image(FRIEND_AVATAR, width=40)
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
        st.image(FRIEND_AVATAR, width=40)
    
    # Create the assistant message display object once
    message = st.chat_message("assistant")
    response_text = ""
    
    if st.session_state.agent_choice == "thinking-agent":
        agent = st.session_state.reflexive_agent
        response: AgentResponse = asyncio.run(agent.run(prompt))
        response_text = response.output
        
        # Display main response
        message.write(response_text)
        
        # Add collapsible evaluation section if judge response is available
        judge_response = response.judge_response
        if judge_response and hasattr(judge_response.final_output, 'score'):
            judge_data = judge_response.final_output
            render_evaluation_details(message, judge_data)
    else:
        client = OpenAI()
        response = client.chat.completions.create(
            model=st.session_state.agent_choice,
            messages=st.session_state.messages
        )
        response_text = response.choices[0].message.content
        message.write(response_text)
        
    # Add response to message history
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Calculate and display response time
    end_time = time.time()
    response_time = end_time - start_time
    st.markdown(f'<div style="text-align: right; color: #888888; font-size: 0.8em; margin-top: -20px;">Response time: {response_time:.2f}s</div>', 
                unsafe_allow_html=True)
    