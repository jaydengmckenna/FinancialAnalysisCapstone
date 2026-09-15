"""Shared enumerations used by the application's data contracts."""

from enum import StrEnum


class RiskTolerance(StrEnum):
    """Supported investor risk-tolerance levels."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class InvestmentObjective(StrEnum):
    """Supported primary investment objectives."""

    GROWTH = "growth"
    INCOME = "income"
    CAPITAL_PRESERVATION = "capital_preservation"
    BALANCED = "balanced"
    UNSPECIFIED = "unspecified"


class TimeHorizon(StrEnum):
    """Supported investment time horizons."""

    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    UNSPECIFIED = "unspecified"


class RequestType(StrEnum):
    """Supported investment-research request types."""

    CANDIDATE_DISCOVERY = "candidate_discovery"
    CANDIDATE_COMPARISON = "candidate_comparison"
    SINGLE_CANDIDATE_ANALYSIS = "single_candidate_analysis"


class AssetType(StrEnum):
    """Asset types supported by the initial capstone version."""

    PUBLIC_STOCK = "public_stock"
    ADR = "adr"


class SearchPurpose(StrEnum):
    """Supported purposes for web-search queries."""

    CANDIDATE_DISCOVERY = "candidate_discovery"
    FINANCIAL_GROWTH = "financial_growth"
    PROFITABILITY = "profitability"
    BALANCE_SHEET = "balance_sheet"
    VALUATION = "valuation"
    COMPETITIVE_POSITION = "competitive_position"
    RISK_RESEARCH = "risk_research"
    SOURCE_CORROBORATION = "source_corroboration"


class SourceCategory(StrEnum):
    """Supported source-quality categories."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DISCOVERY = "discovery"
    UNSUPPORTED = "unsupported"


class WorkflowStage(StrEnum):
    """Stages that may create or receive workflow records."""

    REQUEST_INTAKE = "request_intake"
    INTAKE_VALIDATION = "intake_validation"
    RESEARCH_PLANNING = "research_planning"
    WEB_SEARCH = "web_search"
    SOURCE_SELECTION = "source_selection"
    WEB_RETRIEVAL = "web_retrieval"
    CONTENT_PARSING = "content_parsing"
    FINANCIAL_ANALYSIS = "financial_analysis"
    EVIDENCE_VALIDATION = "evidence_validation"
    REPORT_WRITING = "report_writing"
    REPORT_VALIDATION = "report_validation"
    ARTIFACT_WRITING = "artifact_writing"
    HUMAN_REVIEW = "human_review"

class SourceSelectionStatus(StrEnum):
    """Possible outcomes of source selection."""

    READY_FOR_RETRIEVAL = "ready_for_retrieval"
    ADDITIONAL_SEARCH_REQUIRED = "additional_search_required"
    INSUFFICIENT_CANDIDATE_SOURCES = (
        "insufficient_candidate_sources"
    )


class RetrievalStatus(StrEnum):
    """Possible outcomes of webpage retrieval."""

    SUCCESS = "success"
    FAILED = "failed"
    UNSUPPORTED_CONTENT = "unsupported_content"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"


class ParsingStatus(StrEnum):
    """Possible outcomes of webpage parsing."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"

class DataAvailabilityStatus(StrEnum):
    """Availability states for financial data and analysis categories."""

    AVAILABLE = "available"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    INSUFFICIENT = "insufficient"
    NOT_APPLICABLE = "not_applicable"


class CalculationType(StrEnum):
    """Deterministic calculations supported by the initial version."""

    REVENUE_GROWTH = "revenue_growth"
    NET_PROFIT_MARGIN = "net_profit_margin"
    OPERATING_PROFIT_MARGIN = "operating_profit_margin"
    DEBT_TO_EQUITY = "debt_to_equity"
    PRICE_TO_EARNINGS = "price_to_earnings"
    WEIGHTED_SCORE = "weighted_score"



class CalculationStatus(StrEnum):
    """Possible outcomes of a deterministic calculation."""

    COMPLETED = "completed"
    MISSING_INPUT = "missing_input"
    INVALID_INPUT = "invalid_input"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"

class CalculationOperation(StrEnum):
    """Calculations supported by the minimal Phase 6 implementation."""
    GROWTH_RATE = "growth_rate"
    MARGIN = "margin"
    RATIO = "ratio"
    DIFFERENCE = "difference"

class AnalysisStatus(StrEnum):
    """Possible outcomes of candidate analysis."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_COMPARABLE = "not_comparable"
    FAILED = "failed"


class RecommendationOutcome(StrEnum):
    """Supported preliminary recommendation outcomes."""

    RANKED_RECOMMENDATION = "ranked_recommendation"
    QUALIFIED_RECOMMENDATION = "qualified_recommendation"
    RESEARCH_SHORTLIST = "research_shortlist"
    NO_ALIGNED_CANDIDATE = "no_aligned_candidate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ConfidenceLevel(StrEnum):
    """Supported evidence-confidence levels."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT = "insufficient"

class ValidationOutcome(StrEnum):
    """Possible outcomes of evidence validation."""

    APPROVED = "approved"
    ANALYSIS_CORRECTION_REQUIRED = (
        "analysis_correction_required"
    )
    ADDITIONAL_RESEARCH_REQUIRED = (
        "additional_research_required"
    )
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REJECTED = "rejected"


class ValidationSeverity(StrEnum):
    """Severity levels for validation findings."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"


class ValidationCategory(StrEnum):
    """Supported validation-finding categories."""

    UNSUPPORTED_CLAIM = "unsupported_claim"
    INVALID_CITATION = "invalid_citation"
    IRRELEVANT_CITATION = "irrelevant_citation"
    MISSING_EVIDENCE = "missing_evidence"
    CALCULATION_INPUT_PROBLEM = (
        "calculation_input_problem"
    )
    INCOMPATIBLE_COMPARISON = "incompatible_comparison"
    UNDISCLOSED_CONFLICT = "undisclosed_conflict"
    MISSING_RISK_OR_LIMITATION = (
        "missing_risk_or_limitation"
    )
    OVERSTATED_CONFIDENCE = "overstated_confidence"
    PROMPT_ALIGNMENT_FAILURE = "prompt_alignment_failure"
    HUMAN_REVIEW_BOUNDARY_FAILURE = (
        "human_review_boundary_failure"
    )


class CorrectionTarget(StrEnum):
    """Components that may receive a validation correction."""

    SOURCE_SELECTION = "source_selection"
    RETRIEVAL = "retrieval"
    PARSING = "parsing"
    FINANCIAL_CALCULATION = "financial_calculation"
    FINANCIAL_ANALYSIS = "financial_analysis"
    ORCHESTRATOR = "orchestrator"
    REPORT_WRITING = "report_writing"
    HUMAN_CLARIFICATION = "human_clarification"

class ReportType(StrEnum):
    """Supported final report types."""

    RESEARCH_REPORT = "research_report"
    INSUFFICIENT_EVIDENCE_REPORT = (
        "insufficient_evidence_report"
    )


class ArtifactType(StrEnum):
    """Supported generated artifact types."""

    MARKDOWN_REPORT = "markdown_report"
    JSON_WORKFLOW = "json_workflow"


class ArtifactStatus(StrEnum):
    """Possible artifact-generation outcomes."""

    PENDING = "pending"
    CREATED = "created"
    FAILED = "failed"


class WorkflowStatus(StrEnum):
    """Possible overall workflow states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    CORRECTION_REQUIRED = "correction_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(StrEnum):
    """Possible execution states for one workflow stage."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class ErrorSeverity(StrEnum):
    """Severity levels for structured workflow errors."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
