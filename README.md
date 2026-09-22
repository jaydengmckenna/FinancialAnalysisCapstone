# Agentic Financial Analysis Automation

## Project Status

Phases 1 through 10 are complete. Phase 11 (Documentation and Submission
Preparation) is in progress. The system runs end to end: a
natural-language research request produces either a validated Markdown
report in `outputs/`, or — if evidence validation never approves the
result, even after one bounded retry — no report at all, deliberately,
rather than a weaker or unsupported one. See `constitution/roadmap.md`
for the full phase history and `docs/design-tradeoffs.md` for the
scope decisions made along the way (most notably: single-candidate
research scope, and a simpler ad-hoc retry mechanism in place of the
formally-specified `WorkflowState` contracts).

## Purpose

This project supports preliminary investment research. It converts a
user research request into a structured research plan, source-backed
evidence, and deterministic financial calculations, producing a cited
report for human review — never a final investment decision.

## Problem Statement

Manually researching a single investment candidate — pulling filings,
extracting the right figures, checking they're comparable, and writing
up a defensible conclusion — is slow and easy to get subtly wrong (mismatched
fiscal years, uncorroborated figures, a conclusion that outruns its
evidence). This project automates that process end to end while keeping
every claim traceable to a specific source or calculation, and keeping a
human making the actual decision.

## Intended Users

Individual investors or students doing preliminary, single-candidate
investment research who want a structured, source-cited starting point —
not a trading system, a brokerage integration, or a replacement for
professional financial advice.

## Current Scope

Implemented capabilities include:

- Natural-language request interpretation and clarification-gated intake.
- Research-plan generation for one named or discovered candidate.
- Tavily-based web search and source selection (search and raw page
  content in a single call — see System Boundaries).
- Structured evidence extraction with full source lineage.
- Generic deterministic financial calculations (growth, margin, ratio,
  difference) plus a deterministic yfinance-backed fallback for numeric
  gaps web evidence didn't cover.
- Deterministic evidence validation: traceability, evidence support,
  unit/period/currency compatibility, conflict disclosure, unsafe-language
  rejection, and mandatory risk disclosure.
- A bounded single retry that accumulates newly-found evidence onto what
  a prior round already found, rather than discarding it.
- Markdown report generation, written only for an approved result.

This is intentionally smaller than a production investment platform: one
candidate at a time, one financial-performance score rather than the full
seven-category weighted methodology originally specified, and a single
retry rather than per-finding correction routing. See
`docs/design-tradeoffs.md` for why each of these was reduced, and what a
future iteration would add back.

## System Boundaries

The system does not execute trades, access brokerage accounts, transfer
funds, guarantee returns, provide a final investment decision, or replace
professional financial advice. It does not compare multiple candidates
against each other (single-candidate scope; see `docs/design-tradeoffs.md`
§5) and has no separate HTTP-retrieval or HTML-parsing stage — Tavily
returns page content directly in its search response, and a Requests +
BeautifulSoup pipeline that early specs described was intentionally never
built (`constitution/techstack.md`). Source content is untrusted data:
extraction and report-writing prompts explicitly forbid treating anything
found in retrieved content as an instruction.

## Architecture Summary

A deterministic Python orchestrator coordinates six named workflow
stages: Research Planning, Source Selection, Evidence Extraction,
Financial Analysis, Evidence Validation, and Report Writing. Five of
these are genuinely LLM-driven agents; Evidence Validation is
deterministic Python behind the same interface, by design — the
project's central safety guarantee (no unsupported or unsafe
recommendation is ever approved) depends on that decision always being
made the same way for the same input. Three agents (Source Selection,
Financial Analysis, Report Writing) own and call their own tools
directly; the orchestrator invokes the agent and reads back its result
without knowing about the tool underneath it.

Full detail, including the retry/termination behavior and the trust
boundaries between components, is in [`docs/architecture.md`](docs/architecture.md)
and the diagram at [`docs/architecture.mmd`](docs/architecture.mmd) /
[`docs/architecture.png`](docs/architecture.png).

