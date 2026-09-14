"""Prompt construction for application agents."""

from fin_automation.prompts.intake import (
    INTAKE_SYSTEM_PROMPT,
    build_intake_messages,
)
from fin_automation.prompts.research_planning import (
    RESEARCH_PLANNING_SYSTEM_PROMPT,
    build_research_planning_messages,
)
from fin_automation.prompts.source_selection import (
    SOURCE_SELECTION_SYSTEM_PROMPT,
    build_source_selection_messages,
)

__all__ = [
    "INTAKE_SYSTEM_PROMPT",
    "RESEARCH_PLANNING_SYSTEM_PROMPT",
    "SOURCE_SELECTION_SYSTEM_PROMPT",
    "build_intake_messages",
    "build_research_planning_messages",
    "build_source_selection_messages",
]