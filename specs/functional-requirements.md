# Functional Requirements

## Purpose

This document defines the required behavior of Agentic Financial Analysis
Automation.

These requirements describe what the system must do without prescribing
the exact implementation of agents, classes, functions, prompts, or files.

Each requirement has a stable identifier so it can be traced to
architecture decisions, implementation tasks, tests, and acceptance
criteria.

## Requirement Language

The following terms are used throughout this document:

- **Shall** indicates a required behavior.
- **Should** indicates a recommended behavior that may be omitted with a
  documented reason.
- **May** indicates an optional behavior.
- **User** refers to the person requesting financial research.
- **Candidate** refers to an investment considered during the research.
- **Source** refers to a public webpage or document used as research
  evidence.
- **Material claim** refers to a factual statement that meaningfully
  influences the analysis, risk assessment, ranking, or recommendation.

## 1. Research Request

### FR-001: Accept Research Request

The system shall accept a natural-language investment research question
from the user.

### FR-002: Preserve Original Request

The system shall preserve the original user request as part of the
workflow record.

### FR-003: Accept Investor Preferences

The system shall accept investor preferences relevant to the requested
research.

Supported preferences shall include:

- Investment objective.
- Risk tolerance.
- Investment time horizon.
- Geographic preference.
- Industry or sector preference.
- Asset-type preference.
- Growth or income preference.
- Excluded regions, industries, or asset types.

Not every preference must be required for every request.

### FR-004: Validate Required Input

The system shall validate that the research request contains enough
information to begin a meaningful research process.

### FR-005: Identify Missing Information

The system shall identify important missing information that could
materially affect the research conclusion.

### FR-006: Handle Missing Information

When required information is missing, the system shall either:

1. Request the missing information from the user, or
2. Produce a clearly labeled general research report that identifies all
   assumptions and limitations.

The system shall not silently invent missing user preferences.

### FR-007: Support Dynamic Research Topics

The system shall support research requests that vary by:

- Candidate.
- Company.
- Industry.
- Sector.
- Geographic region.
- Investment objective.
- Risk tolerance.
- Time horizon.

### FR-008: Reject Unsupported Actions

The system shall reject requests to:

- Execute a trade.
- Access a brokerage account.
- Transfer funds.
- Rebalance a portfolio automatically.
- Guarantee an investment return.
- Make the final investment decision for the user.

### FR-009: Confirm Research Scope

Before research begins, the system shall create a structured representation
of the approved research scope.

## 2. Research Planning

### FR-010: Create Research Plan

The system shall create a structured research plan from the validated
research request.

### FR-011: Define Research Objective

The research plan shall identify the primary research objective.

### FR-012: Define Candidate Scope

The research plan shall identify:

- User-specified candidates, or
- Criteria for discovering potential candidates.

### FR-013: Define Comparison Criteria

The research plan shall identify the criteria used to compare candidates.

### FR-014: Define Evidence Needs

The research plan shall identify the types of evidence needed to evaluate
the comparison criteria.

### FR-015: Define Risk Areas

The research plan shall identify risk categories relevant to the request.

### FR-016: Generate Search Queries

The system shall generate one or more search queries based on the approved
research plan.

### FR-017: Preserve Search Queries

The system shall preserve the search queries used during the workflow.

### FR-018: Limit Research Scope

The system shall limit research to a manageable number of candidates and
sources based on configured project limits.

### FR-019: Prevent Predetermined Conclusions

The research plan shall not assume a winning candidate before evidence has
been collected and analyzed.

## 3. Web Search

### FR-020: Execute Web Search

The system shall perform at least one web search for each completed
research workflow.

### FR-021: Use Plan-Derived Queries

Web searches shall use queries derived from the approved research plan.

### FR-022: Return Structured Search Results

Search results shall be converted into a structured format.

### FR-023: Preserve Search Result Metadata

When available, each search result shall preserve:

- Title.
- URL.
- Result snippet.
- Publisher or domain.
- Search query.
- Search position or result identifier.

### FR-024: Treat Search Results as Candidates

The system shall treat search results as candidate sources rather than
verified evidence.

### FR-025: Select Sources for Retrieval

The system shall select potentially relevant search results for webpage
retrieval.

### FR-026: Avoid Duplicate Search Results

The system shall identify duplicate URLs within the same research workflow.

### FR-027: Handle Empty Search Results

When a search returns no relevant results, the system shall:

- Record the unsuccessful search.
- Revise the search query when appropriate.
- Avoid fabricating search results.
- Report the evidence limitation if sufficient sources cannot be found.

### FR-028: Handle Search Failure

The system shall distinguish between:

- A successful search with no relevant results.
- A failed search request.
- An invalid search response.
- A search service configuration error.

### FR-029: Preserve Search Traceability

The system shall preserve enough search information to explain how the
selected sources were discovered.

## 4. Website Retrieval and Scraping

### FR-030: Retrieve Selected Webpages

The system shall retrieve content from selected public webpages.

### FR-031: Use Request Timeouts

