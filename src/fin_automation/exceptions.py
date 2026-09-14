"""Custom exceptions used throughout the application."""


class FinancialAutomationError(Exception):
    """Base exception for application-specific errors."""


class ConfigurationError(FinancialAutomationError):
    """Raised when application configuration is missing or invalid."""


class WorkflowError(FinancialAutomationError):
    """Raised when the workflow cannot continue."""


class ResearchError(FinancialAutomationError):
    """Raised when web research cannot be completed."""


class RetrievalError(ResearchError):
    """Raised when a selected webpage cannot be retrieved."""


class ParsingError(ResearchError):
    """Raised when retrieved webpage content cannot be parsed."""


class CalculationError(FinancialAutomationError):
    """Raised when a financial calculation cannot be completed."""


class EvidenceValidationError(FinancialAutomationError):
    """Raised when evidence validation prevents workflow continuation."""


class ReportGenerationError(FinancialAutomationError):
    """Raised when a report or output artifact cannot be generated."""

class ClarificationRequiredError(WorkflowError):
    """Raised when research cannot proceed without user clarification."""

    def __init__(
        self,
        missing_fields: list[str],
        clarification_questions: list[str],
    ) -> None:
        """Initialize the clarification requirement.

        Args:
            missing_fields: Required fields absent from intake.
            clarification_questions: Questions that should be presented
                to the user.
        """

        self.missing_fields = list(missing_fields)
        self.clarification_questions = list(
            clarification_questions
        )

        super().__init__(
            "Research planning cannot continue because user "
            "clarification is required."
        )