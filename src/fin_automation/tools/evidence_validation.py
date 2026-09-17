"""Deterministic checks for Phase 7 evidence validation."""

import re
from collections.abc import Iterable
from typing import TypeVar
from uuid import UUID

from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    RecommendationResult,
)
from fin_automation.models.intake import InvestorProfile, ResearchRequest
from fin_automation.models.research import ResearchPlan
from fin_automation.models.research import AdditionalResearchRequest
from fin_automation.models.sources import ExtractedEvidence, SourceRecord
from fin_automation.models.validation import (
    ValidationClaim,
    ValidationFinding,
    ValidationResult,
)
from fin_automation.models.common import (
    CorrectionTarget,
    ValidationCategory,
    ValidationOutcome,
    ValidationSeverity,
    SearchPurpose,
    WorkflowStage,
)


_RecordT = TypeVar("_RecordT")

_STOP_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "has",
    "in", "is", "of", "on", "or", "the", "to", "with",
}
_UNSAFE_PHRASES = (
    "guaranteed return",
    "guaranteed profit",
    "cannot lose",
    "no risk",
    "must buy",
    "buy this",
    "execute a trade",
    "place an order",
)


class EvidenceValidationService:
    """Validate one preliminary recommendation against workflow records."""

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
        """Return a structured validation decision without model judgment."""

        workflow_id = research_request.workflow_id
        findings: list[ValidationFinding] = []
        sources_by_id = self._index(source_records, "source_id")
        evidence_by_id = self._index(evidence_records, "evidence_id")
        calculations_by_id = self._index(calculations, "calculation_id")
        analyses_by_id = self._index(candidate_analyses, "analysis_id")

        self._check_workflow_ids(
            workflow_id=workflow_id,
            records=(
                investor_profile,
                research_plan,
                *source_records,
                *evidence_records,
                *calculations,
                *candidate_analyses,
                recommendation,
                *claims,
            ),
            findings=findings,
        )
        self._check_claims(
            workflow_id=workflow_id,
            claims=claims,
            sources_by_id=sources_by_id,
            evidence_by_id=evidence_by_id,
            calculations_by_id=calculations_by_id,
            findings=findings,
        )
        self._check_recommendation(
            workflow_id=workflow_id,
            research_request=research_request,
            investor_profile=investor_profile,
            research_plan=research_plan,
            recommendation=recommendation,
            candidate_analyses=candidate_analyses,
            analyses_by_id=analyses_by_id,
            findings=findings,
        )

        blocking_findings = [
            finding
            for finding in findings
            if finding.severity == ValidationSeverity.BLOCKING
        ]
        research_findings = [
            finding
            for finding in findings
            if finding.correction_target == CorrectionTarget.SOURCE_SELECTION
        ]

        if blocking_findings:
            outcome = self._blocking_outcome(blocking_findings)
        elif research_findings:
            outcome = ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
        elif any(
            finding.severity == ValidationSeverity.ERROR
            for finding in findings
        ):
            outcome = ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
        else:
            outcome = ValidationOutcome.APPROVED

        additional_research_requests = [
            AdditionalResearchRequest(
                workflow_id=workflow_id,
                requested_by_stage=WorkflowStage.EVIDENCE_VALIDATION,
                candidate_name=finding.candidate_name,
                missing_evidence=finding.description,
                reason=finding.required_correction or finding.description,
                suggested_search_purpose=SearchPurpose.SOURCE_CORROBORATION,
                blocks_recommendation=True,
            )
            for finding in research_findings
        ]

        approved = outcome == ValidationOutcome.APPROVED
        return ValidationResult(
            workflow_id=workflow_id,
            recommendation_id=recommendation.recommendation_id,
            outcome=outcome,
            findings=findings,
            approved_candidate_analysis_ids=(
                [analysis.analysis_id for analysis in candidate_analyses]
                if approved else []
            ),
            approved_source_ids=(list(sources_by_id) if approved else []),
            approved_evidence_ids=(list(evidence_by_id) if approved else []),
            approved_calculation_ids=(
                list(calculations_by_id) if approved else []
            ),
            additional_research_requests=additional_research_requests,
            summary=self._summary(outcome, findings),
        )

    @staticmethod
    def _index(records: Iterable[_RecordT], field_name: str) -> dict[UUID, _RecordT]:
        """Index records and reject duplicate identifiers.

        Generic in the record type so callers get back a properly
        typed dict (e.g. `dict[UUID, ExtractedEvidence]`) instead of
        `dict[UUID, object]`, which would otherwise force every
        downstream attribute access (`evidence.source_id`, etc.) to be
        flagged by static type checkers even though it's always
        correct at runtime — `field_name` is still a dynamic
        `getattr`, so it can't be checked either way, but that's
        internal to this method, not something every caller has to
        work around.
        """

        indexed: dict[UUID, _RecordT] = {}
        for record in records:
            identifier = getattr(record, field_name)
            if identifier in indexed:
                raise ValueError(
                    f"Duplicate {field_name} in validation input."
                )
            indexed[identifier] = record
        return indexed

    @staticmethod
    def _check_workflow_ids(
        *,
        workflow_id: UUID,
        records: Iterable[object],
        findings: list[ValidationFinding],
    ) -> None:
        """Reject records that cross workflow boundaries."""

        for record in records:
            if getattr(record, "workflow_id", workflow_id) != workflow_id:
                findings.append(
                    EvidenceValidationService._finding(
                        workflow_id=workflow_id,
                        category=ValidationCategory.INCOMPATIBLE_COMPARISON,
                        description="A validation input belongs to another workflow.",
                        correction="Discard the foreign record and use a record from this workflow.",
                        target=CorrectionTarget.ORCHESTRATOR,
                    )
                )

    def _check_claims(
        self,
        *,
        workflow_id: UUID,
        claims: list[ValidationClaim],
        sources_by_id: dict[UUID, SourceRecord],
        evidence_by_id: dict[UUID, ExtractedEvidence],
        calculations_by_id: dict[UUID, CalculatedMetric],
        findings: list[ValidationFinding],
    ) -> None:
        """Validate claim references and claim-to-record support."""

        for claim in claims:
            unknown_sources = set(claim.source_ids) - set(sources_by_id)
            unknown_evidence = set(claim.evidence_ids) - set(evidence_by_id)

            if unknown_sources or unknown_evidence:
                findings.append(
                    self._finding(
                        workflow_id=workflow_id,
                        category=ValidationCategory.INVALID_CITATION,
                        severity=ValidationSeverity.BLOCKING,
                        affected_claim=claim.text,
                        source_ids=list(unknown_sources),
                        evidence_ids=list(unknown_evidence),
                        description="The claim references an unknown source or evidence identifier.",
                        correction="Replace the citation with a record from this workflow.",
                        target=CorrectionTarget.FINANCIAL_ANALYSIS,
                    )
                )
                continue

            cited_evidence = [evidence_by_id[evidence_id] for evidence_id in claim.evidence_ids]
            for evidence in cited_evidence:
                if claim.source_ids and evidence.source_id not in claim.source_ids:
                    findings.append(
                        self._finding(
                            workflow_id=workflow_id,
                            category=ValidationCategory.INVALID_CITATION,
                            severity=ValidationSeverity.BLOCKING,
                            candidate_name=claim.candidate_name,
                            affected_claim=claim.text,
                            source_ids=claim.source_ids,
                            evidence_ids=[evidence.evidence_id],
                            description="The evidence citation does not match the cited source.",
                            correction="Cite the source that produced the evidence.",
                            target=CorrectionTarget.FINANCIAL_ANALYSIS,
                        )
                    )
                if claim.candidate_name and evidence.candidate_name and evidence.candidate_name.casefold() != claim.candidate_name.casefold():
                    findings.append(
                        self._finding(
                            workflow_id=workflow_id,
                            category=ValidationCategory.IRRELEVANT_CITATION,
                            severity=ValidationSeverity.BLOCKING,
                            candidate_name=claim.candidate_name,
                            affected_claim=claim.text,
                            evidence_ids=[evidence.evidence_id],
                            description="The cited evidence belongs to another candidate.",
                            correction="Use evidence for the claimed candidate.",
                            target=CorrectionTarget.FINANCIAL_ANALYSIS,
                        )
                    )
                elif not self._text_supported(claim.text, evidence.content):
                    findings.append(
                        self._finding(
                            workflow_id=workflow_id,
                            category=ValidationCategory.IRRELEVANT_CITATION,
                            severity=ValidationSeverity.BLOCKING,
                            candidate_name=claim.candidate_name,
                            affected_claim=claim.text,
                            evidence_ids=[evidence.evidence_id],
                            description="The cited evidence does not contain support for the claim.",
                            correction="Cite relevant evidence or qualify the claim.",
                            target=CorrectionTarget.FINANCIAL_ANALYSIS,
                        )
                    )

            if claim.calculation_id is not None:
                calculation = calculations_by_id.get(claim.calculation_id)
                if calculation is None:
                    findings.append(
                        self._finding(
                            workflow_id=workflow_id,
                            category=ValidationCategory.CALCULATION_INPUT_PROBLEM,
                            severity=ValidationSeverity.BLOCKING,
                            affected_claim=claim.text,
                            affected_calculation_id=claim.calculation_id,
                            description="The claim references an unknown calculation.",
                            correction="Use a validated calculation from this workflow.",
                            target=CorrectionTarget.FINANCIAL_CALCULATION,
                        )
                    )
                else:
                    self._check_calculation_claim(
                        workflow_id=workflow_id,
                        claim=claim,
                        calculation=calculation,
                        evidence_by_id=evidence_by_id,
                        findings=findings,
                    )
                    self._check_comparable_periods(
                        workflow_id=workflow_id,
                        claim=claim,
                        calculation=calculation,
                        evidence_by_id=evidence_by_id,
                        findings=findings,
                    )

            unsafe_text = claim.text.casefold()
            if any(phrase in unsafe_text for phrase in _UNSAFE_PHRASES):
                findings.append(
                    self._finding(
                        workflow_id=workflow_id,
                        category=ValidationCategory.HUMAN_REVIEW_BOUNDARY_FAILURE,
                        severity=ValidationSeverity.BLOCKING,
                        candidate_name=claim.candidate_name,
                        affected_claim=claim.text,
                        description="The claim contains guaranteed-return or trade-instruction language.",
                        correction="Remove the unsafe language and preserve human decision authority.",
                        target=CorrectionTarget.FINANCIAL_ANALYSIS,
                    )
                )

    def _check_calculation_claim(
        self,
        *,
        workflow_id: UUID,
        claim: ValidationClaim,
        calculation: CalculatedMetric,
        evidence_by_id: dict[UUID, ExtractedEvidence],
        findings: list[ValidationFinding],
    ) -> None:
        """Verify exact calculation metadata and evidence lineage."""

        mismatches: list[str] = []
        if claim.expected_value != calculation.value:
            mismatches.append("result")
        if claim.expected_unit is not None and claim.expected_unit != calculation.unit:
            mismatches.append("unit")
        if claim.expected_currency is not None and claim.expected_currency != calculation.currency:
            mismatches.append("currency")
        if claim.expected_reporting_periods and set(claim.expected_reporting_periods) != set(calculation.reporting_periods):
            mismatches.append("reporting period")
        if claim.evidence_ids and not set(calculation.input_evidence_ids).issubset(claim.evidence_ids):
            mismatches.append("input evidence")
        if any(evidence_id not in evidence_by_id for evidence_id in calculation.input_evidence_ids):
            mismatches.append("unknown input evidence")

        if mismatches:
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.CALCULATION_INPUT_PROBLEM,
                    severity=ValidationSeverity.BLOCKING,
                    candidate_name=claim.candidate_name,
                    affected_claim=claim.text,
                    affected_calculation_id=calculation.calculation_id,
                    evidence_ids=list(calculation.input_evidence_ids),
                    description=(
                        "The calculated claim does not match its recorded "
                        f"calculation metadata: {', '.join(mismatches)}."
                    ),
                    correction="Regenerate the claim from the validated calculation.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

    @staticmethod
    def _check_comparable_periods(
        *,
        workflow_id: UUID,
        claim: ValidationClaim,
        calculation: CalculatedMetric,
        evidence_by_id: dict[UUID, ExtractedEvidence],
        findings: list[ValidationFinding],
    ) -> None:
        """Reject calculations that compare different period granularities."""

        if calculation.operation.value != "growth_rate":
            return

        periods = [
            str(getattr(evidence_by_id[evidence_id], "reporting_period", ""))
            for evidence_id in calculation.input_evidence_ids
            if evidence_id in evidence_by_id
        ]
        if len(periods) != 2:
            return

        def granularity(period: str) -> str:
            normalized = period.upper().strip()
            if normalized.startswith("Q") or " Q" in normalized:
                return "quarter"
            if (
                normalized.startswith("FY")
                # Catches "FISCAL 2024" and "FISCAL YEAR 2024" alike;
                # requiring the literal phrase "FISCAL YEAR" missed the
                # very common "Fiscal 2024" form used by some sources,
                # which fell through to "other" and was then flagged
                # as incompatible with an "FY2024"-labeled figure for
                # the exact same period.
                or "FISCAL" in normalized
                or "ANNUAL" in normalized
                # A bare four-digit year (e.g. "2023") is also an
                # annual period. Sources routinely label the same
                # fiscal year one way ("FY2024") and the other
                # ("2024"); without this, every such pairing was
                # misclassified as an incompatible comparison even
                # though both values cover a full year.
                or re.fullmatch(r"(?:19|20)\d{2}", normalized)
            ):
                return "annual"
            return "other"

        granularities = {granularity(period) for period in periods}
        if len(granularities) <= 1:
            return

        findings.append(
            EvidenceValidationService._finding(
                workflow_id=workflow_id,
                category=ValidationCategory.INCOMPATIBLE_COMPARISON,
                severity=ValidationSeverity.BLOCKING,
                candidate_name=claim.candidate_name,
                affected_claim=claim.text,
                affected_calculation_id=calculation.calculation_id,
                evidence_ids=list(calculation.input_evidence_ids),
                description=(
                    "The calculation compares reporting periods with "
                    "different granularities: " + ", ".join(periods) + "."
                ),
                correction=(
                    "Retrieve matching periods, such as FY2024 and FY2023 "
                    "or Q3 2024 and Q3 2023."
                ),
                target=CorrectionTarget.SOURCE_SELECTION,
            )
        )

    def _check_recommendation(
        self,
        *,
        workflow_id: UUID,
        research_request: ResearchRequest,
        investor_profile: InvestorProfile,
        research_plan: ResearchPlan,
        recommendation: RecommendationResult,
        candidate_analyses: list[CandidateAnalysis],
        analyses_by_id: dict[UUID, CandidateAnalysis],
        findings: list[ValidationFinding],
    ) -> None:
        """Validate recommendation references, alignment, and safety."""

        unknown_analysis_ids = set(recommendation.candidate_analysis_ids) - set(analyses_by_id)
        if unknown_analysis_ids:
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.UNSUPPORTED_CLAIM,
                    severity=ValidationSeverity.BLOCKING,
                    description="The recommendation references an unknown candidate analysis.",
                    correction="Use only candidate analyses from this workflow.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

        candidate_names = {analysis.candidate_name.casefold() for analysis in candidate_analyses}
        if recommendation.preferred_candidate and recommendation.preferred_candidate.casefold() not in candidate_names:
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.PROMPT_ALIGNMENT_FAILURE,
                    severity=ValidationSeverity.BLOCKING,
                    candidate_name=recommendation.preferred_candidate,
                    description="The preferred candidate was not evaluated in this workflow.",
                    correction="Remove the candidate or evaluate it within the approved scope.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

        excluded_candidates = {
            candidate.casefold()
            for candidate in research_plan.candidate_names
        }
        if recommendation.preferred_candidate and research_plan.candidate_names and recommendation.preferred_candidate.casefold() not in excluded_candidates:
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.PROMPT_ALIGNMENT_FAILURE,
                    severity=ValidationSeverity.BLOCKING,
                    candidate_name=recommendation.preferred_candidate,
                    description="The preferred candidate is outside the approved research scope.",
                    correction="Use a candidate permitted by the research plan.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

        if not recommendation.material_risks:
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.MISSING_RISK_OR_LIMITATION,
                    severity=ValidationSeverity.ERROR,
                    description="The recommendation does not disclose material risks.",
                    correction="Add material risks and limitations before approval.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

        if (
            recommendation.outcome.value in {
                "ranked_recommendation",
                "qualified_recommendation",
            }
            and recommendation.missing_information
        ):
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.MISSING_EVIDENCE,
                    severity=ValidationSeverity.WARNING,
                    candidate_name=recommendation.preferred_candidate,
                    description=(
                        "Material information remains missing: "
                        + "; ".join(recommendation.missing_information)
                    ),
                    correction="Collect the missing evidence before final approval.",
                    target=CorrectionTarget.SOURCE_SELECTION,
                )
            )

        unsafe_text = recommendation.rationale.casefold()
        if any(phrase in unsafe_text for phrase in _UNSAFE_PHRASES):
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.HUMAN_REVIEW_BOUNDARY_FAILURE,
                    severity=ValidationSeverity.BLOCKING,
                    description="The recommendation contains unsafe return or trade language.",
                    correction="Rewrite the recommendation as informational research for human review.",
                    target=CorrectionTarget.FINANCIAL_ANALYSIS,
                )
            )

        if not research_request.original_prompt.strip():
            findings.append(
                self._finding(
                    workflow_id=workflow_id,
                    category=ValidationCategory.PROMPT_ALIGNMENT_FAILURE,
                    severity=ValidationSeverity.BLOCKING,
                    description="The original research request is empty.",
                    correction="Restore the original user request.",
                    target=CorrectionTarget.ORCHESTRATOR,
                )
            )

    @staticmethod
    def _blocking_outcome(
        findings: list[ValidationFinding],
    ) -> ValidationOutcome:
        """Choose a correction outcome from blocking findings."""

        if any(
            finding.category
            in {
                ValidationCategory.HUMAN_REVIEW_BOUNDARY_FAILURE,
                ValidationCategory.INVALID_CITATION,
            }
            for finding in findings
        ):
            return ValidationOutcome.REJECTED

        return ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Split text into lowercase word/number tokens.

        `_claim_text_for_evidence` always ends a claim with a
        sentence-final period ("...for 2026."), and the `.` in the
        character class below is needed to keep decimal numbers like
        "3.108" as one token. Left alone, that same character class
        also glues a sentence-final period onto whatever word precedes
        it ("2026." instead of "2026"), so a bare year at the end of a
        claim would never match the same year appearing mid-sentence
        in the evidence it's citing. Stripping a trailing "." off each
        token (a real decimal number never ends in one) fixes that
        without giving up decimal-number matching.
        """

        return {
            token.rstrip(".")
            for token in re.findall(r"[a-z0-9.]+", text.casefold())
        }

    @staticmethod
    def _text_supported(claim: str, evidence: str) -> bool:
        """Require meaningful lexical overlap for a citation."""

        claim_tokens = {
            token
            for token in EvidenceValidationService._tokenize(claim)
            if token not in _STOP_WORDS and len(token) > 2
        }
        evidence_tokens = EvidenceValidationService._tokenize(evidence)
        return len(claim_tokens & evidence_tokens) >= 2

    @staticmethod
    def _finding(
        *,
        workflow_id: UUID,
        category: ValidationCategory,
        description: str,
        correction: str,
        target: CorrectionTarget,
        severity: ValidationSeverity = ValidationSeverity.BLOCKING,
        candidate_name: str | None = None,
        affected_claim: str | None = None,
        affected_calculation_id: UUID | None = None,
        source_ids: list[UUID] | None = None,
        evidence_ids: list[UUID] | None = None,
    ) -> ValidationFinding:
        """Build a valid structured validation finding."""

        return ValidationFinding(
            workflow_id=workflow_id,
            category=category,
            severity=severity,
            candidate_name=candidate_name,
            affected_claim=affected_claim,
            affected_calculation_id=affected_calculation_id,
            source_ids=source_ids or [],
            evidence_ids=evidence_ids or [],
            description=description,
            required_correction=correction,
            correction_target=target,
        )

    @staticmethod
    def _summary(
        outcome: ValidationOutcome,
        findings: list[ValidationFinding],
    ) -> str:
        """Create a concise validation summary."""

        return (
            f"Validation outcome: {outcome.value}. "
            f"Findings: {len(findings)}."
        )


class EvidenceLookup:
    """Read-only lookup support for validation and agent tools."""

    def __init__(
        self,
        *,
        sources: list[SourceRecord],
        evidence: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
    ) -> None:
        """Index authoritative workflow records for read-only access."""

        self.sources = {record.source_id: record for record in sources}
        self.evidence = {record.evidence_id: record for record in evidence}
        self.calculations = {
            record.calculation_id: record for record in calculations
        }

    def get_source(self, source_id: UUID) -> SourceRecord | None:
        """Return one known source record."""

        return self.sources.get(source_id)

    def get_evidence(self, evidence_id: UUID) -> ExtractedEvidence | None:
        """Return one known evidence record."""

        return self.evidence.get(evidence_id)

    def get_calculation(self, calculation_id: UUID) -> CalculatedMetric | None:
        """Return one known calculation record."""

        return self.calculations.get(calculation_id)


class ValidationCorrectionRouter:
    """Group validation findings by their declared correction target."""

    @staticmethod
    def route(
        result: ValidationResult,
    ) -> dict[CorrectionTarget, list[ValidationFinding]]:
        """Return findings grouped for bounded orchestrator routing."""

        routed: dict[CorrectionTarget, list[ValidationFinding]] = {}
        for finding in result.findings:
            routed.setdefault(finding.correction_target, []).append(finding)
        return routed