# Thinking Agents

We will explore 2 types of thinking:

1.  System 1 Thinking (primarily based on direct LLM invocations)
2.  System 2 Thinking (based on step-by-step, more deliberate orchestration of thinking)

To install `uv` on a Mac / Linux:

```mac or linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For a Windows machine:
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```


Before you run the code, make sure that you have a `.env` file at the toplevel with a `OPENAI_API_KEY` 

To invoke our thinking agent with a nice UI, type:

```
uv sync
source .venv/bin/activate
streamlit run thinking_agent.py
```