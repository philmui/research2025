# Setup Guide for Simple Agent

## Step 1: Create the Environment File

Create a `.env` file in your project root directory with the following content:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

**Replace `your_openai_api_key_here` with your actual OpenAI API key.**

### How to get your OpenAI API Key:
1. Go to https://platform.openai.com/api-keys
2. Sign in to your OpenAI account (or create one)
3. Click "Create new secret key"
4. Copy the key and paste it in your `.env` file

## Step 2: Install Dependencies

Make sure you have the required dependencies installed:

```bash
pip install llama-index-core llama-index-llms-openai python-dotenv ragas
```

## Step 3: Test the Agent

### Simple Agent (No Ragas Integration)

Now you can test the basic agent:

```bash
python atlas/agents/simple_agent.py --user_msg "Hello! What time is it?"
```

### Agent with Ragas Evaluation

For advanced evaluation capabilities:

```bash
# Basic usage
python atlas/agents/simple_agent_with_ragas.py --user_msg "What time is it?"

# With ragas evaluation
python atlas/agents/simple_agent_with_ragas.py --user_msg "What time is it?" --evaluate
```

## Step 4: Example Usage

```bash
# Ask for the current time
python atlas/agents/simple_agent.py --user_msg "What is the current time?"

# Ask a general question
python atlas/agents/simple_agent.py --user_msg "Hello, how are you?"

# With evaluation
python atlas/agents/simple_agent_with_ragas.py --user_msg "Can you tell me what time it is right now?" --evaluate
```

## What's Fixed

✅ **ImportError Fixed**: The `convert_to_ragas_messages` import error has been resolved by:
   - Removing the problematic import from the main agent
   - Creating a custom conversion function for the ragas-enabled version

✅ **OpenAI API Key Error**: Fixed the "Illegal header value b'Bearer '" error by adding proper API key validation and loading from `.env` file.

✅ **LlamaIndex API Changes**: Updated from deprecated `FunctionAgent` to the new `AgentWorkflow.from_tools_or_functions()` API.

✅ **Parameter Issues**: Fixed the "Must provide either user_msg or chat_history" error by using the correct parameter name.

✅ **Model Updates**: Updated to use `gpt-4o-mini` which is more current and cost-effective.

✅ **Ragas Integration**: Created a custom integration that works with the current ragas version (0.2.15).

## Available Files

- `simple_agent.py` - Basic working agent without ragas
- `simple_agent_with_ragas.py` - Advanced agent with optional ragas evaluation

## Troubleshooting

### If you get import errors:
```bash
pip install --upgrade llama-index-core llama-index-llms-openai ragas
```

### If the API key is not working:
1. Double-check your `.env` file is in the project root
2. Make sure there are no extra spaces in your API key
3. Verify your API key is valid at https://platform.openai.com/api-keys

### If you get ragas-related errors:
- Use the simple version: `simple_agent.py`
- Or use the ragas version without `--evaluate` flag

### What if I want to use local LLM / Embedding models instead?

Please refer to LlamaIndex documentation for configuring local models.

## Future Ragas Integration

The `convert_to_ragas_messages` function is expected to be available in future ragas versions for LlamaIndex. Currently, we've implemented a custom conversion function that works with ragas 0.2.15. 