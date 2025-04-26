from dotenv import load_dotenv, find_dotenv
import streamlit as st
from openai import OpenAI
import os

load_dotenv(find_dotenv())

# Set page config
st.set_page_config(
    page_title="BioReasoning Assistant",
    page_icon="🧬",
    layout="wide"
)

# Initialize OpenAI client
client = OpenAI()

# Sidebar for model selection
with st.sidebar:
    st.title("Settings")
    model = st.selectbox(
        "Select LLM Model",
        ["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1", "gpt-4o", ],
        index=0  # Default to gpt-4.1-mini
    )

# Main app interface
st.title("BioReasoning Assistant")
st.write("Ask me anything about medicine, genetics, drug design, and clinical trials!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
        )
        assistant_response = response.choices[0].message.content
        st.write(assistant_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
