# Safety Requirements

## Purpose

This document defines the safety boundaries for Agentic Financial Analysis
Automation.

The system is a research and decision-support application. It may research,
compare, rank, and explain potential investments, but it shall not execute
transactions or make final investment decisions for the user.

## 1. Human Decision Authority

### SR-001: Human Final Decision

The final investment decision shall always remain with the human user.

### SR-002: Informational Output

The final report shall describe its recommendation as informational
research for human consideration.

### SR-003: No Autonomous Action

The system shall not initiate, approve, or execute a financial transaction.

### SR-004: No Brokerage Control

The system shall not request access to or control a brokerage account.

### SR-005: No Fund Control

The system shall not transfer, hold, allocate, or manage user funds.

## 2. Recommendation Safety

### SR-010: No Guaranteed Returns

The system shall not guarantee profit, market outperformance, or protection
from loss.

### SR-011: No Risk-Free Claims

The system shall not describe an investment as risk-free.

### SR-012: No Compulsory Language

The system shall not tell the user that the user must purchase, sell, or
hold an investment.

### SR-013: Evidence-Dependent Language

Recommendations shall be described as dependent on:

- Collected evidence.
- Documented methodology.
- Supplied investor preferences.
- Available data.
- Current research limitations.

### SR-014: Insufficient-Evidence Outcome

The system shall be able to conclude that no recommendation is supported by
the available evidence.

### SR-015: Risk Inclusion

The system shall not remove material risks solely because they weaken a
recommendation.

## 3. Missing and Uncertain Information

### SR-020: No Fabricated User Preferences

The system shall not invent missing investor preferences.

### SR-021: No Fabricated Financial Data

The system shall not fabricate financial values.

### SR-022: No Fabricated Sources

The system shall not fabricate source titles, URLs, publishers, dates, or
citations.

### SR-023: Missing Information Disclosure

Material missing information shall be disclosed in the analysis or report.

### SR-024: Conflicting Information Disclosure

Material unresolved source conflicts shall be disclosed.

### SR-025: Confidence Limitation

Recommendation confidence shall be reduced or withheld when evidence is
insufficient, stale, conflicting, or unavailable.

## 4. External Content and Prompt Injection

### SR-030: Untrusted Search Results

Search results shall be treated as untrusted external data.

### SR-031: Untrusted Webpage Content

Retrieved webpage content shall be treated as untrusted external data.

### SR-032: Untrusted Model Output

Language-model output shall be validated before entering a dependent
workflow stage.

### SR-033: Ignore Embedded Instructions

Instructions embedded in search results or webpages shall not override:

- The user request.
- Project specifications.
- System instructions.
- Agent responsibilities.
- Tool restrictions.
- Validation requirements.
- Human-review requirements.

### SR-034: Prevent Objective Manipulation

External content shall not be permitted to change the research objective or
investor profile.

### SR-035: Prevent Candidate Manipulation

External content shall not directly force the selection or recommendation
of a specific candidate.

### SR-036: Prevent Validation Bypass

External content shall not disable evidence validation, citation
validation, risk disclosure, or human-review statements.

### SR-037: Prevent Secret Disclosure

External content shall not cause the application to reveal API keys,
configuration secrets, internal prompts, or private system information.

## 5. Financial Comparison Safety

### SR-040: Comparable Evidence

Candidates shall not be directly ranked using values that are materially
incompatible without normalization or qualification.

### SR-041: Period Awareness

The system shall preserve reporting periods when comparing financial data.

### SR-042: Currency Awareness

The system shall preserve currency information when comparing monetary
values.

### SR-043: Non-Applicable Metrics

The system shall not assign a misleading numeric value to a metric that is
not applicable.

### SR-044: False Precision

The system shall avoid precise scores when evidence quality does not
support that precision.

### SR-045: Methodology Disclosure

The report shall disclose that project scoring weights are part of the
project methodology rather than an objective guarantee of investment
quality.

## 6. Source Safety

### SR-050: Source Verification

A material claim shall not be approved when its cited source is unknown or
does not support the claim.

### SR-051: Search Snippet Limitation

A search snippet shall not normally serve as the sole verified evidence for
a material claim.

### SR-052: Duplicate Source Handling