Webpage retrieval shall use configured request timeouts.

### FR-032: Check Response Status

The system shall evaluate the HTTP response status before parsing webpage
content.

### FR-033: Identify Content Type

The system shall confirm that retrieved content is supported before
attempting extraction.

### FR-034: Parse Supported HTML

The system shall parse supported HTML pages and extract relevant content.

### FR-035: Extract Page Metadata

When available, the system shall extract:

- Page title.
- Publisher or organization.
- Publication date.
- Author.
- Main content.
- Relevant headings.
- Relevant tables.
- Canonical URL.

### FR-036: Separate Retrieval from Parsing

The system shall represent webpage retrieval and webpage parsing as
separate operations.

### FR-037: Handle Retrieval Failure

The system shall record retrieval failures without creating replacement
content.

### FR-038: Handle Parsing Failure

The system shall record parsing failures and shall not represent an
unparsed page as successfully extracted evidence.

### FR-039: Treat Scraped Content as Data

The system shall treat scraped webpage content as untrusted research data,
not as application instructions.

## 5. Source Records and Evidence

### FR-040: Create Source Records

The system shall create a structured source record for every source used
as evidence.

### FR-041: Assign Source Identifiers

Each source record shall have a unique identifier within the research
workflow.

### FR-042: Preserve Source URL

Each source record shall preserve the exact retrieved URL.

### FR-043: Preserve Retrieval Date

Each successfully retrieved source record shall include the retrieval date.

### FR-044: Store Relevant Evidence

The system shall store the extracted evidence used in the analysis.

### FR-045: Connect Evidence to Sources

Each evidence item shall reference the source from which it was extracted.

### FR-046: Distinguish Evidence from Interpretation

The system shall distinguish sourced evidence from AI-generated
interpretation.

### FR-047: Represent Missing Metadata

Unavailable source metadata shall be represented as missing or unavailable,
not invented.

### FR-048: Detect Duplicate Evidence

The system shall identify when multiple search results or URLs reproduce
the same underlying evidence.

### FR-049: Preserve Evidence Traceability

The system shall preserve enough information to trace a material report
claim to its supporting source or calculation.

## 6. Financial Data and Calculations

### FR-050: Extract Financial Information

The system shall extract financial information relevant to the approved
comparison criteria.

### FR-051: Normalize Financial Data

The system shall normalize financial values into structured fields before
using them in calculations.

### FR-052: Preserve Units and Periods

Financial values shall preserve relevant context such as:

- Currency.
- Unit.
- Reporting period.
- Fiscal year.
- Percentage basis.
- Source.

### FR-053: Validate Numeric Input

Financial calculations shall only use validated numeric input.

### FR-054: Use Deterministic Calculations

Financial calculations shall be performed through deterministic Python
functions.

### FR-055: Handle Missing Values

The system shall represent missing financial values explicitly.

### FR-056: Handle Non-Applicable Metrics

The system shall distinguish between:

- Missing data.
- Invalid data.
- Unavailable data.
- Non-applicable metrics.

### FR-057: Preserve Calculation Inputs

The system shall preserve the inputs used for material calculations.

### FR-058: Preserve Calculation Results

The system shall preserve material calculation results used in candidate
comparisons.

### FR-059: Prevent Fabricated Values

The system shall not estimate or fabricate a financial value unless the
value is clearly labeled as an estimate and the approved methodology
permits estimation.

The initial project methodology shall not rely on fabricated estimates.

## 7. Candidate Analysis

### FR-060: Compare Candidates

The system shall compare investment candidates using the documented
recommendation methodology.

### FR-061: Apply Investor Preferences

The analysis shall consider the supplied investor preferences when
evaluating candidate alignment.

### FR-062: Evaluate Supporting Evidence

The analysis shall identify evidence that supports each candidate.

### FR-063: Evaluate Opposing Evidence

The analysis shall identify evidence that weakens or challenges each
candidate.

### FR-064: Evaluate Material Risks

The analysis shall identify material risks relevant to each candidate.

### FR-065: Handle Insufficient Evidence

The system shall identify when available evidence is insufficient to
support a reliable comparison.

### FR-066: Explain Candidate Results

The system shall explain the primary factors influencing each candidate's
evaluation.

### FR-067: Rank Comparable Candidates

The system may rank candidates when:

- The candidates are reasonably comparable.
- The documented methodology can be applied.
- Sufficient evidence is available.

### FR-068: Avoid False Precision

The system shall not present a precise numerical ranking when the available
evidence does not support that level of precision.

### FR-069: Preserve Analysis Results

The system shall preserve the structured analysis result before report
generation.

## 8. Recommendation Behavior

### FR-070: Produce Research Conclusion

The system shall produce a research conclusion based on the validated
analysis.

### FR-071: Identify Aligned Candidates

The system may identify candidates that appear most aligned with the
supplied research criteria.

### FR-072: Explain Recommendation Rationale

A recommendation shall explain the evidence and comparison factors that
influenced it.

