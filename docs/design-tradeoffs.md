# Design Trade-offs and Scope Decisions

This document records the deliberate engineering decisions made while
finishing Phase 9, including what was intentionally left out, what was
built in a reduced form instead of the originally specified version,
and what a future iteration would improve. Its purpose is to make the
reasoning behind these decisions explicit and reviewable, the same way
a research paper's "Limitations and Future Work" section separates
conscious scope decisions from unfinished work.

## 1. Analysis-Correction Routing (`WorkflowState`, `StageResult`, `ValidationCorrectionRouter`) — Descoped

**What exists but isn't wired up:** Phase 4 defined full `WorkflowState`
and `StageResult` Pydantic contracts (`src/fin_automation/models/workflow.py`)
meant to be the single, structured record of a workflow run — current
stage, per-stage status and timestamps, retry counts, and every
downstream record ID. Phase 7 built `ValidationCorrectionRouter`
(`src/fin_automation/tools/evidence_validation.py`), a deterministic
utility that groups validation findings by which component
(`CorrectionTarget`: source_selection, financial_calculation,
financial_analysis, report_writing, etc.) is actually at fault.

**What the orchestrator does instead:** it tracks progress through a
handful of ad-hoc instance attributes (`self.last_source_records`,
`self.last_evidence_records`, `self.last_recommendation`, and so on)
rather than building a `WorkflowState` object. `ValidationCorrectionRouter`
is never imported or called — a validation outcome of
`analysis_correction_required` is treated identically to an outright
rejection: the workflow stops. The one exception is a single, blanket
retry of the research-gathering stage when additional research
requests exist, which is not the same as routing a correction to the
*specific* stage a finding named.

**Why we chose not to build it:** wiring this up properly means
restructuring the orchestrator's control flow — real per-`CorrectionTarget`
dispatch logic, since re-running "just the calculation" and re-running
"just the report writer" are different code paths, not a single
generic retry. That is a nontrivial rework, not a small patch. Multiple
live runs during Phase 9 QA (2026-09-17) confirmed the current
behavior is *conservative, not unsafe*: the system never produces an
invalid report from an unrecoverable failure — it either recovers via
the one bounded research retry it already has, or safely stops with an
`insufficient_evidence` result or a raised `WorkflowError` (now caught
cleanly in `main.py` — see the exit-criteria note in `roadmap.md`).
Given the project is heading into Phase 10 and 11, the cost of the
restructuring didn't justify the benefit right now.

**What it would have bought us:** some recoverable failures that
currently stop the whole workflow (a bad calculation input, a
report-writing formatting slip) could instead retry only the at-fault
stage, producing a real recommendation in cases that currently end in
`insufficient_evidence`.

**Status:** descoped for this capstone version.

## 2. Candidate Scoring — Reduced from the Full Weighted Methodology

**What the spec envisions** (`specs/recommendation-methodology.md`,
sections 6–8): seven weighted categories — Financial Growth (20%),
Profitability (15%), Balance-Sheet Strength (15%), Valuation (15%),
Competitive Position (15%), Risk Profile (10%), and Investor-Profile
Alignment (10%) — each independently scored 0–100 with its own
evidence, reasoning, and confidence, combined into one weighted score
by a deterministic Python function.

**What's actually implemented:** the system only ever produces one
category, `financial_performance`, derived from a single growth,
margin, ratio, or difference calculation. The other six categories
were never built — there is no evidence-gathering or scoring path for
profitability ratios, balance-sheet metrics, valuation multiples, or
competitive-position comparisons today.

**The gap found during QA (2026-09-17):** before this fix, the single
`financial_performance` score was a hardcoded constant
(`Decimal("75")`) regardless of the calculated result. Every generated
report — whether it showed +126% growth or a -40% decline — displayed
the identical "moderate confidence, score 75." This was confirmed by
inspecting every report generated up to that point; the score never
varied once.