## Repository Structure

- `constitution/`: mission, technology decisions, and roadmap.
- `specs/`: functional requirements, data contracts, methodology, safety,
  and acceptance criteria.
- `docs/`: architecture documentation and diagram, design trade-offs,
  test-results artifact, and requirement-to-test traceability mapping.
- `src/fin_automation/`: agents, prompts, models, tools, workflow
  orchestrator, and smoke-test scripts.
- `tests/`: offline model, tool, prompt, agent, and orchestrator tests —
  no live network or API access required.
- `outputs/`: generated Markdown reports and run logs (gitignored — see
  `docs/examples/` for tracked example reports).
- `CLAUDE.md`: AI-assistance documentation (prompt examples and decision
  rationale).

## Installation

The project targets Python 3.12 and uses a `src/`-layout package.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e . --no-deps
```

The second install step is required — `fin_automation` will not be
importable from `requirements.txt` alone.

## Configuration

Copy `.env.example` to `.env` and fill in real values. Never commit
`.env`.

```bash
cp .env.example .env
```

Required variables:

- `OPENAI_API_KEY` — OpenAI-compatible API key for the LLM-driven agents.
- `OPENAI_BASE_URL` — base URL for that API endpoint.
- `TAVILY_API_KEY` — Tavily API key for web search and content retrieval.
- `MODEL_ID` — model identifier passed to the OpenAI-compatible endpoint.

Optional:

- `OUTPUT_DIRECTORY` — defaults to `./outputs`.

## Usage

```bash
.venv/bin/python -m fin_automation.main
```

You'll be prompted for a research request. The run is logged to
`outputs/logs/`, and — if the result is approved — a Markdown report is
written to `outputs/`.

To capture a full run's console output alongside the report:

```bash
.venv/bin/python run_smoke_test.py
```

## Testing

```bash
.venv/bin/pytest -v
```

356 tests, no live API calls or network access — OpenAI, Tavily, and
yfinance are all mocked. A `.env` file with non-empty values is still
required for Pydantic settings validation to pass (see
`docs/test-results.md`); the values don't need to work, since nothing
in the suite actually calls out to a real service. See
[`docs/test-results.md`](docs/test-results.md) for a saved run and
per-file breakdown, and
[`docs/traceability-mapping.md`](docs/traceability-mapping.md) for how
every functional requirement maps to a specific test (or an honest note
that none exists).

## Example Input

A prompt that works well names one candidate, one metric, and specific
fiscal years:

```text
What is Microsoft's fiscal-year revenue growth from FY2023 to FY2024
based on total revenue in USD billions, and what qualified research
conclusion can be drawn for a high-risk, long-term growth investor?
```

Open-ended prompts (e.g. "is this a good investment based on its current
financials and trajectory") still work, but tend to pull in a wider,
messier mix of quarterly figures, forecasts, and price targets, which
makes an inconclusive result more likely.

## Example Output

Every generated report follows the same structure: Research Question,
Investor Profile, Research Scope, Executive Summary, Research
Methodology, Candidate Analyses, Recommendation Outcome, Material Risks,
Missing Information and Unresolved Conflicts, Limitations, Sources, and
a mandatory Human Review statement. A representative excerpt (from a
live run analyzing Nike's net-income growth):

```markdown
## Executive Summary
This report analyzes Nike's net income growth rate from fiscal year
2025 to fiscal year 2026. Data from primary and secondary sources
indicate a moderate decline in net income, with a calculated growth
rate of -3.45%. Despite this decline, the workflow results in a
qualified recommendation for Nike, supported by moderate confidence in
the evidence and evaluations.

