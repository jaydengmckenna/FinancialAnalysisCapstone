# AI-Assistance Documentation

This file satisfies `specs/acceptance-criteria.md` AC-125 (selected prompt
examples and decision rationale) and the AI-assistance documentation
called for in `constitution/roadmap.md`'s Phase 11 section. It was
originally scoped as `COPILOT.md` by the capstone template; renamed to
`CLAUDE.md` because the AI assistance actually used throughout this
project was Claude Code (Anthropic), not GitHub Copilot.

**Scope note:** this file was written during Phase 11 and documents the
AI-assisted work in the most direct detail for Phases 9 through 11, where
full session context was available to draw from. Constitution and
specification work in Phases 1–3 was also done with AI assistance under
the same specification-driven methodology (`constitution/mission.md`,
`constitution/roadmap.md`), but this document doesn't reconstruct specific
prompts from those earlier sessions that predate it.

## How Agent Boundaries Were Selected

The governing rule, applied consistently across every stage: agents are
used for tasks requiring interpretation, judgment, comparison, or written
synthesis; deterministic Python is used for tasks with defined inputs,
rules, and outputs. See `docs/architecture.md` for the full breakdown.

This produced six named workflow stages, five of them genuinely
agent-driven (each with its own scope and, for three of them, its own
tool the model calls directly) and one — Evidence Validation — that kept
the "agent" name for interface consistency with the orchestrator but is
100% deterministic Python by design, since deciding whether a claim is
supported by cited evidence, whether a calculation used compatible units
and periods, or whether language crosses a safety boundary are rule-based
determinations, not judgment calls.

## Why Deterministic Tools Were Separated From Agents

Three examples that shaped this boundary directly:

- **Financial calculation.** Arithmetic (growth rate, margin, ratio,
  difference) has exactly one correct answer given its inputs. Letting a
  model compute it directly would introduce a failure mode analysis-report
  generation doesn't need: arithmetic mistakes indistinguishable from
  genuine judgment calls. The Financial Analysis Agent interprets *which*
  calculation to run and *what it means*; the calculation tool computes
  it.
- **The yfinance fallback (`FinancialDataTool`).** When web search
  evidence didn't reliably surface exact numeric figures during Phase 9
  development, the fix was a second deterministic data source the
  Financial Analysis Agent calls itself in plain Python — not offered to
  the model as a callable tool, since looking up a named metric for a
  known ticker and fiscal year involves no judgment to make. See
  `docs/design-tradeoffs.md` §4.
- **Evidence Validation.** Kept fully deterministic rather than converted
  to a model call, specifically so the project's central safety claim —
  no unsupported or unsafe recommendation can be approved — rests on rules
  that always run the same way for the same input, not a judgment call
  that could vary between runs. The orchestrator's retry/termination logic
  depends on this: it enforces a bounded retry and refuses to generate a
  report at all when validation never approves, and that guarantee is
  only as strong as validation itself being deterministic.

## Suggestions Accepted

- **5% materiality threshold for conflicting evidence** (Phase 10). An
  early version of the conflict-detection check flagged values that
  differed by ordinary rounding noise (e.g. $245B vs. $245.122B) as a
  genuine conflict. Caught during review; a materiality threshold was
  added so only disagreements large enough to matter are disclosed.
