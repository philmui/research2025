#########################################################################
# base.py
#
# A collection of base classes for the bioagents project.
#
# Author: Phil Mui
# Date: 2025-04-19
#########################################################################

from dataclasses import dataclass
from typing import List
from .schemas import ReflexiveResponse

@dataclass
class Citation:
    url: str
    title: str
    snippet: str

@dataclass
class AgentResponse:
    output: str
    citations: List[Citation]
    judge_response: ReflexiveResponse = None

DEFAULT_THINKING_MODEL = "gpt-4.1"