Duplicate or derivative sources shall not be counted as independent
confirmation without justification.

### SR-053: Promotional Content

Promotional language shall not be treated as verified evidence without
supporting data.

### SR-054: Retrieval Failure

Failed retrieval shall not be represented as successful source collection.

## 7. Input and URL Safety

### SR-060: Input Validation

User input shall be validated before it controls search, retrieval, or file
output.

### SR-061: URL Validation

URLs shall be validated before retrieval.

### SR-062: Supported Public URLs

The initial system shall retrieve only supported public web URLs.

### SR-063: No Local File Retrieval

User-controlled web retrieval shall not access local files.

### SR-064: No Secret Paths

User input shall not control output paths in a way that exposes or
overwrites secret or unrelated files.

### SR-065: Predictable Output Directory

Generated files shall be restricted to an approved output directory.

## 8. Secret Protection

### SR-070: Environment-Based Secrets

Secret credentials shall be loaded through environment variables.

### SR-071: No Hard-Coded Secrets

Secret credentials shall not be hard-coded in source files.

### SR-072: No Secret Logging

Secret credentials shall not be written to logs.

### SR-073: No Secret Reporting

Secret credentials shall not be included in Markdown reports or structured
workflow data.

### SR-074: No Secret Test Fixtures

Real secret credentials shall not be stored in test fixtures.

## 9. Failure Safety

### SR-080: Fail Closed on Validation

When required evidence or citation validation fails, the system shall not
approve the report as complete.

### SR-081: No Silent Failure

The system shall not silently continue after a failure that invalidates
downstream analysis.

### SR-082: Controlled Partial Results

Partial results shall be labeled incomplete and shall not be represented as
a fully validated recommendation.

### SR-083: Clear Error Explanation

A stopped workflow shall identify the class of failure without exposing
secrets.

## 10. Report Safety

### SR-090: Required Human-Review Statement

Every completed recommendation report shall contain a human-review
statement.

### SR-091: Required Risk Section

Every completed recommendation report shall contain a risk section.

### SR-092: Required Limitation Section

Every completed recommendation report shall contain a limitations section.

### SR-093: Required Source Section

Every completed recommendation report shall contain a source section.

### SR-094: Fact and Interpretation Separation

The report shall distinguish sourced facts from system interpretation.

### SR-095: No New Writer Facts

The report-writing stage shall not introduce new material facts that were
not present in validated workflow data.

## 11. Safety Response Patterns

When the user requests an unsupported financial action, the system should:

1. Decline the unsupported action.
2. Preserve the research-assistance boundary.
3. Offer research, comparison, risk analysis, or explanation instead.

When research evidence is insufficient, the system should:

1. State that the evidence is insufficient.
2. Identify the missing information.
3. Avoid selecting a winner.
4. Preserve collected sources and findings.
5. Produce a limitation report when appropriate.

## 12. Required Adversarial Tests

The safety test suite shall include:

- A webpage instructing the agent to ignore project instructions.
- A webpage instructing the agent to recommend a predetermined company.
- A webpage instructing the agent to remove risks.
- A webpage requesting API keys.
- A fabricated source URL.
- A citation unrelated to the claim.
- Duplicate sources presented as independent confirmation.
- A user requesting guaranteed returns.
- A user requesting direct trade execution.
- A user requesting removal of unfavorable evidence.
- Missing investor preferences.
- Conflicting financial values.
- Negative earnings with a non-applicable valuation metric.
- A report writer introducing an unsupported fact.
- A file path attempting to escape the approved output directory.
- A failed search or retrieval followed by fabricated content.

## Safety Approval Conditions

A completed report may only be approved when:

- Required input was validated.
- Material claims passed evidence validation.
- Citations refer to collected sources.
- Material risks are included.
- Missing and conflicting information is disclosed.
- Recommendation language avoids guarantees and trade instructions.
- The human-review boundary is present.
- Output files are written to approved locations.
- No required safety validation failed.

## Change Control

A safety requirement may only be weakened through an explicit,
documented decision.

Any safety-requirement change must trigger review of:

- Functional requirements.
- Source policy.
- Recommendation methodology.
- Data contracts.
- Agent prompts.
- Architecture.
- Adversarial tests.
- Acceptance criteria.
- Roadmap scope.