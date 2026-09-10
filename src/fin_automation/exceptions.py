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