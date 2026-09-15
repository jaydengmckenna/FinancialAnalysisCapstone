# Agentic Financial Analysis Automation

## Project Status

Phase 5, the simplified Phase 6 financial-analysis slice, and Phase 7
evidence validation are complete. Phase 8 is focused on generating one
validated Markdown report for human review.

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