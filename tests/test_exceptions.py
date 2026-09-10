"""Tests for application exceptions."""

from fin_automation.exceptions import (
    CalculationError,
    ConfigurationError,
    EvidenceValidationError,
    FinancialAutomationError,
    ParsingError,
    ReportGenerationError,
    ResearchError,
    RetrievalError,
    WorkflowError,
)


def test_application_exceptions_share_common_base() -> None:
    """Application exceptions should inherit from the common base."""

    exception_types = [
        ConfigurationError,
        WorkflowError,
        ResearchError,
        RetrievalError,
        ParsingError,
        CalculationError,
        EvidenceValidationError,
        ReportGenerationError,
    ]

    for exception_type in exception_types:
        assert issubclass(
            exception_type,
            FinancialAutomationError,
        )


def test_retrieval_and_parsing_errors_are_research_errors() -> None:
    """Retrieval and parsing failures should be research failures."""

    assert issubclass(RetrievalError, ResearchError)
    assert issubclass(ParsingError, ResearchError)


def test_exception_preserves_message() -> None:
    """Application exceptions should preserve their error messages."""

    error = CalculationError(
        "Revenue growth cannot be calculated."
    )

    assert str(error) == (
        "Revenue growth cannot be calculated."
    )