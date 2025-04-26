from dataclasses import dataclass
from bioagents.models.citation import Citation
from typing import List

@dataclass
class AgentResponse:
    response_str: str
    citations: List[Citation]
    judge_response: str
    route: str