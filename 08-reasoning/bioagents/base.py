from dataclasses import dataclass
from typing import List

@dataclass
class Citation:
    url: str
    title: str
    snippet: str

@dataclass
class AgentResponse:
    output: str
    citations: List[Citation]

DEFAULT_THINKING_MODEL = "gpt-4.1"
