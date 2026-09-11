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
