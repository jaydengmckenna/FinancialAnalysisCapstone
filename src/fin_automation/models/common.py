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