"""Tests for source and evidence data contracts."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    ParsingStatus,
    RetrievalStatus,
    SearchPurpose,
    SourceCategory,
    SourceSelectionStatus,
    WorkflowStage,
)
from fin_automation.models.research import AdditionalResearchRequest
from fin_automation.models.sources import (
    ExtractedEvidence,
    RetrievalResult,
    SearchResult,
    SelectedSource,
    SourceRecord,
    SourceSelection,
)


def create_search_result(
    workflow_id: UUID,
) -> SearchResult:
    """Create a valid search result."""

    return SearchResult(
        workflow_id=workflow_id,
        query_id=uuid4(),
        title="Company A Annual Report",
        url="https://example.com/company-a-report",
        snippet="Company A reported annual results.",
        domain="example.com",
        result_position=1,
    )


def create_selected_source(
    search_result_id: UUID,
) -> SelectedSource:
    """Create a valid selected source using the current schema."""

    return SelectedSource(
        search_result_id=search_result_id,
        url=(
            "https://investors.example.com/"
            "annual-report"
        ),
        title="Company A Annual Report",
        domain="investors.example.com",
        raw_content=(
            "Company A reported annual revenue growth "
            "in its annual report."
        ),
        selected=True,
        selection_reason=(
            "The annual report contains primary financial evidence."
        ),
        exclusion_reason=None,
        candidate_name="Company A",
        evidence_requirement_ids=[
            uuid4()
        ],
        expected_source_category=(
            SourceCategory.PRIMARY
        ),
    )


def test_search_result_accepts_valid_data() -> None:
    """Valid search-result data should pass validation."""

    result = create_search_result(uuid4())

    assert result.title == "Company A Annual Report"
    assert result.url.scheme == "https"
    assert result.result_position == 1
    assert result.retrieved_at.tzinfo is not None


@pytest.mark.parametrize(
    "invalid_url",
    [
        "not-a-url",
        "ftp://example.com/file",
        "file:///tmp/source.html",
    ],
)
def test_search_result_rejects_invalid_url(
    invalid_url: str,
) -> None:
    """Search-result URLs must use HTTP or HTTPS."""

    with pytest.raises(ValidationError):
        SearchResult(
            workflow_id=uuid4(),
            query_id=uuid4(),
            title="Invalid result",
            url=invalid_url,
            domain="example.com",
        )


def test_selected_source_requires_evidence_requirement() -> None:
    """Selected sources must identify their evidence purpose."""

    with pytest.raises(
        ValidationError,
        match="must reference at least one evidence requirement",
    ):
        SelectedSource(
            search_result_id=uuid4(),
            url="https://example.com/source",
            title="Example Source",
            domain="example.com",
            raw_content="Example source content.",
            selected=True,
            selection_reason="The source appears relevant.",
            exclusion_reason=None,
            candidate_name="Company A",
            evidence_requirement_ids=[],
            expected_source_category=SourceCategory.PRIMARY,
        )

def test_excluded_source_requires_reason() -> None:
    """An excluded source must explain its exclusion."""

    with pytest.raises(
        ValidationError,
        match="must include an exclusion reason",
    ):
        SelectedSource(
            search_result_id=uuid4(),
            url="https://example.com/source",
            title="Example Source",
            domain="example.com",
            raw_content=None,
            selected=False,
            selection_reason="The source was reviewed.",
            exclusion_reason=None,
            candidate_name="Company A",
            evidence_requirement_ids=[],
            expected_source_category=(
                SourceCategory.UNSUPPORTED
            ),
        )

def test_unsupported_source_cannot_be_selected() -> None:
    """Unsupported sources cannot proceed to analysis."""

    with pytest.raises(
        ValidationError,
        match="unsupported source cannot be selected",
    ):
        SelectedSource(
            search_result_id=uuid4(),
            url="https://example.com/source",
            title="Example Source",
            domain="example.com",
            raw_content="Example source content.",
            selected=True,
            selection_reason="The source appears relevant.",
            exclusion_reason=None,
            candidate_name="Company A",
            evidence_requirement_ids=[
                uuid4()
            ],
            expected_source_category=(
                SourceCategory.UNSUPPORTED
            ),
        )

def test_ready_selection_requires_selected_source() -> None:
    """Ready status requires at least one selected source."""

    with pytest.raises(
        ValidationError,
        match="requires at least one selected source",
    ):
        SourceSelection(
            workflow_id=uuid4(),
            plan_id=uuid4(),
            status=SourceSelectionStatus.READY_FOR_RETRIEVAL,
            selections=[],
        )


def test_ready_selection_accepts_selected_source() -> None:
    """A valid selected source should support ready status."""

    workflow_id = uuid4()
    search_result = create_search_result(workflow_id)

    source_selection = SourceSelection(
        workflow_id=workflow_id,
        plan_id=uuid4(),
        status=SourceSelectionStatus.READY_FOR_RETRIEVAL,
        selections=[
            create_selected_source(
                search_result.search_result_id
            )
        ],
    )

    assert (
        source_selection.status
        == SourceSelectionStatus.READY_FOR_RETRIEVAL
    )


def test_additional_search_requires_request() -> None:
    """Additional-search status requires a research request."""

    with pytest.raises(
        ValidationError,
        match="requires at least one additional research request",
    ):
        SourceSelection(
            workflow_id=uuid4(),
            plan_id=uuid4(),
            status=(
                SourceSelectionStatus.ADDITIONAL_SEARCH_REQUIRED
            ),
        )


def test_additional_request_must_use_same_workflow() -> None:
    """Additional research requests must match the workflow."""

    source_selection_workflow_id = uuid4()

    request = AdditionalResearchRequest(
        workflow_id=uuid4(),
        requested_by_stage=WorkflowStage.SOURCE_SELECTION,
        missing_evidence="Current profitability evidence",
        reason="Available profitability evidence is outdated.",
        suggested_search_purpose=SearchPurpose.PROFITABILITY,
    )

    with pytest.raises(
        ValidationError,
        match="must use the same workflow_id",
    ):
        SourceSelection(
            workflow_id=source_selection_workflow_id,
            plan_id=uuid4(),
            status=(
                SourceSelectionStatus.ADDITIONAL_SEARCH_REQUIRED
            ),
            additional_research_requests=[request],
        )


def test_successful_retrieval_accepts_required_data() -> None:
    """Successful retrieval requires final URL and timestamp."""

    result = RetrievalResult(
        workflow_id=uuid4(),
        search_result_id=uuid4(),
        requested_url="https://example.com/source",
        final_url="https://example.com/source",
        status=RetrievalStatus.SUCCESS,
        http_status_code=200,
        content_type="text/html",
        retrieved_at=datetime.now(timezone.utc),
    )

    assert result.status == RetrievalStatus.SUCCESS
    assert result.error_message is None


def test_successful_retrieval_requires_final_url() -> None:
    """Successful retrieval must preserve the final URL."""

    with pytest.raises(
        ValidationError,
        match="requires a final URL",
    ):
        RetrievalResult(
            workflow_id=uuid4(),
            search_result_id=uuid4(),
            requested_url="https://example.com/source",
            status=RetrievalStatus.SUCCESS,
            retrieved_at=datetime.now(timezone.utc),
        )


def test_failed_retrieval_requires_error_message() -> None:
    """Failed retrieval must explain the failure."""

    with pytest.raises(
        ValidationError,
        match="requires an error message",
    ):
        RetrievalResult(
            workflow_id=uuid4(),
            search_result_id=uuid4(),
            requested_url="https://example.com/source",
            status=RetrievalStatus.FAILED,
        )


def test_retrieval_rejects_naive_timestamp() -> None:
    """Retrieval timestamps must contain timezone information."""

    with pytest.raises(
        ValidationError,
        match="retrieved_at must be timezone-aware",
    ):
        RetrievalResult(
            workflow_id=uuid4(),
            search_result_id=uuid4(),
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            status=RetrievalStatus.SUCCESS,
            retrieved_at=datetime(2026, 9, 11, 10, 0, 0),
        )


def test_successful_source_record_accepts_summary() -> None:
    """A successfully parsed source should preserve metadata."""

    source = SourceRecord(
        workflow_id=uuid4(),
        retrieval_id=uuid4(),
        search_result_id=uuid4(),
        title="Company A Annual Report",
        url="https://example.com/company-a-report",
        publisher="Company A",
        publication_date=date(2026, 3, 1),
        retrieval_date=date(2026, 9, 11),
        source_category=SourceCategory.PRIMARY,
        parsing_status=ParsingStatus.SUCCESS,
        candidate_names=["Company A"],
        evidence_requirement_ids=[uuid4()],
        content_summary=(
            "Company A reported annual financial results."
        ),
    )

    assert source.parsing_status == ParsingStatus.SUCCESS
    assert source.content_summary is not None


def test_successful_source_record_requires_summary() -> None:
    """Successful parsing requires a content summary."""

    with pytest.raises(
        ValidationError,
        match="requires a content summary",
    ):
        SourceRecord(
            workflow_id=uuid4(),
            retrieval_id=uuid4(),
            search_result_id=uuid4(),
            title="Company A Annual Report",
            url="https://example.com/company-a-report",
            retrieval_date=date(2026, 9, 11),
            source_category=SourceCategory.PRIMARY,
            parsing_status=ParsingStatus.SUCCESS,
        )


def test_source_record_rejects_duplicate_candidates() -> None:
    """Candidate associations should be unique regardless of case."""

    with pytest.raises(
        ValidationError,
        match="candidate names must be unique",
    ):
        SourceRecord(
            workflow_id=uuid4(),
            retrieval_id=uuid4(),
            search_result_id=uuid4(),
            title="Company A Annual Report",
            url="https://example.com/company-a-report",
            retrieval_date=date(2026, 9, 11),
            source_category=SourceCategory.PRIMARY,
            parsing_status=ParsingStatus.PARTIAL,
            candidate_names=["Company A", "company a"],
        )


def test_extracted_evidence_accepts_numeric_value() -> None:
    """Numeric evidence should preserve its context."""

    evidence = ExtractedEvidence(
        workflow_id=uuid4(),
        source_id=uuid4(),
        candidate_name="Company A",
        evidence_requirement_id=uuid4(),
        evidence_type="reported_financial_value",
        content="Revenue was USD 2.5 billion in fiscal year 2025.",
        reported_value=Decimal("2.5"),
        currency="USD",
        unit="billion",
        reporting_period="FY2025",
        supports_candidate=True,
    )

    assert evidence.reported_value == Decimal("2.5")
    assert evidence.currency == "USD"
    assert evidence.unit == "billion"
    assert evidence.reporting_period == "FY2025"


def test_numeric_metadata_requires_value() -> None:
    """Numeric metadata cannot exist without a numeric value."""

    with pytest.raises(
        ValidationError,
        match="require a reported numeric value",
    ):
        ExtractedEvidence(
            workflow_id=uuid4(),
            source_id=uuid4(),
            evidence_type="reported_financial_value",
            content="Revenue was reported for fiscal year 2025.",
            currency="USD",
            unit="billion",
            reporting_period="FY2025",
        )


def test_source_models_reject_unknown_fields() -> None:
    """Source contracts should reject undocumented fields."""

    with pytest.raises(ValidationError):
        SearchResult(
            workflow_id=uuid4(),
            query_id=uuid4(),
            title="Company A",
            url="https://example.com/company-a",
            domain="example.com",
            undocumented_field="unexpected value",
        )