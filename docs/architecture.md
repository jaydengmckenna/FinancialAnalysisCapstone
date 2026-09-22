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
- Five LLM-driven agents, plus one deterministic validation stage that is
  named and shaped like an agent but makes no model call.
- Tavily as the sole content-retrieval source (search and raw page content
  in one call; no separate HTTP-retrieval or HTML-parsing stage).
- A deterministic, generic financial-calculation tool, plus a deterministic
  yfinance-backed fallback tool for filling numeric gaps web evidence
  didn't cover.
- Pydantic data contracts.
- Deterministic validation and file-writing functions.
- Human review as the final decision boundary.

The six named workflow stages are:

1. Research Planning Agent.
2. Source Selection Agent.
3. Evidence Extraction Agent.
4. Financial Analysis Agent.
5. Evidence Validation Agent (deterministic — see below).
6. Report Writing Agent.

The orchestrator controls workflow order, validates handoffs, retries a
bounded number of times when evidence is incomplete, and prevents a
non-approved analysis from ever producing a report.

## Architectural Principle

Agents are used for tasks requiring interpretation, judgment, comparison,
or written synthesis.

Deterministic Python code is used for tasks with defined inputs, rules, and
outputs.

Three of the five LLM agents — Source Selection, Financial Analysis, and
Report Writing — own their own tool and call it directly as part of their
own model-driven tool-calling loop, rather than being driven by
deterministic Python after the fact. The orchestrator invokes these agents
and reads back their result; it does not know about, or call, their
underlying tools itself.

### Agent Responsibilities

Agents are responsible for:

- Interpreting the user's research request.
- Creating a research plan.
- Selecting relevant candidate sources from search results.
- Extracting structured evidence from a selected source's content.
- Interpreting financial evidence and computing candidate metrics.
- Producing a preliminary research conclusion.
- Writing the approved research report.

Evidence validation — deciding whether that conclusion is defensible — is
handled deterministically instead; see below.

### Deterministic Responsibilities

Python components are responsible for:

- Workflow orchestration, including the bounded retry loop.
- Pydantic validation of every data contract.
- Web-search execution via Tavily (search and raw content in one call).
- Financial calculations (generic growth/margin/ratio/difference
  operations) and yfinance-backed gap-filling.
- Evidence validation: traceability, support, consistency, safety-language,
  and conflict checks — no model call.
- Identifier and citation-authorization validation.
- Report-structure validation and Markdown file writing.
- Retry-limit enforcement and error handling.

## Component Overview

### Deterministic Python Orchestrator

The orchestrator (`ResearchOrchestrator.run()`) receives the original
prompt and controls the workflow.

It:

- Invokes agents and tools in the approved order.
- Tracks the current run's intermediate results as plain attributes
  (`self.last_*`) for introspection and testing — not a formal
  `WorkflowState`/`StageResult` contract. That formal state-tracking layer
  was scoped in Phase 3 but deliberately descoped during Phase 9 review as
  unnecessary restructuring this late in the project, since the simpler
  approach is provably safe (conservative, not unsafe); see
  `docs/design-tradeoffs.md` §1.
- Retries exactly once when evidence gaps or an evidence-validation request
  for additional research exist, re-running Source Selection with those
  specific requests and accumulating the new round's evidence and sources
  onto the first round's rather than discarding them.
- Stops without generating a report if evidence validation still has not
  approved the result after that one retry — regardless of which
  non-approved outcome caused it. No report is ever written for an
  unapproved analysis; see `docs/test-results.md` and
  `tests/workflow/test_orchestrator.py`'s three end-to-end tests, which
  cover the approved-first-try, approved-after-retry, and
  never-approved-after-retry paths.
- Invokes the deterministic financial-calculation and evidence-validation
  logic between agent calls.

The orchestrator coordinates the process but does not perform financial
reasoning.

### Research Planning Agent

The Research Planning Agent converts the user's natural-language request
into structured intake data and an approved `ResearchPlan`.

It has no tools (`tools=[]`); it produces structured output directly, with
no model-driven tool-calling loop.

Its outputs include:

