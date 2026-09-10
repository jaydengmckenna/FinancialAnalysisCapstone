# Non-Functional Requirements

## Purpose

This document defines the quality attributes and operational constraints
for Agentic Financial Analysis Automation.

Functional requirements describe what the system does. Non-functional
requirements describe how reliably, safely, transparently, and
maintainably the system must perform those behaviors.

## 1. Reliability

### NFR-001: Deterministic Calculations

The same validated financial inputs shall produce the same deterministic
calculation results.

### NFR-002: Explicit Failure Behavior

The system shall return an explicit failure result when a required
operation cannot be completed.

### NFR-003: No Fabricated Recovery

The system shall not replace failed searches, failed retrievals, missing
data, or invalid model output with fabricated content.

### NFR-004: Controlled External Calls

External HTTP, search, and language-model calls shall use configured
timeouts where supported.

### NFR-005: Limited Retries

Retry behavior shall be finite and configurable.

### NFR-006: Partial Evidence Disclosure

When part of the research succeeds and part fails, the system shall
identify which results are complete, incomplete, or unavailable.

## 2. Data Integrity

### NFR-010: Schema Validation

Structured data exchanged between major workflow stages shall be validated
against approved Pydantic models.

### NFR-011: Source Preservation

Source URLs and identifiers shall not be silently altered after collection.

### NFR-012: Calculation Traceability

Material calculation results shall retain their input values and units.

### NFR-013: Missing Data Representation

Missing values shall be represented explicitly rather than replaced with
zero, empty text, or invented values.

### NFR-014: Artifact Consistency

The Markdown report and structured JSON artifacts shall describe the same
completed workflow result.

## 3. Security

### NFR-020: Secret Management

API keys and secret configuration values shall be loaded from environment
variables.

### NFR-021: Version-Control Protection

Secret credentials, `.env`, and local virtual environments shall not be
committed to version control.

### NFR-022: Log Protection

Logs shall not contain API keys, authentication tokens, or secret
configuration values.

### NFR-023: Untrusted External Content

Search results, webpage content, and language-model responses shall be
treated as untrusted input.

### NFR-024: URL Validation

URLs shall be validated before webpage retrieval.

### NFR-025: Supported Retrieval Schemes

The initial application shall only retrieve supported public web URLs.

### NFR-026: Local Resource Protection

The scraper shall not use user-supplied URLs to access local files or
unsupported local network resources.

## 4. Privacy

### NFR-030: Data Minimization

The system shall collect only user information required to support the
research request.

### NFR-031: No Brokerage Credentials

The system shall not request or store brokerage credentials.

### NFR-032: No Banking Credentials

The system shall not request or store banking credentials.

### NFR-033: No Unnecessary Personal Data

The system shall not require personally identifying information when
general investor preferences are sufficient.

### NFR-034: Report Review

Generated reports shall avoid exposing secrets, local file paths, or
private configuration values.

## 5. Transparency and Explainability

### NFR-040: Methodology Visibility

The system shall make the comparison methodology understandable to a
human reviewer.

### NFR-041: Recommendation Explanation

A recommendation shall identify the main evidence, calculations, and risks
that influenced the result.

### NFR-042: Information-Type Separation

Reports shall distinguish:

- Sourced facts.
- Deterministic calculations.
- Model-generated interpretations.
- Recommendations.

### NFR-043: Uncertainty Visibility

The system shall disclose missing, conflicting, stale, or insufficient
evidence.

### NFR-044: Human Authority

The report shall clearly state that final investment decisions belong to
the human user.

## 6. Maintainability

### NFR-050: Modular Components

Search, retrieval, parsing, calculations, validation, orchestration, and
file writing shall be implemented as separable components.

### NFR-051: Limited Agent Access

Each agent shall receive only the tools required for its responsibility.

### NFR-052: Central Configuration

Environment-dependent settings shall be managed through a central
configuration component.

### NFR-053: Clear Naming

Public models, functions, agents, and modules shall use names that reflect
their actual responsibilities.

