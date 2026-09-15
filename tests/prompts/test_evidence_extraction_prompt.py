"""Tests for evidence-extraction prompt construction."""

from datetime import date
from uuid import uuid4

import pytest

from fin_automation.models.common import ParsingStatus, SearchPurpose, SourceCategory
from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import SourceRecord
from fin_automation.prompts.evidence_extraction import (
    build_evidence_extraction_messages,
)


def create_requirement() -> EvidenceRequirement:
    return EvidenceRequirement(
        name="Revenue growth",
        description="Find reported revenue-growth evidence.",
        candidate_name="Company A",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.PRIMARY],
        required=True,
    )


def create_source(requirement_id):
    return SourceRecord(
        workflow_id=uuid4(),
        search_result_id=uuid4(),
        title="Company A Results",
        url="https://example.com/results",
        publisher="example.com",
        retrieval_date=date.today(),
        source_category=SourceCategory.PRIMARY,
        parsing_status=ParsingStatus.SUCCESS,
        candidate_names=["Company A"],
        evidence_requirement_ids=[requirement_id],
        content_summary="Company A reported revenue growth.",
    )


def test_prompt_contains_source_and_requirement() -> None:
    requirement = create_requirement()
    source = create_source(requirement.requirement_id)

    messages = build_evidence_extraction_messages(
        source_record=source,
        raw_content="Company A reported revenue of USD 10 million.",
        evidence_requirements=[requirement],
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert str(source.source_id) in messages[1]["content"]
    assert str(requirement.requirement_id) in messages[1]["content"]


def test_prompt_rejects_empty_content() -> None:
    requirement = create_requirement()
    source = create_source(requirement.requirement_id)

    with pytest.raises(ValueError, match="requires source content"):
        build_evidence_extraction_messages(source, "   ", [requirement])