- `IntakeResult`
- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`
- `ResearchPlan`

### Source Selection Agent

The Source Selection Agent calls a Tavily search tool and a submission
tool directly, searching for and selecting the pages that should proceed
to evidence extraction.

Its primary output is:

- `SourceSelection`

There is no separate HTTP-retrieval or HTML-parsing stage: Tavily returns
each result's raw page content in the same search response, and Phase 5B/5C
intentionally excluded a `requests` + `BeautifulSoup` pipeline in favor of
that. See `constitution/techstack.md` ("Content Retrieval").

### Evidence Extraction Agent

The Evidence Extraction Agent reads one selected source's raw content at a
time and extracts structured evidence relevant to the research plan's
evidence requirements, via its own submission tool.

Its primary output is:

- A `SourceRecord` (built deterministically from the selected source) plus
  a list of `ExtractedEvidence` records and any evidence gaps the agent
  could not fill from that source.

### Financial Analysis Agent

The Financial Analysis Agent interprets validated evidence and calls a
deterministic, generic calculation tool (growth, margin, ratio, and
difference operations, rather than a separate calculator per financial
metric).

It also owns a second deterministic tool, `FinancialDataTool`
(yfinance-backed), which it calls itself in plain Python — not offered to
the model as a callable tool — to fill numeric evidence gaps that web
search alone did not reliably find, verified live across multiple
companies.

The current project scope is single-candidate research throughout, so this
agent scores one candidate's performance rather than comparing multiple;
the data contracts still carry multi-candidate comparison fields, reserved
for potential future expansion rather than implemented now. See
`docs/design-tradeoffs.md` §5.

It produces:

- `CandidateAnalysis`
- Preliminary `RecommendationResult`

### Evidence Validation Agent (Deterministic)

Despite the name, this stage makes no model call — it is 100%
deterministic Python (`EvidenceValidationService`), by design, wrapped in
an `EvidenceValidationAgent`-shaped interface so the orchestrator can treat
it like the other stages.

It independently determines whether the preliminary conclusion and its
claims are:

- Traceable to source evidence or deterministic calculations.
- Evidence-supported.
- Internally consistent, including a materiality-threshold conflict check
  across sources reporting the same candidate/metric/period (differences
  beyond 5% are disclosed as a non-blocking `WARNING`, not silently
  resolved or treated as blocking).
- Free of unsafe or guaranteed-return language.
- Appropriately qualified (material risks disclosed).

Its primary output is:

- `ValidationResult`, with an outcome of `approved`,
  `analysis_correction_required`, `additional_research_required`,
  `insufficient_evidence`, or `rejected`.

The Evidence Validation stage does not create a separate investment
recommendation.

### Report Writing Agent

The Report Writing Agent transforms the approved findings into a clear,
cited Markdown report. It owns and calls its own `ReportWriterTool`
directly, the same way the Financial Analysis Agent owns its calculation
tool — the orchestrator does not hold or invoke a separate report-writing
or file-writing step itself.

It returns both:

- The validated `ReportDraft`.
- The `ReportArtifact` the tool produced (the written Markdown file's
  path and metadata).

The agent does not perform new research, introduce new financial facts, or
change the approved recommendation. Every report includes a human-review
statement; human review is required before acting on any recommendation
regardless of confidence level.

### Deterministic File Writing

`ReportWriterTool` validates the approved payload, restricts the output
path to the configured output directory, and writes the Markdown report.
A disk-level write failure (`OSError`) is caught and re-raised as a
`ValueError`, so it flows through the same bounded-retry handling as every
other tool failure instead of crashing the workflow.

No separate JSON workflow-state artifact is written — that would have
required the formal `WorkflowState`/`StageResult` contracts described
above, which were deliberately descoped.

## Primary Workflow

The primary workflow is:

```text
User Prompt
    ↓
Request Interpretation and Intake Validation
    ↓
Research Planning
    ↓
Source Selection (Tavily search + raw content)
    ↓
Evidence Extraction
    ↓
Financial Analysis (calculation tool + yfinance fallback)
    ↓
Evidence Validation (deterministic)
    ↓
Report Writing (owns its own file-writing tool)
    ↓
Human Review
```

## Retry and Termination Behavior

```text
Evidence gaps or additional research requested
→ one retry: re-run Source Selection with those specific requests,
  accumulate new evidence/sources onto the prior round

Still not approved after that retry
→ workflow stops; no report is generated

Approved (first try or after the retry)
→ Report Writing Agent runs; a report is generated
```

The workflow retries at most once per run and does not continue
indefinitely. This is a deliberately conservative design: an unresolved
gap after one targeted retry produces no report rather than a weaker one,
since there is no way to flag partial confidence within a report that
does not exist yet. See `constitution/roadmap.md`'s Phase 10 section for
the tests that verify each branch of this behavior.

## Trust Boundaries

### User Input

User input is untrusted until it has been interpreted and validated against
the intake data contracts.

### Search Results

Search results are discovery records and are not treated as verified
evidence; the Source Selection Agent's judgment (and the deterministic
identity checks in `_validate_source_selection_identity`) stand between a
raw search result and anything downstream treating it as usable.

### Retrieved Content

A source's raw content (from Tavily) is untrusted external text. It is
read for evidence, never executed as instructions — the Evidence
Extraction and Report Writing system prompts both explicitly forbid
following any instruction found inside retrieved or cited content, and
this boundary is pinned by
`test_prompt_injection_in_evidence_is_not_workflow_instruction` and
`tests/prompts/test_report_prompts.py`.

### Model Output

Every agent's structured output is validated against its Pydantic data
contract before the next stage can use it; malformed or incomplete output
is rejected and retried rather than passed downstream as-is.

### Recommendation Content

No recommendation reaches a report unless Evidence Validation approves it.
Guaranteed-return language, missing risk disclosure, and citations to
unapproved or unrelated evidence are all rejected deterministically before
a report can be written.

### Output Path

`ReportWriterTool` restricts every write to the configured output
directory; a path that attempts to escape it is rejected rather than
followed.
