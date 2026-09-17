# Agentic Financial Analysis Automation

## Project Status

Phases 1 through 8 are complete. Phase 9 (Complete Product Workflow) has
connected intake, research planning, source selection, evidence
extraction, financial calculation, evidence validation, and report
writing into one working end-to-end product: a natural-language
research request produces a validated Markdown report in `outputs/`.
A deterministic `FinancialDataTool` (yfinance-backed) fills numeric
evidence gaps that web search alone cannot reliably find. One Phase 9
deliverable — formal `WorkflowState`/`StageResult` tracking and routed
analysis-correction behavior — remains an open scope decision; see
`constitution/roadmap.md` for details. Phase 10 (testing and quality
verification) has not started.

## Purpose

This project supports preliminary investment research. It converts a user
research request into structured research plans, source-backed evidence,
and deterministic financial calculations for human review.

The project is intentionally smaller than a production investment platform.
It demonstrates bounded agent communication, traceable evidence, and safe
workflow decisions rather than real-time investing or portfolio management.

## Current Scope

Implemented capabilities include:

- Intake and research-plan generation.
- Tavily-based search and source selection.
- Selected-source content preservation.
- Structured evidence extraction with source lineage.
- Generic deterministic financial calculations for growth, margin, ratio,
	and difference operations.
- Decimal arithmetic with currency, units, periods, and evidence references.
- A Financial Analysis Agent that requests bounded calculations and
	interprets their results.
- Pydantic contracts for workflow, analysis, recommendation, validation,
  and report data.

The current Phase 6 implementation does not attempt to provide a large
catalog of named calculators. Generic operations are selected by the agent
and identified by a metric name supplied by the approved research plan.

## Completed Phase 7

Phase 7 implements an Evidence Validation Agent and deterministic
validation helpers. Validation checks:

- Citation references against known source and evidence identifiers.
- Research claims against relevant extracted evidence.
- Numerical claims against the exact calculation inputs and results.
- Candidate, unit, currency, and reporting-period compatibility.
- Disclosure of missing, conflicting, favorable, and unfavorable evidence.
- Recommendation confidence and human-review boundaries.
- Prompt-injection resistance in source content.

Validation may approve the preliminary result, request analysis
correction, request additional research, declare insufficient evidence, or
reject the result. Only approved data may proceed to report generation.

## Boundaries

The system does not execute trades, access brokerage accounts, transfer
funds, guarantee returns, provide final investment decisions, or replace
professional financial advice. Source content is untrusted data and cannot
change workflow instructions.

## Workflow

```text
User request
	-> intake and research plan
	-> search and source selection
	-> evidence extraction
	-> generic deterministic calculations
	-> preliminary financial analysis
	-> evidence, citation, and calculation validation
	-> validated Markdown report
	-> human review
```

## Example Prompt and Interpreting a Report

A prompt that works well with the current implementation names one
candidate, one metric, and specific fiscal years:

```text
What is Microsoft's fiscal-year revenue growth from FY2023 to FY2024
based on total revenue in USD billions, and what qualified research
conclusion can be drawn for a high-risk, long-term growth investor?
```

Open-ended prompts (e.g. "is this a good investment based on its
current financials and trajectory") still work, but tend to pull in a
wider, messier mix of quarterly figures, forecasts, and price targets,
which makes an inconclusive result more likely.

Before acting on any generated report:

- **`qualified_recommendation` means a calculation was completed and
  passed validation — it does not mean the result is favorable.** The
  system does not currently score a calculated decline differently
  from a calculated increase; check the actual value and its sign in
  the Candidate Analyses section yourself.
- **`insufficient_evidence` means no verified calculation could be
  completed**, even if the underlying sources clearly lean one
  direction. The system will not turn a qualitative impression (a
  headline, a pre-computed percentage from an uninspected source)
  into a recommendation on its own.
- **Check which periods were actually compared.** The Research
  Methodology and Candidate Analyses sections state the exact fiscal
  years or periods used. Confirm they match what you asked for.
- **Treat a "difference" calculation with extra caution.** Most
  calculations are growth rates (a percentage). If a report instead
  shows a raw dollar "difference" for a single candidate, and the two
  periods look the same, that indicates conflicting source data
  rather than a real trend.
- **Verify the cited sources directly.** Every report links its
  sources (SEC filings, investor relations pages, annual reports).
  Open them and confirm the cited figures match before relying on the
  report.
- **Re-run the prompt if a result looks off.** Web search and
  extraction are not fully deterministic; the same prompt run twice
  can return different source coverage.

Every report ends with a mandatory Human Review section. This is not
boilerplate — no report from this system is a final investment
decision.

## Repository Guide

- `constitution/`: mission, technology decisions, and roadmap.
- `specs/`: functional requirements, contracts, methodology, safety, and
	acceptance criteria.
- `docs/`: architecture documentation and Mermaid diagram.
- `src/fin_automation/`: agents, prompts, models, tools, and smoke tests.
- `tests/`: offline model, tool, prompt, and agent tests.
- `outputs/`: generated Markdown reports.

## Setup

The project targets Python 3.12. Install dependencies in the local virtual
environment:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Configure external credentials through environment variables or a local
`.env` file. Never commit credentials.

## Tests

Run the offline suite with:

```bash
.venv/bin/pytest -q
```

Live smoke tests are separate and require configured service credentials.

## Governing Documents

- [Mission](constitution/mission.md)
- [Technology stack](constitution/techstack.md)
- [Roadmap](constitution/roadmap.md)
- [Architecture](docs/architecture.md)
- [Functional requirements](specs/functional-requirements.md)
- [Data contracts](specs/data-contracts.md)
- [Agent workflows](specs/agent-workflows.md)
- [Recommendation methodology](specs/recommendation-methodology.md)
- [Acceptance criteria](specs/acceptance-criteria.md)
- [Safety requirements](specs/safety-requirements.md)

## Capstone Artifacts

The repository currently contains the constitution, specifications,
architecture diagram, implementation, and automated tests. Example reports,
prompt journals, and final workflow artifacts belong to later phases.