## Human Review
Human review is required before acting on this recommendation.
```

Four full, real, unedited example reports (strong growth, modest growth,
a decline, and an insufficient-evidence case) live in
[`docs/examples/`](docs/examples/) — see that directory's index for what
each one demonstrates.

## Interpreting a Report

Before acting on any generated report:

- **`qualified_recommendation` means a calculation was completed and
  passed validation — it does not mean the result is favorable.** The
  system does not score a calculated decline differently from a
  calculated increase in terms of whether it's reported; check the
  actual value and its sign in the Candidate Analyses section yourself.
- **No report at all means validation never approved the result**, even
  after one retry — not that something crashed. Check the console output
  or log for the validation outcome and findings.
- **Check which periods were actually compared.** The Research
  Methodology and Candidate Analyses sections state the exact fiscal
  years or periods used. Confirm they match what you asked for.
- **Treat a "difference" calculation with extra caution.** Most
  calculations are growth rates (a percentage). If a report instead
  shows a raw dollar "difference" for a single candidate, and the two
  periods look the same, that indicates conflicting source data rather
  than a real trend — see `docs/design-tradeoffs.md` §3.
- **Verify the cited sources directly.** Every report links its sources.
  Open them and confirm the cited figures match before relying on the
  report.
- **Re-run the prompt if a result looks off.** Web search and extraction
  are not fully deterministic; the same prompt run twice can return
  different source coverage.

Every report ends with a mandatory Human Review section. This is not
boilerplate — no report from this system is a final investment decision.

## Safety and Limitations

- The system never guarantees a return, executes a trade, or gives an
  unqualified buy/sell instruction; unsafe language is rejected
  deterministically before a report can be written.
- A recommendation with no disclosed material risks is rejected, not
  silently approved.
- Conflicting evidence across sources for the same candidate/metric/period
  is disclosed (a non-blocking warning above a 5% materiality threshold),
  not silently resolved in either direction.
- The system does not compare multiple candidates, does not implement the
  full seven-category weighted scoring methodology, and does not
  route corrections to a specific at-fault stage — a validation issue
  triggers one bounded, general retry, and if that doesn't resolve it,
  the workflow stops without a report rather than routing to a narrower
  fix. See `docs/design-tradeoffs.md` for the full reasoning behind each
  of these.
- Known, accepted gaps (not silent ones): duplicate-source inflation and
  fabricated unsupported facts are guarded against by explicit
  system-prompt instruction, not a deterministic code check, since
  neither has a deterministic signal to check against.

## Governing Documents

- [Mission](constitution/mission.md)
- [Technology stack](constitution/techstack.md)
- [Roadmap](constitution/roadmap.md)
- [Architecture](docs/architecture.md)
- [Design trade-offs](docs/design-tradeoffs.md)
- [Functional requirements](specs/functional-requirements.md)
- [Non-functional requirements](specs/non-functional-requirements.md)
- [Data contracts](specs/data-contracts.md)
- [Agent workflows](specs/agent-workflows.md)
- [Recommendation methodology](specs/recommendation-methodology.md)
- [Source policy](specs/source-policy.md)
- [Safety requirements](specs/safety-requirements.md)
- [Acceptance criteria](specs/acceptance-criteria.md)
- [AI-assistance documentation](CLAUDE.md)

## Required-Artifact Checklist

Per `specs/acceptance-criteria.md` §13 and `constitution/roadmap.md`'s
Phase 11 section:

- [x] Constitution (`constitution/`).
- [x] Specifications (`specs/`).
- [x] Architecture documentation, Mermaid source, and PNG diagram
      (`docs/architecture.md`, `.mmd`, `.png`).
- [x] Happy-path and adversarial tests (`tests/`; see
      `docs/test-results.md`).
- [x] README matching the current implementation (this file).
- [x] AI-assistance artifact (`CLAUDE.md`).
- [x] Example outputs (`docs/examples/`) — four live-run reports covering
      strong growth, modest growth, a decline, and insufficient evidence.
- [x] Requirement-to-test traceability mapping
      (`docs/traceability-mapping.md`).
- [x] Test-results artifact (`docs/test-results.md`).
- [ ] Final repository review — pending.
- [ ] Submission-ready packaging — pending.
