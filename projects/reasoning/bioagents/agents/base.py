#------------------------------------------------------------------------------
# base.py
# 
# This file provides base classes for agent interactions. It provides a common
# interface for all agent responses.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------


from dataclasses import dataclass
from typing import List
from bioagents.models.citation import Citation

@dataclass
class AgentResponse:
    response_str: str
    citations: List[Citation]
    judge_response: str
    route: str