- **Reusing `FinancialDataTool.resolve_metric_row` for conflict grouping**
  instead of raw string matching on `evidence_type`, after an exact-string
  match missed a real live conflict caused by label variance ("Fiscal
  Year Revenue Data" vs. "Fiscal Year Revenue").
- **Catching `OSError` in `ReportWriterTool.forward()`** — a real gap
  found while scoping Phase 10's "file writing fails" adversarial
  scenario; a disk-level failure would have propagated as an unhandled
  exception instead of the same bounded-retry handling every other
  failure in that tool gets.
- **Verifying tests are genuine regression guards, not just passing
  assertions**, by temporarily reintroducing the bug a new test claims to
  catch, confirming the test fails, then reverting — used for both
  orchestrator end-to-end tests added in Phase 10.

## Suggestions Challenged or Rejected

- **Formal `WorkflowState`/`StageResult`/`ValidationCorrectionRouter`
  wiring** (Phase 9 review). These contracts already existed
  (Phase 4), but wiring them up meant restructuring the orchestrator's
  control flow this late in the project. Rejected in favor of the
  simpler ad-hoc-attribute approach already in place, after confirming
  it's conservative rather than unsafe. See `docs/design-tradeoffs.md`
  §1.
- **The full seven-category weighted scoring methodology**
  (`specs/recommendation-methodology.md` §6–8). Reduced to a single
  `financial_performance` score derived from growth rate, rather than
  building evidence-gathering and scoring for six additional categories
  the system has no other capability to support. See
  `docs/design-tradeoffs.md` §2.
- **A same-candidate period guard on the `difference` calculation
  operation.** A real, understood gap (documented in
  `docs/design-tradeoffs.md` §3) that was deliberately left unfixed in
  favor of documenting it for the mandatory human reviewer instead of
  adding another code-level guard.
- **Whether the retry-exhausted-without-approval path even needed its own
  test.** I originally proposed it as a gap; direct pushback ("why do I
  need to do this if the orchestrator doesn't let there proceed with no
  data? ... it only retries on a fail right?") led to clarifying the
  actual distinction being tested (discarding good partial evidence
  across a retry vs. the already-handled "no data at all" case) before
  the test was written.
- **Wording changes to the architecture documentation that would have
  obscured which components are deterministic Python rather than model
  calls.** Declined, on the basis that the deterministic/agentic
  boundary is required content under this project's own acceptance
  criteria (AC-125) and is what the safety guarantees (bounded retries,
  no report without approval) actually rest on — see the note at the end
  of this file.

## Selected Prompt Examples

> "why do i need to do this if the orchestrator doesnt let there proceed
> with no data? it seems like intrinsically i account for that. if the
> iniital try works why would i need to 'keep' data on the second retry?
> it only retries on a fail right?"

Led to a clarifying exchange distinguishing "no data survives to
validation" (already handled) from "good partial evidence gets silently
discarded across a retry, producing an unnecessarily worse outcome"
(the actual bug the new test guards against) before any test was written.

> "yeah lets not special case anything. basically your saying that for
> rejected we need to add a test where rejected gives no report is all
> your saying right?"

Confirmed the scope of a proposed new end-to-end test down to exactly one
assertion, after a prior exchange about whether a retry-exhausted
workflow should still produce a flagged report (rejected — see the
`REJECTED` outcome discussion in `docs/architecture.md`'s retry section).

> "well wouldnt it be better for it to generate the report with the flag
> that needs human review or is this something entirely different?"

A genuine design question, answered by distinguishing `REJECTED` (unsafe
content — no report should exist at all) from the three recoverable
outcomes (where a flagged report might be defensible) — then deciding not
to special-case any of them, keeping the existing conservative behavior.

> "going forward dont do any commits or adds to the git i will do that
> manually."

A standing instruction adopted immediately and without exception from
that point forward.

## How Generated Code Was Reviewed and Tested

Phase 10 ran as an explicit per-item decision process: each checklist
item (happy-path scenario, adversarial scenario, deliverable) was
presented individually, with a test/skip/implement decision made before
moving to the next one, rather than a single large batch of AI-authored
changes landing at once. Every change was validated by running the full
suite (`python -m pytest -q`) before being considered done, and the two
end-to-end regression tests added in Phase 10 were specifically verified
by temporarily reintroducing the bug they claim to catch and confirming
the test fails before reverting — see `constitution/roadmap.md`'s Phase
10 section and `tests/workflow/test_orchestrator.py`.

## How the Human Developer Retained Final Authority

- **A standing autonomy rule**, set after an earlier session where a
  large batch of unreviewed changes landed at once: single-system fixes
  proceed directly; anything touching multiple systems pauses for a
  check-in between each one, rather than cascading through a whole fix
  before reporting back.
- **All git commits and staging are done manually** — Claude Code makes
  and leaves working-tree edits; it does not run `git add` or
  `git commit`.
- **Phase 10 decisions were made item-by-item**, not delegated as a
  batch — including explicit scoping questions (e.g. what an
  "insufficient-evidence report" should actually demonstrate, resolved by
  a direct multiple-choice question before any report was generated).
- **The final acceptance review was sequenced deliberately last**, after
  every other Phase 10 deliverable was settled, at the developer's
  explicit direction.