### NFR-054: Documented Assumptions

Material implementation assumptions shall be documented.

### NFR-055: Dependency Control

The project shall avoid dependencies that do not support a documented
requirement.

## 7. Testability

### NFR-060: Independently Testable Calculations

Financial calculation functions shall be testable without a language model
or web connection.

### NFR-061: Mockable External Services

Search, language-model, and HTTP dependencies shall be replaceable with
mocks during unit testing.

### NFR-062: Repeatable Scraper Tests

Scraping behavior shall be testable with saved HTML fixtures.

### NFR-063: Structured Agent Output

Agent output used by later workflow stages shall conform to structured
contracts.

### NFR-064: Requirement Traceability

Major requirements shall map to tests or documented acceptance checks.

### NFR-065: Adversarial Testing

The test suite shall include malicious or misleading webpage content,
unsupported claims, malformed input, and external-service failures.

## 8. Reproducibility

### NFR-070: Environment Documentation

The project shall document how to create a Python 3.12.3 virtual
environment and install dependencies.

### NFR-071: Dependency Record

Required Python dependencies shall be recorded in `requirements.txt`.

### NFR-072: Example Configuration

Required environment variables shall be documented in `.env.example`.

### NFR-073: Preserved Research Context

Example reports shall preserve enough structured context to explain how
the result was produced.

### NFR-074: Stable Test Fixtures

Unit tests shall not depend unnecessarily on changing live webpages or
paid external services.

## 9. Usability

### NFR-080: Understandable Input

The system shall accept a natural-language research request.

### NFR-081: Actionable Input Errors

Input-validation errors shall identify the missing or invalid field.

### NFR-082: Readable Report Structure

The Markdown report shall use clear headings and organized sections.

### NFR-083: Clear Limitations

The report shall present risks and limitations in language understandable
to the intended user.

### NFR-084: Predictable Output Location

Generated artifacts shall be saved to predictable configured locations.

## 10. Performance and Resource Control

### NFR-090: Bounded Research Scope

The number of candidates, search queries, sources, retries, and external
calls shall be bounded by configuration.

### NFR-091: No Indefinite Operations

The application shall not wait or retry indefinitely.

### NFR-092: Avoid Duplicate Processing

The workflow should avoid retrieving and processing the same source
multiple times within one research run unless a documented reason exists.

### NFR-093: Appropriate Data Processing

The application shall use pandas only when it improves the clarity or
reliability of tabular operations.

## 11. Compatibility

### NFR-100: Python Compatibility

The project shall support Python 3.12.3.

### NFR-101: Environment Independence

Application code shall not rely on hard-coded developer-specific paths.

### NFR-102: Markdown Portability

Human-readable reports shall use standard Markdown where practical.

### NFR-103: JSON Portability

Structured artifacts shall use valid JSON-compatible data.

## 12. Observability

### NFR-110: Workflow Logging

The system shall log major workflow stage transitions.

### NFR-111: Failure Logging

The system shall log the category and location of recoverable and
unrecoverable failures.

### NFR-112: Validation Logging

The system shall record whether required validation passed or failed.

### NFR-113: Report Logging

The system shall record whether output files were written successfully.

### NFR-114: Safe Logging

Logs shall exclude secret credentials and unnecessarily sensitive user
information.

## 13. Documentation Quality

### NFR-120: Current README

README instructions shall reflect the current implementation.

### NFR-121: Architecture Consistency

The architecture diagram shall match the implemented workflow.

### NFR-122: Specification Consistency

Implementation behavior shall remain consistent with approved
specifications.

### NFR-123: Prompt Decision Record

Representative development prompts and decisions shall be preserved in the
prompt journal or AI-assistance artifact.

## Change Control

A non-functional requirement may be revised when implementation or testing
shows that the original quality constraint is incomplete, impractical, or
insufficient.

Changes must include:

1. The updated requirement.
2. The reason for the change.
3. Review of affected tests.
4. Review of affected architecture.
5. A roadmap update when phase scope or order changes.