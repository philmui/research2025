#########################################################################
# schemas.py
#
# A collection of schemas for the bioagents project.
#
# Author: Phil Mui
# Date: 2025-04-19
#########################################################################

from pydantic import BaseModel, Field
from typing import List

class Reflexion(BaseModel):
    missing: str = Field(description="Critique of what is missing.")
    superfluous: str = Field(description="Critique of what is superfluous")


class ReflexiveResponse(BaseModel):
    """Answer the user query with a detailed answer, reflection, critique, subqueries, and references."""

    answer: str = Field(description="detailed answer to the user query.")
    query_str: str = Field(description="The user query you are trying to answer.")
    reflection: Reflexion = Field(description="Your reflection on the initial answer.")
    critique: str = Field(description="A detailed critique highlighting specific missing or inadequate aspects of the response")
    subqueries: List[str] = Field(description="1-3 additional queries for researching improvements to address the critique of your current answer.")
    score: float = Field(
        description="The score of the response between 0.0 and 1.0 evaluating sufficiency to answer the user query."
    )
    references: List[str] = Field(description="Citations or sources for your answer.")

