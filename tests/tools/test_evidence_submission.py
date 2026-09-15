"""Tests for structured evidence submission."""

from datetime import date
from uuid import uuid4

from fin_automation.models.common import ParsingStatus, SearchPurpose, SourceCategory
from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import SourceRecord
from fin_automation.tools.evidence_submission import SubmitExtractedEvidenceTool


def test_submission_attaches_authoritative_ids() -> None:
    workflow_id = uuid4()
    requirement = EvidenceRequirement(
        name="Revenue",
        description="Find reported revenue.",
        candidate_name="Company A",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.PRIMARY],
        required=True,
    )
    source = SourceRecord(
        workflow_id=workflow_id,
        search_result_id=uuid4(),
        title="Company A Results",
        url="https://example.com/results",
        publisher="example.com",
        retrieval_date=date.today(),
        source_category=SourceCategory.PRIMARY,
        parsing_status=ParsingStatus.SUCCESS,
        candidate_names=["Company A"],
        evidence_requirement_ids=[requirement.requirement_id],
        content_summary="Company A reported revenue.",
    )

    tool = SubmitExtractedEvidenceTool()
    tool.begin_run(source, [requirement])
    tool.forward(
        {
            "evidence_records": [
                {
                    "candidate_name": "Company A",
                    "evidence_requirement_id": str(requirement.requirement_id),
                    "evidence_type": "reported_revenue",
                    "content": "Revenue was USD 10 million.",
                    "reported_value": "10",
                    "currency": "USD",
                    "unit": "million",
                    "reporting_period": "FY2025",
                    "supports_candidate": True,
                    "extraction_notes": [],
                }
            ],
            "evidence_gaps": [],
        }
    )

    evidence = tool.accepted_evidence[0]
    assert evidence.workflow_id == workflow_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_requirement_id == requirement.requirement_id
