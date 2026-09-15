"""Evidence Validation Agent boundary for Phase 7."""

from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    RecommendationResult,
)
from fin_automation.models.intake import InvestorProfile, ResearchRequest
from fin_automation.models.research import ResearchPlan
from fin_automation.models.sources import ExtractedEvidence, SourceRecord
from fin_automation.models.validation import ValidationClaim, ValidationResult
from fin_automation.tools.evidence_validation import (
    EvidenceValidationService,
)


class EvidenceValidationAgent:
    """Validate a preliminary recommendation against workflow records.

    The validation decision is deterministic. A language model may later
    help classify nuanced claim relevance, but it cannot bypass these
    identifier, lineage, safety, and boundary checks.
    """

    def __init__(self) -> None:
        """Initialize the deterministic validation boundary."""

        self._validator = EvidenceValidationService()

    def validate(
        self,
        *,
        research_request: ResearchRequest,
        investor_profile: InvestorProfile,
        research_plan: ResearchPlan,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
        candidate_analyses: list[CandidateAnalysis],
        recommendation: RecommendationResult,
        claims: list[ValidationClaim],
    ) -> ValidationResult:
        """Return the validated outcome for one workflow pass."""

        return self._validator.validate(
            research_request=research_request,
            investor_profile=investor_profile,
            research_plan=research_plan,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations,
            candidate_analyses=candidate_analyses,
            recommendation=recommendation,
            claims=claims,
        )