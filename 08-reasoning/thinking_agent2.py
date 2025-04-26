import asyncio
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import streamlit as st
from openai import OpenAI
import time

from bioagents.reflexive_agent import ReflexiveAgent
from bioagents.base import DEFAULT_THINKING_MODEL

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize the ReflexiveAgent as a singleton in session state
if "reflexive_agent" not in st.session_state:
    st.session_state.reflexive_agent = ReflexiveAgent()
    print("Initialized ReflexiveAgent singleton")

MODEL_DESCRIPTIONS = {
    "gpt-4.1-nano": "gpt-4.1-nano (Fast)",
    "gpt-4.1": "gpt-4.1 (Capable)",
    "o4-mini": "o4-mini (Reasoning)",
    "thinking-agent": "Thinking Agent (Web Search)"
}

# Define example queries
EXAMPLE_QUERIES = [
    "",
    "About measles, how is the disease trend in the US over the last year?",
    "About measles, are there pubmed articles about this disease in the last year?",
    "About COVID, how is the disease trend in the US over the last year?",
    "About COVID, are there pubmed articles about this disease in the last year?",
]


if "agent_choice" not in st.session_state:
    st.session_state["agent_choice"] = DEFAULT_THINKING_MODEL

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

if "pending_example" not in st.session_state:
    st.session_state["pending_example"] = None

# Define all functions before using them
def process_query(query):
    """Process a query and generate a response"""
    if not OPENAI_API_KEY:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    start_time = time.time()
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Display user message with avatar on right
    cols = st.columns([0.85, 0.15])  # Avatar on right
    with cols[0]:  # Text column
        st.markdown(f'<div style="width:100%; text-align:right; padding-right:10px;">{query}</div>', unsafe_allow_html=True)
    with cols[1]:  # Avatar column
        st.image("https://api.dicebear.com/7.x/bottts/svg?seed=user", width=40)
    
    response_text = ""
    if st.session_state.agent_choice == "thinking-agent":
        # Use the singleton agent from session state
        agent = st.session_state.reflexive_agent
        response = asyncio.run(agent.run(query))
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

def handle_example_selection():
    """Handle when an example is selected from the dropdown"""
    selected = st.session_state.example_dropdown
    if selected and selected != "":
        # Store the example query for processing but don't add to messages yet
        st.session_state.pending_example = selected
        # Set a flag indicating we need to process - don't call rerun directly
        st.session_state.needs_processing = True

# Initialize the processing flag if not already set
if "needs_processing" not in st.session_state:
    st.session_state.needs_processing = False

# Build the UI
st.title("💬 Agent Reasoning Chatbot")

# Display message history with right alignment for user messages
for msg in st.session_state.messages:
    # Handle different styling for user vs assistant messages
    if msg["role"] == "user":
        # Create columns for user message - reverse order for right-side avatar
        cols = st.columns([0.85, 0.15])  # Avatar on right
        with cols[0]:  # Text column
            st.markdown(f'<div style="width:100%; text-align:right; padding-right:10px;">{msg["content"]}</div>', unsafe_allow_html=True)
        with cols[1]:  # Avatar column
            st.image("https://api.dicebear.com/7.x/bottts/svg?seed=user", width=40)
    else:
        # Normal display for assistant messages
        message = st.chat_message(msg["role"])
        message.write(msg["content"])

# Sidebar UI
with st.sidebar:
    "[Mui Group @ ASDRP](https://bit.ly/mui-group)"
    "[Research Repo](https://github.com/philmui/research2025)"
    st.divider()
    st.session_state.agent_choice = st.selectbox(
        "Choose Mode:",
        MODEL_DESCRIPTIONS.keys(),
        help="Select a mode to use for generating responses",
        format_func=lambda x: MODEL_DESCRIPTIONS[x]
    )
    st.divider()
    
    st.markdown("<p style='font-size: 14px; font-weight: bold;'>Example Queries:</p>", unsafe_allow_html=True)
    
    # Add a dropdown for example queries with smaller font
    selected_example = st.selectbox(
        "Example Queries",
        EXAMPLE_QUERIES,
        key="example_dropdown",
        on_change=handle_example_selection,
        label_visibility="collapsed"  # Hide the label
    )
    
    # Custom CSS for smaller font in the dropdown
    st.markdown("""
    <style>
    div[data-testid="stSelectbox"] {
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

# Process pending example query if one exists
if st.session_state.pending_example and st.session_state.needs_processing:
    query = st.session_state.pending_example
    # Add to messages
    st.session_state.messages.append({"role": "user", "content": query})
    # Clear pending example
    st.session_state.pending_example = None
    # Reset processing flag
    st.session_state.needs_processing = False
    # Process the query
    process_query(query)
    # Now it's safe to rerun from the main flow (outside callbacks)
    st.rerun()

# Chat input
prompt = st.chat_input()
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    process_query(prompt)
    