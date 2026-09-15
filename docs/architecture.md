# System Architecture

## Purpose

This document explains the architecture of Agentic Financial Analysis
Automation and the major design decisions represented in the accompanying
architecture diagram.

The architecture supports a fixed research workflow in which specialized
agents perform judgment-based tasks and deterministic Python components
perform predictable operations.

## Architecture Overview

The system currently uses:

- A deterministic Python orchestrator.
- Five specialized AI agents.
- Deterministic web-research tools.
- One deterministic generic financial-calculation tool.
- Pydantic data contracts.
- Deterministic validation and file-writing functions.
- Human review as the final decision boundary.

The five agents are:

1. Research Planning Agent.
2. Source Selection Agent.
3. Financial Analysis Agent.
4. Evidence Validation Agent.
5. Report Writing Agent.

The orchestrator controls workflow order, validates handoffs, routes
corrections, enforces retry limits, and prevents invalid downstream
processing.

## Architectural Principle

Agents are used for tasks requiring interpretation, judgment, comparison,
or written synthesis.

Deterministic Python code is used for tasks with defined inputs, rules, and
outputs.

### Agent Responsibilities

Agents are responsible for:

- Interpreting the user's research request.
- Creating a research plan.
- Selecting relevant candidate sources.
- Interpreting financial evidence.
- Comparing investment candidates.
- Producing a preliminary research conclusion.
- Validating whether the conclusion is defensible.
- Writing the approved research report.

### Deterministic Responsibilities

Python components are responsible for:

- Workflow orchestration.
- Pydantic validation.
- Web-search execution.
- URL validation.
- HTTP retrieval.
- HTML parsing.
- Duplicate URL detection.
- Financial calculations.
- Identifier validation.
- Report-structure validation.
- Markdown file writing.
- Retry-limit enforcement.
- Error handling.

## Component Overview

### Deterministic Python Orchestrator

The orchestrator receives the original prompt and controls the workflow.

It:

- Preserves workflow state.
- Invokes agents and tools in the approved order.
- Validates each stage's output.
- Stops for user clarification when required.
- Routes additional-research requests.
- Routes analysis corrections.
- Enforces retry limits.
- Prevents failed validation from producing an approved report.
- Invokes the deterministic file writers.

The orchestrator coordinates the process but does not perform financial
reasoning.

### Research Planning Agent

The Research Planning Agent converts the user's natural-language request
into structured intake data and an approved `ResearchPlan`.

Its outputs include:

- `IntakeResult`
- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`
- `ResearchPlan`

### Source Selection Agent

The Source Selection Agent evaluates structured search results and selects
the pages that should proceed to retrieval.

Its primary output is:

- `SourceSelection`

Web search execution, webpage retrieval, HTML parsing, and evidence
extraction remain deterministic operations.

### Financial Analysis Agent

The Financial Analysis Agent interprets validated evidence and deterministic
generic calculation results. The current slice supports growth, margin,
ratio, and difference operations rather than a separate calculator for each
financial metric.

It compares candidates using the approved methodology and produces:

- `CandidateAnalysis`
- Preliminary `RecommendationResult`

Financial arithmetic is performed by deterministic calculation tools.

### Evidence Validation Agent

The Evidence Validation Agent independently determines whether the
preliminary conclusion and its claims are:

- Traceable to source evidence or deterministic calculations.
- Evidence-supported.
- Internally consistent.
- Responsive to the user request.
- Appropriately qualified.
- Compliant with project requirements.

Its primary output is:

- `ValidationResult`

The Evidence Validation Agent does not create a separate investment
recommendation.

### Report Writing Agent

The Report Writing Agent transforms the approved findings into a clear,
cited Markdown report.

Its primary output is:

- `ReportDraft`

The agent does not perform new research, introduce new financial facts, or
change the approved recommendation.

### Deterministic File Writers

Deterministic Python functions validate and write:

- Markdown research report.
- JSON workflow artifact.

File writers restrict output to the configured output directory.

## Primary Workflow

The primary workflow is:

```text
User Prompt
    ↓
Request Interpretation
    ↓
Intake Validation
    ↓
Research Planning
    ↓
Web Search
    ↓
Source Selection
    ↓
Webpage Retrieval and Parsing
    ↓
Financial Calculations and Analysis
    ↓
Evidence Validation
    ↓
Report Writing
    ↓
Report Validation and File Writing
    ↓
Human Review
```

## Validation and Correction Paths

The orchestrator supports controlled correction paths:

```text
Missing investor information
→ Human clarification

Missing research evidence
→ Source Selection Agent

Retrieval or parsing failure
→ Deterministic retrieval handling

Invalid financial input
→ Financial calculation stage

Unsupported analysis
→ Financial Analysis Agent

Approved conclusion
→ Report Writing Agent

Insufficient evidence
→ Limitation report
```

Correction paths are bounded by configured retry limits.

The workflow shall not continue indefinitely.

## Trust Boundaries

### User Input

User input is untrusted until it has been interpreted and validated against
the intake data contracts.

### Search Results

Search results are discovery records and are not treated as 