**Decision:** rather than build the full seven-category weighted
framework (which requires adding financial-analysis capability the
system doesn't have at all today), we implemented a smaller,
single-score version: `ResearchOrchestrator._score_financial_performance`
derives the score from the candidate's own calculated growth-rate
percentage, mapped through project-defined bands (≥50% → 95, ≥15% →
80, ≥0% → 60, ≥-15% → 35, below that → 15; no growth-rate calculation
available → 50, neutral). This is a deliberate simplification of the
spec's methodology — it fixes the part of the gap that mattered most
(a score that reflects what was actually found, so two reports are not
interchangeable) without the cost of the full framework. It is
explicitly labeled in code as project-defined bands, not a universal
financial rule, consistent with the spec's own framing of its weights.

**What we'd improve with more time:** incorporate investor-profile
alignment directly into the curve — a high-risk-tolerance, growth-
objective investor's score should reward an exceptionally large
positive return more steeply than a linear band does (an accelerating
bonus for outsized growth, not a flat step), and a low-risk-tolerance
investor's score should be penalized more for the same decline than a
high-risk one. Longer-term, the remaining six categories from the
spec's methodology would give a genuinely weighted, multi-factor score
instead of one category standing in for the whole recommendation.

**Status:** implemented in reduced form; see
`ResearchOrchestrator._score_financial_performance` in
`src/fin_automation/workflow/orchestrator.py`.

## 3. The `difference`-Operation Same-Period Gap — Accepted, Mitigated via Documentation

**What happened:** a live QA run against Microsoft produced a
confidently-presented `qualified_recommendation` that was actually
wrong. The evidence-extraction agent mislabeled a real FY2025 revenue
figure as `"FY2024"` — the same label already used by a genuine FY2024
figure. The financial analysis agent first tried a `growth_rate`
calculation, which the deterministic calculator correctly rejected
("Growth rate requires two different reporting periods"). Rather than
treating that as a real gap, the model switched to the `difference`
operation, which has no equivalent guard, computed a meaningless
$36.7 billion delta between two different fiscal years' figures both
labeled the same period, and the report presented that as answering
the original "FY2023 to FY2024 growth" question. Evidence validation
approved it with zero findings.

**Why the existing guard doesn't cover this:** `difference` is
deliberately exempt from period-matching in
`FinancialCalculationTool._validate_compatibility`, because it is also
legitimately used to compare two *different* candidates at the *same*
period (e.g., "Company A vs. Company B revenue, both FY2024" — same
period is correct there). The gap is specifically a same-candidate
`difference` calculation, which the existing exemption didn't
distinguish from the legitimate cross-candidate case.

**Decision:** the fix itself is well-understood and small — extend the
same-period rejection to also apply to `difference` when both inputs
share a candidate, leaving the cross-candidate case untouched. We
chose not to make this change. Every report already requires mandatory
human review before use, so the chosen mitigation was to arm that
reviewer with what to check instead of adding another validation
layer: `README.md`'s "Example Prompt and Interpreting a Report"
section now explicitly tells a reader to check which periods a
calculation actually compared, and to treat a `difference` result for
a single candidate with extra scrutiny if both periods look the same.

**Status:** accepted as a known limitation; human review is the
documented safety net, not a code-level guard.

## 4. yfinance as a Deterministic Fallback

Live web search alone was not reliably producing exact numeric
financial figures during Phase 9 development — some runs found no
usable source, others found figures buried in large filings that
extraction couldn't reliably pull out. `FinancialAnalysisAgent` was
given a second, deterministic data source (`FinancialDataTool`,
yfinance-backed) that fills a specific numeric gap — revenue, net
income, or gross profit for a named ticker and fiscal year — only when
web search evidence is missing or unusable for that requirement. This
is plain Python, not an agentic tool call, since looking up a named
metric involves no judgment. See `constitution/techstack.md` for the
full rationale, including the ticker-resolution and fiscal-year-search
design decisions. This entry exists here mainly to tie it into the
same "what we decided and why" narrative as the rest of this document.

## 5. Single-Candidate Research Scope — Multi-Candidate Fields Reserved for Future Expansion

**The decision:** the project's research scope has been single-candidate
throughout — evaluating one company against the investor's profile,
not ranking several candidates against each other. This was a
deliberate choice to avoid introducing a second, largely untested
surface (candidate-vs-candidate comparison logic, and the additional
failure modes and tests that would come with it) this late in the
project.

**What this means for the schema:** `CandidateAnalysis.opposing_evidence_ids`
and `RecommendationResult.alternative_candidates` both exist as real
fields — `opposing_evidence_ids` for evidence that weakens a candidate
relative to others being compared, `alternative_candidates` for
candidates considered but not preferred. Both are always left as `[]`
by `orchestrator.py` today. That's correct behavior for the current
scope, not a bug: with one candidate evaluated per request, there is
no "other candidate" for either field to hold anything about.

**Status:** the fields are left in place, unused, rather than removed
from the schema — the same low-risk precedent as `WorkflowState` and
`RetrievalResult` elsewhere in this document. If multi-candidate
comparison is ever built, the schema to receive it already exists;
nothing has to be added retroactively.

## 6. What We'd Improve With More Time

- Real per-stage correction routing via `WorkflowState` and
  `ValidationCorrectionRouter` (see §1), instead of a single blanket
  research retry.
- Investor-profile-aware, accelerating scoring curves, and the
  remaining scoring categories from the recommendation methodology
  (see §2).
- A same-candidate period guard on the `difference` operation (see
  §3) — small, understood, and still open if a future pass wants to
  close it rather than rely on human review alone.
- Evidence-validation checks that cross-reference a claimed reporting
  period against its cited source's own stated period (e.g., a source
  titled "2025 Annual Report" backing an evidence record labeled
  "FY2024") — this would have caught the Microsoft mislabeling at the
  extraction stage, before either the calculator guard or human review
  needed to matter.
- Multi-candidate comparison (see §5) — populating `opposing_evidence_ids`
  and `alternative_candidates` with real content once there's more
  than one candidate to compare against.
- Phase 10's structured adversarial test suite, which will formalize
  much of what today's live QA passes found by hand.
