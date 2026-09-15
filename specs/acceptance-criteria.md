# Acceptance Criteria

## Purpose

This document defines the observable conditions that must be satisfied for
Agentic Financial Analysis Automation to meet its approved requirements.

Acceptance criteria describe pass or fail behavior. They do not prescribe
the exact implementation.

## Acceptance Status Definitions

Each criterion may have one of the following statuses:

- **Not Tested**
- **Passed**
- **Failed**
- **Blocked**
- **Not Applicable**

A criterion shall not be marked Passed without supporting test output or
documented inspection evidence.

## 1. Research Request Acceptance

### AC-001: Valid Request Accepted

**Given** a research request containing an investment objective, risk
tolerance, time horizon, and research scope,

**When** the request is validated,

**Then** the system creates a structured research request and preserves the
original user text.

Maps to:

- FR-001
- FR-002
- FR-003
- FR-004

### AC-002: Missing Required Preference Identified

**Given** a personalized research request missing a required preference,

**When** the request is validated,

**Then** the system identifies the missing field and does not silently
invent a value.

Maps to:

- FR-005
- FR-006
- SR-020
- NFR-081

### AC-003: Unsupported Action Rejected

**Given** a request to execute a trade or access a brokerage account,

**When** the request is processed,

**Then** the system rejects the action and preserves the research-only
boundary.

Maps to:

- FR-008
- SR-003
- SR-004
- SR-005

## 2. Research Planning Acceptance

### AC-010: Research Plan Created

**Given** a valid research request,

**When** research planning completes,

**Then** the output includes:

- Research objective.
- Candidate scope.
- Comparison criteria.
- Required evidence.
- Risk areas.
- Search queries.

Maps to:

- FR-010 through FR-016

### AC-011: Search Queries Preserved

**Given** an approved research plan,

**When** web research begins,

**Then** every executed search query is stored in the workflow record.

Maps to:

- FR-017
- FR-029
- FR-112

### AC-012: No Predetermined Winner

**Given** a new research request,

**When** the research plan is created,

**Then** the plan does not identify a winning candidate before evidence
collection and analysis.

Maps to:

- FR-019

## 3. Web Search Acceptance

### AC-020: Web Search Executed

**Given** an approved research plan,

**When** the research workflow runs successfully,

**Then** at least one plan-derived web search is performed.

Maps to:

- FR-020
- FR-021

### AC-021: Search Results Structured

**Given** a successful search response,

**When** search results are processed,

**Then** each selected result is represented in a validated structure with
available title, URL, snippet, and query metadata.

Maps to:

- FR-022
- FR-023

### AC-022: Duplicate Search Result Detected

**Given** multiple search results containing the same normalized URL,

**When** results are processed,

**Then** the duplicate is identified and does not create independent
evidence automatically.

Maps to:

- FR-026
- SR-052

### AC-023: Empty Search Handled

**Given** a valid search that returns no relevant results,

**When** the workflow handles the response,

**Then** the system records the outcome, avoids fabricated results, and
reports the evidence limitation if research cannot continue.

Maps to:

- FR-027
- FR-028
- NFR-003

## 4. Website Retrieval and Scraping Acceptance

### AC-030: Selected Webpage Retrieved

**Given** a supported public webpage URL,

**When** retrieval succeeds,

**Then** the system records the retrieval status and passes the returned
HTML to the parser.

Maps to:

- FR-030
- FR-032
- FR-033

### AC-031: Webpage Parsed

**Given** supported HTML containing identifiable content,

**When** the parser processes the page,

**Then** relevant content and available metadata are extracted into a
structured source record.

Maps to:

- FR-034
- FR-035
- FR-040

### AC-032: Retrieval Timeout Handled

**Given** a webpage request that exceeds the configured timeout,

**When** retrieval fails,

**Then** the workflow records the failure and does not create fabricated
page content.

Maps to:

- FR-031
- FR-037
- NFR-004
- NFR-003

