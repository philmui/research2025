#############################################################################
# proposition_extraction.py
#
# class for proposition (facts, opinions, preferences, beliefs, experiences,
# and goals) extraction from conversations
#
# @author Theodore Mui
# @email  theodoremui@gmail.com
# Fri Jul 04 11:30:53 PDT 2025
#############################################################################

import re
from typing import Any, List, Optional, Union

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.bridge.pydantic import Field, field_validator
from llama_index.core.llms import LLM
from llama_index.core.memory.memory import BaseMemoryBlock
from llama_index.core.prompts import (BasePromptTemplate, PromptTemplate,
                                      RichPromptTemplate)
from llama_index.core.settings import Settings

DEFAULT_EXTRACT_PROMPT = RichPromptTemplate("""You are a comprehensive information extraction system designed to identify key propositions from conversations.

INSTRUCTIONS:
1. Review the conversation segment and existing propositions provided prior to this message
2. Extract specific, concrete propositions (facts, opinions, preferences, beliefs, experiences, and goals) the user has disclosed or important information discovered
3. Focus on all types of information including:
   - Factual information (preferences, personal details, requirements, constraints, context)
   - Opinions and beliefs (what the user thinks, feels, or believes about topics)
   - Preferences and choices (what the user likes, dislikes, or prefers)
   - Experiences and anecdotes (what the user has done or experienced)
   - Goals and intentions (what the user wants to achieve or plans to do)
4. Format each proposition as a separate <proposition> XML tag
5. Include both objective facts and subjective opinions - capture the full range of user-disclosed information
6. Do not duplicate information that are already in the existing propositions list

<existing_propositions>
{{ existing_propositions }}
</existing_propositions>

Return ONLY the extracted propositions in this exact format:
<propositions>
  <proposition>Specific proposition 1</proposition>
  <proposition>Specific proposition 2</proposition>
  <!-- More propositions as needed -->
</propositions>

If no new propositions are present, return: <propositions></propositions>""")

DEFAULT_CONDENSE_PROMPT = RichPromptTemplate("""You are a comprehensive proposition condensing system designed to identify key information from conversations.

INSTRUCTIONS:
1. Review the current list of existing propositions
2. Condense the propositions into a more concise list, less than {{ max_propositions }} propositions
3. Focus on all types of information including:
   - Factual information (preferences, personal details, requirements, constraints, context)
   - Opinions and beliefs (what the user thinks, feels, or believes about topics)
   - Preferences and choices (what the user likes, dislikes, or prefers)
   - Experiences and anecdotes (what the user has done or experienced)
   - Goals and intentions (what the user wants to achieve or plans to do)
4. Format each proposition as a separate <proposition> XML tag
5. Include both objective facts and subjective opinions - preserve the full range of user information
6. Do not duplicate propositions that are already in the existing propositions list

<existing_propositions>
{{ existing_propositions }}
</existing_propositions>

Return ONLY the condensed propositions in this exact format:
<propositions>
  <proposition>Specific proposition 1</proposition>
  <proposition>Specific proposition 2</proposition>
  <!-- More propositions as needed -->
</propositions>

If no new propositions are present, return: <propositions></propositions>""")


def get_default_llm() -> LLM:
    return Settings.llm


class PropositionExtractionMemoryBlock(BaseMemoryBlock[str]):
    """
    A memory block that extracts key propositions from conversation history using an LLM.

    This block identifies and stores discrete propositions disclosed during the conversation,
    including facts, opinions, preferences, beliefs, experiences, and goals,
    structuring them in XML format for easy parsing and retrieval.
    """

    name: str = Field(
        default="ExtractedPropositions", description="The name of the memory block."
    )
    llm: LLM = Field(
        default_factory=get_default_llm,
        description="The LLM to use for proposition extraction.",
    )
    propositions: List[str] = Field(
        default_factory=list,
        description="List of extracted propositions from the conversation.",
    )
    max_propositions: int = Field(
        default=50, description="The maximum number of propositions to store."
    )
    proposition_extraction_prompt_template: BasePromptTemplate = Field(
        default=DEFAULT_EXTRACT_PROMPT,
        description="Template for the proposition extraction prompt.",
    )
    proposition_condense_prompt_template: BasePromptTemplate = Field(
        default=DEFAULT_CONDENSE_PROMPT,
        description="Template for the proposition condense prompt.",
    )

    @field_validator("proposition_extraction_prompt_template", mode="before")
    @classmethod
    def validate_proposition_extraction_prompt_template(
        cls, v: Union[str, BasePromptTemplate]
    ) -> BasePromptTemplate:
        if isinstance(v, str):
            if "{{" in v and "}}" in v:
                v = RichPromptTemplate(v)
            else:
                v = PromptTemplate(v)
        return v

    async def _aget(
        self, messages: Optional[List[ChatMessage]] = None, **block_kwargs: Any
    ) -> str:
        """Return the current propositions as formatted text."""
        if not self.propositions:
            return ""

        return "\n".join([f"<proposition>{proposition}</proposition>" for proposition in self.propositions])

    async def _aput(self, messages: List[ChatMessage]) -> None:
        """Extract propositions from new messages and add them to the propositions list."""
        # Skip if no messages
        if not messages:
            return

        # Format existing propositions for the prompt
        existing_propositions_text = ""
        if self.propositions:
            existing_propositions_text = "\n".join(
                [f"<proposition>{proposition}</proposition>" for proposition in self.propositions]
            )

        # Create the prompt
        prompt_messages = self.proposition_extraction_prompt_template.format_messages(
            existing_propositions=existing_propositions_text,
        )

        # Get the propositions extraction
        response = await self.llm.achat(messages=[*messages, *prompt_messages])

        # Parse the XML response to extract propositions
        propositions_text = response.message.content or ""
        new_propositions = self._parse_propositions_xml(propositions_text)

        # Add new propositions to the list, avoiding exact-match duplicates
        for proposition in new_propositions:
            if proposition not in self.propositions:
                self.propositions.append(proposition)

        # Condense the propositions if they exceed the max_propositions
        if len(self.propositions) > self.max_propositions:
            existing_propositions_text = "\n".join(
                [f"<proposition>{proposition}</proposition>" for proposition in self.propositions]
            )

            prompt_messages = self.proposition_condense_prompt_template.format_messages(
                existing_propositions=existing_propositions_text,
                max_propositions=self.max_propositions,
            )
            response = await self.llm.achat(messages=[*messages, *prompt_messages])
            new_propositions = self._parse_propositions_xml(response.message.content or "")
            self.propositions = new_propositions

    def _parse_propositions_xml(self, xml_text: str) -> List[str]:
        """Parse propositions from XML format."""
        propositions = []

        # Extract content between <proposition> tags
        pattern = r"<proposition>(.*?)</proposition>"
        matches = re.findall(pattern, xml_text, re.DOTALL)

        # Clean up extracted propositions
        for match in matches:
            proposition = match.strip()
            if proposition:
                propositions.append(proposition)

        return propositions
