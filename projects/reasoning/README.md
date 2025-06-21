# Bio Reasoning Project


## Environment Setup

Before running any program here, we need to do basic lib imports at the toplevel of this project.  We are also activating the `bioagent` virtual environment here:

```
uv sync
source .venv/bin/activate
```

In order to run the `bioagents` module, we need to set the following env variable at the toplevel:

```
export PYTHONPATH="`pwd`"
```

## Running Streamlit

To run the web app after activating the virtual environment, at the toplevel, type:

```
streamlit run bioreasoning.py
```


## Agent Graph Design

The initial project has a simple "Agent Graph" design:

```mermaid
flowchart TB
    %% Top: User input
    U[User Input] 
    
    %% Concierge Agent layer
    U --> CA[Concierge Agent]
    subgraph "Concierge Agent"
      CA1[Input Parser]
      CA2[Intent Classifier]
      CA3[Router]
      CA1 --> CA2 --> CA3
    end
    
    %% Agent Processing Layer
    subgraph "Sub-agents"
        direction LR
        CC[Chitchat Agent]
        BM[BioMCP Agent]
        WS[Websearch Agent]
    end
    
    CA3 --> CC
    CA3 --> BM
    CA3 --> WS

    %% Aggregation and output
    CC --> AG[Response Aggregator]
    BM --> AG
    WS --> AG
    AG --> U
```


---
If you have any questions, please contact Theodore Mui <theodoremui@gmail.com>