### AC-033: Parsing Failure Handled

**Given** malformed or unsupported page content,

**When** parsing fails,

**Then** the source is marked as unparsed and is not represented as
successfully extracted evidence.

Maps to:

- FR-038
- SR-054

### AC-034: Embedded Instruction Ignored

**Given** a webpage containing instructions to ignore project rules and
recommend a predetermined candidate,

**When** the content is parsed and analyzed,

**Then** the instruction is treated as webpage data and does not change the
workflow objective, candidate ranking, or validation requirements.

Maps to:

- FR-039
- SR-031 through SR-036
- NFR-023

## 5. Source and Evidence Acceptance

### AC-040: Source Record Created

**Given** a successfully retrieved and parsed source,

**When** the source is stored,

**Then** it receives a unique source identifier and preserves its URL,
retrieval date, and available metadata.

Maps to:

- FR-040
- FR-041
- FR-042
- FR-043

### AC-041: Evidence Connected to Source

**Given** an extracted evidence item,

**When** it is stored,

**Then** it references the source record from which it was extracted.

Maps to:

- FR-044
- FR-045
- FR-049

### AC-042: Missing Metadata Not Invented

**Given** a source without an available author or publication date,

**When** its source record is created,

**Then** the unavailable fields remain explicitly missing.

Maps to:

- FR-047
- NFR-013

### AC-043: Duplicate Evidence Does Not Inflate Confidence

**Given** multiple pages reproducing the same original claim,

**When** evidence strength is evaluated,

**Then** those pages are not automatically counted as independent
confirmation.

Maps to:

- FR-048
- SR-052

### AC-044: Conflicting Evidence Preserved

**Given** two credible sources containing materially conflicting values,

**When** evidence is evaluated,

**Then** both values are preserved and the unresolved conflict is disclosed.

Maps to:

- FR-086
- SR-024

## 6. Financial Calculation Acceptance

### AC-050: Deterministic Calculation

**Given** the same validated financial inputs,

**When** a financial calculation is executed multiple times,

**Then** the same result is returned each time.

Maps to:

- FR-054
- NFR-001
- NFR-060

### AC-051: Units and Periods Preserved

**Given** a financial value with a currency, unit, and reporting period,

**When** the value is normalized,

**Then** the currency, unit, reporting period, and source remain available.

Maps to:

- FR-051
- FR-052

### AC-052: Missing Input Handled

**Given** a calculation with a required missing value,

**When** the function is invoked,

**Then** it returns or raises a defined missing-input result and does not
silently use zero.

Maps to:

- FR-053
- FR-055
- NFR-013

### AC-053: Non-Applicable Metric Handled

**Given** a candidate for which a financial metric is not applicable,

**When** the metric is evaluated,

**Then** it is marked not applicable rather than assigned a misleading
score.

Maps to:

- FR-056
- SR-043

### AC-054: Calculation Traceable

**Given** a material calculated value used in the report,

**When** the calculation record is inspected,

**Then** its formula inputs and source references are available.

Maps to:

- FR-057
- FR-058
- NFR-012

## 7. Analysis and Recommendation Acceptance

### AC-060: Candidates Compared Using Methodology

**Given** comparable candidates with sufficient evidence,

**When** analysis completes,

**Then** each candidate is evaluated using the approved methodology.

Maps to:

- FR-060
- NFR-040

### AC-061: Investor Profile Applied

**Given** a valid investor profile,

**When** candidates are evaluated,

**Then** the analysis explains how the supplied preferences affect candidate
alignment.

Maps to:

- FR-061

### AC-062: Supporting and Opposing Evidence Included

**Given** candidate evidence containing both favorable and unfavorable
information,

**When** analysis completes,

**Then** both types of evidence appear in the candidate analysis.

Maps to:

- FR-062
- FR-063

### AC-063: Risks Included

**Given** identified material risks,

**When** a recommendation is generated,

**Then** the report includes those risks even when they weaken the preferred
candidate.