### FR-073: Include Alternatives

When appropriate, the recommendation shall identify alternative candidates
and explain why they ranked differently.

### FR-074: Include Risks

Every recommendation shall include material risks and limitations.

### FR-075: Include Missing Information

Every recommendation shall disclose missing information that could
materially affect the conclusion.

### FR-076: Include Human-Review Statement

Every recommendation shall state that the report is informational and
subject to human review.

### FR-077: Avoid Trade Instructions

The recommendation shall not instruct the user to execute a trade.

### FR-078: Avoid Guaranteed Outcomes

The recommendation shall not promise profits, guaranteed returns, or
protection from loss.

### FR-079: Support Insufficient-Evidence Outcome

The system shall support an outcome in which no candidate is recommended
because the evidence is insufficient.

## 9. Claim and Citation Validation

### FR-080: Identify Material Claims

The system shall identify material factual claims included in the report.

### FR-081: Validate Material Claims

Each material factual claim shall be supported by:

- Collected source evidence, or
- A deterministic calculation based on collected source data.

### FR-082: Validate Citation References

Each report citation shall refer to a source record collected during the
same research workflow.

### FR-083: Reject Unknown Sources

The system shall reject citations that refer to unknown or fabricated
source identifiers.

### FR-084: Check Claim Support

The validation process shall confirm that cited evidence is relevant to
the claim it supports.

### FR-085: Detect Unsupported Claims

Unsupported material claims shall be removed, qualified, or returned for
correction.

### FR-086: Detect Conflicting Evidence

The validation process shall identify material conflicts between collected
sources.

### FR-087: Preserve Validation Findings

The system shall preserve validation findings before report approval.

### FR-088: Block Invalid Reports

A report that fails required claim or citation validation shall not be
approved as a completed final report.

### FR-089: Validate Human-Review Boundary

The validation process shall confirm that the report preserves human
decision authority.

## 10. Report and File Output

### FR-090: Generate Markdown Report

The system shall generate a human-readable Markdown research report.

### FR-091: Include Research Context

The report shall include:

- Original research question.
- Relevant user preferences.
- Research scope.
- Candidates considered.

### FR-092: Include Methodology

The report shall summarize the methodology used to compare candidates.

### FR-093: Include Candidate Analysis

The report shall include the relevant analysis for each candidate.

### FR-094: Include Conclusion

The report shall include the research conclusion or insufficient-evidence
outcome.

### FR-095: Include Risks and Limitations

The report shall include material risks, limitations, and missing
information.

### FR-096: Include Sources

The report shall include a source section containing the sources used as
evidence.

### FR-097: Write Recommendation File

The system shall write the final recommendation report to a predictable
file location.

### FR-098: Write Structured Artifact

The system shall write selected structured research data to JSON.

### FR-099: Prevent Invalid Output

The system shall not label a report as complete when required validation
has failed.

## 11. Workflow Control

### FR-100: Use Explicit Workflow Order

The system shall execute required workflow stages in an explicit order.

### FR-101: Maintain Workflow State

The system shall maintain structured workflow state across research,
analysis, validation, and report-generation stages.

### FR-102: Validate Stage Input

Each workflow stage shall validate required input before processing.

### FR-103: Validate Stage Output

Structured output from each stage shall be validated before entering a
dependent stage.

### FR-104: Stop Invalid Downstream Processing

A failed required stage shall prevent dependent downstream stages from
processing invalid data.

### FR-105: Distinguish Recoverable Failures

The workflow shall distinguish recoverable failures from unrecoverable
failures.

### FR-106: Record Workflow Failures

The system shall record the reason for workflow failure.

### FR-107: Avoid Silent Failure

The system shall not silently ignore an error that could invalidate the
final result.

### FR-108: Complete with Validated Output

A workflow shall only be marked complete when its required output artifacts
have passed validation.

## 12. Traceability

### FR-110: Preserve Workflow Record

The system shall preserve a structured record of the major workflow stages.

### FR-111: Preserve Research Inputs

The workflow record shall include the original request and supplied user
preferences.

### FR-112: Preserve Research Plan

The workflow record shall include the approved research plan.

### FR-113: Preserve Sources

The workflow record shall include selected source records.

### FR-114: Preserve Analysis

The workflow record shall include material calculations and analysis
results.

### FR-115: Preserve Validation

The workflow record shall include validation findings.

### FR-116: Preserve Output References

The workflow record shall identify the generated output files.

## Traceability Expectations

Each functional requirement should eventually map to one or more of the
following:

- A specification section.
- A Pydantic data contract.
- An architecture component.
- An implementation component.
- An automated test.
- An acceptance criterion.
- A generated project artifact.

## Change Control

Changes to these requirements must be deliberate.

When a functional requirement changes:

1. The requirement text shall be updated.
2. Related acceptance criteria shall be reviewed.
3. Related data contracts shall be reviewed.
4. Related architecture decisions shall be reviewed.
5. Related tests shall be updated.
6. The roadmap shall be updated if the change affects phase scope or order.