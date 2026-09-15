"""Tests for deterministic SourceRecord construction."""

from uuid import uuid4

import pytest

from fin_automation.agents.evidence_extraction import EvidenceExtractionAgent
from fin_automation.models.common import SourceCategory
from fin_automation.models.sources import SelectedSource


def create_selected_source(raw_content: str | None = "Reported source content."):
    return SelectedSource(
        search_result_id=uuid4(),
        url="https://example.com/results",
        title="Company A Results",
        domain="example.com",
        raw_content=raw_content,
        candidate_name="Company A",
        selected=True,
        expected_source_category=SourceCategory.PRIMARY,
        selection_reason="Relevant primary source.",
        exclusion_reason=None,
        evidence_requirement_ids=[uuid4()],
    )


def test_build_source_record_preserves_selected_source() -> None:
    workflow_id = uuid4()
    selected = create_selected_source()

    source = EvidenceExtractionAgent._build_source_record(
        selected_source=selected,
        workflow_id=workflow_id,
    )

    assert source.workflow_id == workflow_id
    assert source.search_result_id == selected.search_result_id
    assert str(source.url) == str(selected.url)
    assert source.candidate_names == ["Company A"]


def test_build_source_record_requires_content() -> None:
    with pytest.raises(ValueError, match="requires selected source content"):
        EvidenceExtractionAgent._build_source_record(
            selected_source=create_selected_source(None),
            workflow_id=uuid4(),
        )