Maps to:

- FR-064
- FR-074
- SR-015

### AC-064: Ranking Explained

**Given** a ranked recommendation,

**When** the report is generated,

**Then** the report explains the primary factors that caused candidates to
rank differently.

Maps to:

- FR-066
- FR-072
- NFR-041

### AC-065: Insufficient Evidence Supported

**Given** material missing or conflicting evidence,

**When** the available evidence cannot support a reliable ranking,

**Then** the system produces an insufficient-evidence or research-shortlist
outcome instead of forcing a winning candidate.

Maps to:

- FR-065
- FR-079
- SR-014

### AC-066: No Guaranteed Outcome

**Given** a completed recommendation,

**When** its language is validated,

**Then** it contains no promise of profit, guaranteed return, or protection
from loss.

Maps to:

- FR-078
- SR-010
- SR-011

### AC-067: No Trade Instruction

**Given** a completed recommendation,

**When** its language is validated,

**Then** it does not direct the user to execute a trade.

Maps to:

- FR-077
- SR-012

## 8. Claim and Citation Acceptance

### AC-070: Material Claims Supported

**Given** a material factual claim in the draft report,

**When** validation runs,

**Then** the claim references collected evidence or a traceable
deterministic calculation, and any calculated value matches the recorded
formula, result, units, periods, and input evidence.

Maps to:

- FR-080
- FR-081
- SR-050

### AC-071: Known Citation Required

**Given** a citation in the report,

**When** citation validation runs,

**Then** the citation refers to a source record from the same workflow.

Maps to:

- FR-082
- FR-083

### AC-072: Citation Must Support Claim

**Given** a valid source identifier that points to unrelated evidence,

**When** claim validation runs,

**Then** the claim fails validation.

Maps to:

- FR-084
- FR-085

### AC-073: Invalid Report Blocked

**Given** a report containing an unsupported material claim,

**When** required validation fails,

**Then** the workflow does not approve the report as complete.

Maps to:

- FR-088
- SR-080

### AC-074: Report Writer Cannot Add Facts

**Given** validated analysis data,

**When** the report writer creates the report,

**Then** no new material facts appear unless they were present in the
validated workflow data.

Maps to:

- SR-095

## 9. Report Output Acceptance

### AC-080: Markdown Report Written

**Given** a fully validated workflow,

**When** report generation completes,

**Then** a Markdown report is written to the approved output directory.

Maps to:

- FR-090
- FR-097
- SR-065

### AC-081: Required Report Sections Present

**Given** a completed report,

**When** its structure is inspected,

**Then** it contains:

- Research question.
- Investor preferences.
- Research scope.
- Candidates considered.
- Methodology.
- Candidate analysis.
- Conclusion.
- Risks.
- Limitations.
- Sources.
- Human-review statement.

Maps to:

- FR-091 through FR-096
- SR-090 through SR-093

### AC-084: Invalid Output Not Marked Complete

**Given** failed required validation,

**When** output handling runs,

**Then** any partial artifact is labeled incomplete and is not represented
as the final approved report.

Maps to:

- FR-099
- SR-082

## 10. Workflow Acceptance

### AC-090: Explicit Stage Order

**Given** a valid research request,

**When** the workflow executes,

**Then** research planning, evidence collection, analysis, validation, and
report generation occur in the approved order.

Maps to:

- FR-100

### AC-091: Structured Workflow State

**Given** an active workflow,

**When** a stage completes,

**Then** the workflow state records its validated output or failure.

Maps to:

- FR-101
- FR-110

### AC-092: Invalid Stage Output Rejected

**Given** a stage returning output that fails its Pydantic contract,

**When** the next stage attempts to consume it,

**Then** the invalid output is rejected and dependent processing does not
continue.

Maps to:

- FR-102
- FR-103
- FR-104
- NFR-010

### AC-093: Failure Reason Preserved

**Given** an unrecoverable workflow failure,

**When** the workflow stops,

