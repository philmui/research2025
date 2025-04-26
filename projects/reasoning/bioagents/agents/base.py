from dataclasses import dataclass
from typing import List
from bioagents.models.citation import Citation

@dataclass
class AgentResponse:
    response_str: str
    citations: List[Citation]
    judge_response: str
    route: str
