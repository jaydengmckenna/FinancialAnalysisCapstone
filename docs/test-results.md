# Test Results

A saved, point-in-time record of a full test suite run, per Phase 10's
"test-results artifact" deliverable (`constitution/roadmap.md`).

## Run details

- **Date:** 2026-09-21 (regenerated — added an end-to-end orchestrator
  test covering retry/accumulation across a correction-required round)
- **Base commit:** `5fa79fc` (plus uncommitted changes to
  `tests/workflow/test_orchestrator.py` at run time — this reflects
  the actual working tree the suite was run against, not a claim that
  a specific commit alone produces this result).
- **Python:** 3.12.3
- **Command:** `python -m pytest -v`
- **External dependencies:** none required. OpenAI, Tavily, and
  yfinance are all mocked throughout the suite — this result is
  reproducible without any API credentials or network access.

## Result

```
356 passed in 2.54s
```

0 failed, 0 errors, 0 skipped.

## Coverage by file

| Test file | Tests |
|---|---:|
| `tests/test_models/test_financial.py` | 47 |
| `tests/test_models/test_workflow.py` | 29 |
| `tests/test_models/test_validation.py` | 26 |
| `tests/agents/test_research_planner.py` | 26 |
| `tests/test_models/test_intake.py` | 25 |
| `tests/test_models/test_reports.py` | 23 |
| `tests/prompts/test_intake_prompts.py` | 22 |
| `tests/test_models/test_sources.py` | 21 |
| `tests/tools/test_evidence_validation.py` | 18 |
| `tests/test_models/test_research.py` | 17 |
| `tests/workflow/test_orchestrator.py` | 14 |
| `tests/tools/test_financial_data.py` | 11 |
| `tests/prompts/test_research_planning.py` | 11 |
| `tests/agents/test_research_planner_planning.py` | 11 |
| `tests/agents/test_financial_analysis.py` | 11 |
| `tests/test_logging_config.py` | 9 |
| `tests/tools/test_report_writer.py` | 7 |
| `tests/tools/test_financial_calculation.py` | 5 |
| `tests/test_config.py` | 4 |
| `tests/agents/test_source_selection.py` | 4 |
| `tests/agents/test_evidence_extraction.py` | 4 |
| `tests/test_exceptions.py` | 3 |
| `tests/tools/test_tavily_search.py` | 2 |
| `tests/prompts/test_report_prompts.py` | 2 |
| `tests/prompts/test_evidence_extraction_prompt.py` | 2 |
| `tests/tools/test_evidence_submission.py` | 1 |
| `tests/test_main.py` | 1 |
| **Total** | **356** |

## Reproducing this result

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e . --no-deps
.venv/bin/pytest -v
```

The `pip install -e .` step is required — `fin_automation` is a
`src/`-layout package, and `requirements.txt` alone does not make it
importable. This was a real gap found during Phase 11 (`pyproject.toml`
was empty): verified by testing `requirements.txt`-only installation in
a genuinely clean virtual environment, which failed with 28 collection
errors before `pyproject.toml` was given real packaging metadata.

No `.env` file or live credentials are required to run the suite —
only to run `main.py`/`run_smoke_test.py` against real services.

## Relationship to other project artifacts

- `docs/traceability-mapping.md` maps each of the 114 functional
  requirements to the specific test(s) counted here.
- `constitution/roadmap.md`'s Phase 10 section tracks which
  categories of behavior (happy-path, adversarial, end-to-end) this
  suite covers and which remain partial or not applicable.
- This file should be regenerated (same command, new date) if the
  suite's count changes materially before Phase 10 is marked complete.