**Then** the failure category and explanation are preserved without
exposing secrets.

Maps to:

- FR-105
- FR-106
- FR-107
- SR-083

### AC-094: Completion Requires Valid Output

**Given** a workflow with incomplete required stages,

**When** completion status is evaluated,

**Then** the workflow is not marked complete.

Maps to:

- FR-108

## 11. Security and Privacy Acceptance

### AC-100: Secrets Loaded from Environment

**Given** a configured development environment,

**When** the application starts,

**Then** required credentials are loaded from environment variables and are
not hard-coded in application source.

Maps to:

- NFR-020
- SR-070
- SR-071

### AC-101: Secrets Excluded from Logs

**Given** application logging during external-service calls,

**When** logs are inspected,

**Then** API keys and authentication secrets are absent.

Maps to:

- NFR-022
- SR-072
- NFR-114

### AC-102: Local File URL Rejected

**Given** a user-controlled local file URL,

**When** webpage retrieval is requested,

**Then** the request is rejected.

Maps to:

- SR-061
- SR-062
- SR-063

### AC-103: Output Path Restricted

**Given** an output filename attempting to escape the approved output
directory,

**When** file writing is requested,

**Then** the request is rejected or safely normalized within the approved
directory.

Maps to:

- SR-064
- SR-065

## 12. Reproducibility Acceptance

### AC-110: Clean Environment Installation

**Given** Python 3.12.3 and a clean virtual environment,

**When** dependencies are installed from `requirements.txt`,

**Then** the source package and test suite can be loaded.

Maps to:

- NFR-070
- NFR-071
- NFR-100

### AC-111: Example Configuration Present

**Given** the repository,

**When** setup documentation is reviewed,

**Then** `.env.example` documents the required environment-variable names
without containing real credentials.

Maps to:

- NFR-072

### AC-112: Tests Avoid Live Dependency

**Given** the unit test suite,

**When** tests run,

**Then** search, language-model, and HTTP behavior can be tested through
mocks and saved fixtures without requiring live paid services.

Maps to:

- NFR-061
- NFR-062
- NFR-074

## 13. Capstone Artifact Acceptance

### AC-120: Constitution Present

The repository shall contain:

- `constitution/mission.md`
- `constitution/tech-stack.md`
- `constitution/roadmap.md`

### AC-121: Specifications Present

The repository shall contain:

- `specs/functional-requirements.md`
- `specs/non-functional-requirements.md`
- `specs/source-policy.md`
- `specs/safety-requirements.md`
- `specs/recommendation-methodology.md`
- `specs/acceptance-criteria.md`

### AC-122: Architecture Present

The repository shall contain:

- Architecture documentation.
- Mermaid diagram source.
- Exported architecture PNG.

### AC-123: Tests Present

The repository shall contain happy-path and adversarial tests.

### AC-124: README Present

The repository shall contain a README that matches the current
implementation.

### AC-125: AI-Assistance Artifact Present

The repository shall contain selected prompt examples and decision
rationale in `COPILOT.md` or the approved AI-assistance documentation.

### AC-126: Example Outputs Present

The repository shall contain:

- An example financial research article.
- An example investment recommendation report.
- Supporting structured artifacts.

## Phase 2 Completion Criteria

Phase 2 is complete when:

- Functional requirements are documented.
- Non-functional requirements are documented.
- Source-selection and citation rules are documented.
- Safety boundaries are documented.
- The initial recommendation methodology is documented.
- Acceptance criteria map to the major requirements.
- The specification files are consistent with the mission and technology
  stack.
- Remaining model and architecture decisions can proceed without inventing
  undocumented behavior.

## Change Control

When an acceptance criterion changes:

1. Its mapped requirements shall be reviewed.
2. Its planned tests shall be reviewed.
3. Its data-contract implications shall be reviewed.
4. Its architecture implications shall be reviewed.
5. The roadmap shall be updated when phase scope or order changes.
6. The reason for the change shall be preserved.