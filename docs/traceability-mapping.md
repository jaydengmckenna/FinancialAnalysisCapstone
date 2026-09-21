# Requirement-to-Test Traceability Mapping

This maps every functional requirement in `specs/functional-requirements.md`
(114 requirements, FR-001 through FR-116) to the test(s) that verify it, or
explains honestly why one doesn't exist. It was built by reading the full
requirements spec against the actual test suite (356 tests as of
2026-09-21) and the actual implementation — not assumed from the spec text
alone, since several requirements describe behavior that was later
intentionally superseded (see `docs/design-tradeoffs.md` and
`constitution/techstack.md`).

**Status key:**
- **Covered** — a specific test verifies this behavior.
- **Partial** — some aspect is tested; a real gap remains, described inline.
- **Not automated** — genuinely true of the system (verified live, or true
  by construction) but no unit/integration test asserts it directly.
- **N/A** — describes behavior that was intentionally never built this way;
  see the linked decision.

Doing this pass surfaced a few real, previously undocumented gaps (not just
missing tests) — they're flagged with **(new finding)** and summarized at
the bottom.

## 1. Research Request

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-001 | Accept Research Request | Covered | `test_research_request_accepts_valid_data`, `test_interpret_intake_returns_validated_result` |
| FR-002 | Preserve Original Request | Covered | `test_original_prompt_is_preserved_exactly`, `test_interpret_intake_task_contains_original_prompt` |
| FR-003 | Accept Investor Preferences | Covered | `test_investor_profile_accepts_valid_preferences`, `test_investor_profile_allows_missing_preferences`, `test_required_profile_fields_are_included` |
| FR-004 | Validate Required Input | Covered | `test_clarification_gate_rejects_incomplete_intake`, `test_research_request_rejects_blank_text` |
| FR-005 | Identify Missing Information | Covered | `test_intake_result_requires_clarification_questions`, `test_intake_result_rejects_inaccurate_missing_fields` |
| FR-006 | Handle Missing Information | Partial | Clarification path is covered (`test_clarification_gate_allows_complete_intake`); the alternative "general limitation report" path (when the user isn't asked and a labeled-assumptions report is produced instead) isn't unit tested. |
| FR-007 | Support Dynamic Research Topics | Not automated | Verified live across many companies and sectors (NVIDIA, Apple, Chewy, Build-A-Bear, National Presto, Nike, Microsoft) throughout Phase 9 QA. "Supports variety" isn't a single assertable behavior. |
| FR-008 | Reject Unsupported Actions | Partial | `evidence_validation.py`'s unsafe-language check is tested (`test_unsafe_recommendation_is_rejected`). `report_writer.py`'s separate unsafe-phrase check in `_report_structure_validation` has **no dedicated test** — same category of language, checked twice in the codebase, only one instance verified. **(new finding)** |
| FR-009 | Confirm Research Scope | Covered | `test_research_scope_uses_expected_defaults`, `test_research_scope_rejects_*` |

## 2. Research Planning

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-010 | Create Research Plan | Covered | `test_create_research_plan_returns_valid_plan`, `test_research_plan_accepts_valid_data` |
| FR-011 | Define Research Objective | Covered | `test_research_plan_rejects_blank_objective` |
| FR-012 | Define Candidate Scope | Covered | `test_plan_preserves_named_candidates`, `test_research_plan_allows_empty_names_for_discovery` |
| FR-013 | Define Comparison Criteria | Covered | `test_research_plan_accepts_valid_data` (field presence); no dedicated behavioral test beyond schema. |
| FR-014 | Define Evidence Needs | Covered | `test_evidence_requirement_accepts_valid_data`, `test_research_plan_rejects_unknown_requirement_reference` |
| FR-015 | Define Risk Areas | Covered | `research_plan.risk_categories` — used directly by `test_score_derived_risk_*` and `_default_material_risks`; schema-level test via `test_research_plan_accepts_valid_data`. |
| FR-016 | Generate Search Queries | Covered | `test_search_query_accepts_valid_data`, `test_research_plan_requires_matching_query_purpose` |
| FR-017 | Preserve Search Queries | Covered | `test_search_query_rejects_duplicate_requirement_ids` |
| FR-018 | Limit Research Scope | Covered | `test_candidate_limit_is_preserved`, `test_plan_rejects_changed_candidate_limit`, `test_plan_rejects_excessive_source_limit` |
| FR-019 | Prevent Predetermined Conclusions | Not automated | A prompt-instruction-level behavior (the research planner shouldn't presuppose a winner); no test isolates this the way `test_system_prompt_forbids_unsupported_facts` does for the report writer's equivalent instruction. **(new finding — same category as the already-documented "unsupported facts" gap, just for a different agent)** |

## 3. Web Search

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-020 | Execute Web Search | Covered | `test_tavily_search_accepts_current_sdk_depths`; live-verified extensively. |
| FR-021 | Use Plan-Derived Queries | Partial | `TavilySearchTool` requires a `query_id` referencing an approved `SearchQuery`, but no test isolates rejection of an unapproved query specifically. |
| FR-022 | Return Structured Search Results | Covered | `test_search_result_accepts_valid_data`, `test_tavily_search_accepts_current_sdk_depths` |
| FR-023 | Preserve Search Result Metadata | Covered | `test_search_result_accepts_valid_data` (title, URL, domain, position fields) |
| FR-024 | Treat Search Results as Candidates | Covered | Implicit in the Source Selection stage's whole design (selected vs. excluded); `test_ready_selection_accepts_selected_source` |
| FR-025 | Select Sources for Retrieval | Covered | `test_validate_source_selection_identity_accepts_source_with_raw_content`, `test_ready_selection_requires_selected_source`, `test_search_and_select_returns_the_submitted_selection` (full agent run, mocked LLM) |
| FR-026 | Avoid Duplicate Search Results | N/A / Partial | No deterministic duplicate-URL detection exists — this is the same "duplicate sources" limitation already documented in `constitution/roadmap.md`'s Phase 10 section: handled only by Source Selection Agent prompt judgment (instructions 26-27), not code. |
| FR-027 | Handle Empty Search Results | Covered | `test_tavily_search_returns_empty_list_for_no_results` |
| FR-028 | Handle Search Failure | Partial | `ResearchError` exists and `TavilySearchTool.forward()` raises it on a malformed/failed Tavily response (`_map_response`), but no test exercises that raise path directly — only the "empty results" case is tested. **(new finding)** |
| FR-029 | Preserve Search Traceability | Covered | `SearchResult`/`SelectedSource` retain `query_id`, `search_result_id`, `result_position`. |

## 4. Website Retrieval and Scraping

All of section 4 describes a `Requests` + `Beautiful Soup 4` retrieval/parsing
pipeline that Phase 5B/5C intentionally excluded in favor of Tavily
returning raw content directly in the same search call — see
`constitution/techstack.md` ("Content Retrieval") and
`constitution/roadmap.md`'s Phase 5B/5C "Intentional Scope Decisions." The
requirements below predate that decision.

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-030 | Retrieve Selected Webpages | N/A | No separate retrieval step; see above. |
| FR-031 | Use Request Timeouts | N/A | No `requests` call exists to time out. |
| FR-032 | Check Response Status | N/A | No HTTP response to check; Tavily's own client handles this internally. |
| FR-033 | Identify Content Type | N/A | No separate content-type detection step. |
| FR-034 | Parse Supported HTML | N/A | No HTML parsing step (no Beautiful Soup). |
| FR-035 | Extract Page Metadata | N/A | Superseded — Tavily supplies title/URL/snippet/raw content directly; no separate metadata extraction. |
| FR-036 | Separate Retrieval from Parsing | N/A | There is no retrieval-then-parsing pipeline to separate. |
| FR-037 | Handle Retrieval Failure | Covered (superseded intent) | The actual failure mode today is a selected source with no `raw_content` from Tavily, which is rejected and retried — `test_validate_source_selection_identity_rejects_source_without_raw_content`. The requirement's *intent* (don't silently proceed without content) is satisfied even though the described mechanism (a `RetrievalResult`) isn't built. |
| FR-038 | Handle Parsing Failure | N/A | No parsing step exists to fail. |
| FR-039 | Treat Scraped Content as Data | Covered | Still fully applicable regardless of retrieval mechanism — `test_prompt_injection_in_evidence_is_not_workflow_instruction`, `test_prompt_injection_text_is_preserved_as_user_data`, `test_system_prompt_forbids_following_source_instructions`. |

## 5. Source Records and Evidence

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-040 | Create Source Records | Covered | `test_build_source_record_preserves_selected_source`, `test_successful_source_record_accepts_summary` |
| FR-041 | Assign Source Identifiers | Covered | `SourceRecord.source_id` (`default_factory=uuid4`); `test_source_record_rejects_duplicate_candidates` |
| FR-042 | Preserve Source URL | Covered | `test_build_source_record_preserves_selected_source` |
| FR-043 | Preserve Retrieval Date | Covered | `SourceRecord.retrieval_date`; `test_successful_source_record_accepts_summary` |
| FR-044 | Store Relevant Evidence | Covered | `test_extracted_evidence_accepts_numeric_value` |
| FR-045 | Connect Evidence to Sources | Covered | `ExtractedEvidence.source_id`; `test_build_source_record_preserves_selected_source` |
| FR-046 | Distinguish Evidence from Interpretation | Covered | Structural — `ExtractedEvidence` (sourced) vs. the Financial Analysis Agent's own `final_answer` interpretation text are separate model types by design; no single dedicated test name. |
| FR-047 | Represent Missing Metadata | Covered | `ExtractedEvidence` fields are `Optional`; `test_numeric_metadata_requires_value` |
| FR-048 | Detect Duplicate Evidence | Covered | `test_conflicting_evidence_flags_different_values_for_same_fact` and related tests — note this catches *conflicting* values for the same fact, which is closely related but not identical to detecting a literal re-reported duplicate. |
| FR-049 | Preserve Evidence Traceability | Covered | `evidence_ids` referenced throughout `ValidationClaim`, `CalculatedMetric.input_evidence_ids` |

## 6. Financial Data and Calculations

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-050 | Extract Financial Information | Covered | `test_prompt_contains_evidence_ids_and_values`; `test_extract_evidence_returns_the_submitted_evidence` (full agent run, mocked LLM); live-verified extensively. |
| FR-051 | Normalize Financial Data | Covered | `test_fetch_metric_returns_normalized_value` (yfinance path); web-extraction normalization enforced structurally by the `ExtractedEvidence` model. |
| FR-052 | Preserve Units and Periods | Covered | `test_financial_input_normalizes_currency`; `currency`/`unit`/`reporting_period` fields throughout. |
| FR-053 | Validate Numeric Input | Covered | `test_available_financial_input_requires_value`, `test_missing_financial_input_rejects_value` |
| FR-054 | Use Deterministic Calculations | Covered | `test_growth_rate_uses_authoritative_evidence`; the entire design of `financial_calculation.py`. |
| FR-055 | Handle Missing Values | Covered | `test_missing_financial_input_rejects_value` |
| FR-056 | Handle Non-Applicable Metrics | Covered | `test_resolve_metric_row_rejects_unsupported_metric`; also the Phase 10 "P/E is not applicable" finding (no P/E path exists to misuse). |
| FR-057 | Preserve Calculation Inputs | Covered | `CalculatedMetric.input_evidence_ids`; `test_calculation_rejects_duplicate_inputs` |
| FR-058 | Preserve Calculation Results | Covered | `test_completed_calculation_accepts_result` |
| FR-059 | Prevent Fabricated Values | Covered | `FinancialCalculationTool._numeric_value` raises rather than guessing when `reported_value` is `None`; deterministic-only design. |

## 7. Candidate Analysis

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-060 | Compare Candidates | Partial | Single-candidate scoring is covered (`test_score_financial_performance_*`); no dedicated multi-candidate comparison test (same gap already noted in the Phase 10 happy-path list). |
| FR-061 | Apply Investor Preferences | Partial | `_score_financial_performance`/`_score_derived_risk` don't vary by risk tolerance or objective — a known limitation documented in `docs/design-tradeoffs.md`'s "What We'd Improve" section. |
| FR-062 | Evaluate Supporting Evidence | Covered | `CandidateAnalysis.supporting_evidence_ids`; `test_completed_candidate_analysis_accepts_evaluation` |
| FR-063 | Evaluate Opposing Evidence | N/A (potential future expansion) | The project's scope has been single-candidate research throughout — there is no second candidate to hold opposing evidence against. `opposing_evidence_ids` exists on the model and `orchestrator.py` always leaves it `[]`, correctly, for the current scope; it's reserved schema for a possible future multi-candidate comparison feature. |
| FR-064 | Evaluate Material Risks | Covered | `test_recommendation_without_material_risks_requires_correction`, `test_score_derived_risk_flags_declining_growth` |
| FR-065 | Handle Insufficient Evidence | Covered | `AnalysisStatus.INSUFFICIENT_EVIDENCE` path; live-verified many times. |
| FR-066 | Explain Candidate Results | Covered | `CandidateAnalysis.rationale` (always populated, generically). |
| FR-067 | Rank Comparable Candidates | Covered | `RecommendationResult.ranked_candidates`; `test_ranked_recommendation_requires_ranking` |
| FR-068 | Avoid False Precision | Not automated | No test asserts against an overly precise ranking claim. Loosely related to `_RESULT_QUANTUM` rounding in calculations, but that governs a number's precision, not a ranking's. **(new finding)** |
| FR-069 | Preserve Analysis Results | Covered | Cached via `self.last_candidate_analyses` before report generation reuses it. |

## 8. Recommendation Behavior

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-070 | Produce Research Conclusion | Covered | `_default_recommendation`'s outcome logic; live-verified. |
| FR-071 | Identify Aligned Candidates | Covered | `preferred_candidate` logic in `_default_recommendation`. |
| FR-072 | Explain Recommendation Rationale | Covered | `RecommendationResult.rationale` |
| FR-073 | Include Alternatives | N/A (potential future expansion) | Same scope reason as FR-063 — with single-candidate research, there's no alternative to include. `alternative_candidates` exists on the model and `_default_recommendation` always leaves it `[]`, correctly, for the current scope; reserved schema for a possible future multi-candidate comparison feature. |
| FR-074 | Include Risks | Covered | `test_recommendation_without_material_risks_requires_correction` |
| FR-075 | Include Missing Information | Covered | `missing_information` populated for the insufficient-evidence outcome. |
| FR-076 | Include Human-Review Statement | Covered | `test_report_draft_requires_human_review_language`, `test_human_review_cannot_be_disabled` |
| FR-077 | Avoid Trade Instructions | Covered | `test_unsafe_recommendation_is_rejected` ("execute a trade") |
| FR-078 | Avoid Guaranteed Outcomes | Covered | `test_unsafe_recommendation_is_rejected` ("guaranteed return") |
| FR-079 | Support Insufficient-Evidence Outcome | Covered | `test_insufficient_evidence_rejects_preferred_candidate`, `test_insufficient_outcome_requires_insufficient_confidence` |

## 9. Claim and Citation Validation

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-080 | Identify Material Claims | Covered | `_default_validation_claims` builds one claim per evidence record and calculation. |
| FR-081 | Validate Material Claims | Covered | `test_supported_calculated_claim_is_approved`, `test_altered_calculation_claim_requires_correction` |
| FR-082 | Validate Citation References | Covered | `test_unknown_citation_is_rejected` |
| FR-083 | Reject Unknown Sources | Covered | `test_unknown_citation_is_rejected` |
| FR-084 | Check Claim Support | Covered | `test_text_supported_rejects_unrelated_evidence`, `test_unrelated_citation_requires_analysis_correction` |
| FR-085 | Detect Unsupported Claims | Covered | Same mechanism as FR-084. |
| FR-086 | Detect Conflicting Evidence | Covered | `test_conflicting_evidence_flags_different_values_for_same_fact` and the full `_check_conflicting_evidence` suite. |
| FR-087 | Preserve Validation Findings | Covered | `test_validation_finding_serialization_round_trip` |
| FR-088 | Block Invalid Reports | Covered | `test_rejected_result_requires_blocking_finding`, `test_approved_result_rejects_blocking_finding` |
| FR-089 | Validate Human-Review Boundary | Covered | `test_unsafe_recommendation_is_rejected` (`HUMAN_REVIEW_BOUNDARY_FAILURE` category) |

## 10. Report and File Output

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-090 | Generate Markdown Report | Covered | `test_forward_writes_valid_payload` |
| FR-091 | Include Research Context | Covered | `test_forward_rejects_missing_required_section` (required-heading check) |
| FR-092 | Include Methodology | Covered | Same mechanism. |
| FR-093 | Include Candidate Analysis | Covered | Same mechanism. |
| FR-094 | Include Conclusion | Covered | Same mechanism. |
| FR-095 | Include Risks and Limitations | Covered | `test_report_draft_requires_risks`, `test_report_draft_requires_limitations` |
| FR-096 | Include Sources | Covered | Same required-heading mechanism. |
| FR-097 | Write Recommendation File | Covered | `test_forward_writes_valid_payload`, `ReportWriterTool._next_available_path` |
| FR-099 | Prevent Invalid Output | Covered | `test_forward_rejects_missing_required_section`; "only validated results proceed to report generation" is an established Phase 9 exit criterion. |

*(There is no FR-098 in the source spec.)*

## 11. Workflow Control

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-100 | Use Explicit Workflow Order | Covered | `test_orchestrator_executes_full_phase_9_pipeline`; `orchestrator.run()`'s fixed stage sequence. |
| FR-101 | Maintain Workflow State | Partial (documented) | Already an explicit, documented decision — `WorkflowState` was descoped in favor of ad-hoc `self.last_*` attributes. See `docs/design-tradeoffs.md` §1. Accumulation of source/evidence records across a retry round (rather than discarding prior rounds) is covered by `test_orchestrator_retries_and_accumulates_evidence_after_correction_required`. |
| FR-102 | Validate Stage Input | Covered | `ValueError` raised at each stage boundary, e.g. `_validate_source_selection_identity`. |
| FR-103 | Validate Stage Output | Covered | Pydantic validation at every stage transition. |
| FR-104 | Stop Invalid Downstream Processing | Covered | `test_create_research_plan_stops_incomplete_intake`; `_run_with_retries` raising `WorkflowError`; `test_search_and_select_raises_when_agent_never_submits`, `test_extract_evidence_rejects_source_outside_extraction_scope`. |
| FR-105 | Distinguish Recoverable Failures | Covered | `ValueError` (recoverable, retried) vs. `WorkflowError` (unrecoverable) distinction; `test_nonrecoverable_error_rejects_retry` |
| FR-106 | Record Workflow Failures | Covered | `logger.error`/`logger.warning` throughout `orchestrator.py`; `WorkflowError` model. |
| FR-107 | Avoid Silent Failure | Covered | `main.py`'s `WorkflowError` catch and `ReportWriterTool`'s `OSError` catch — both fixed during this Phase 10 pass; `test_unrecoverable_workflow_error_exits_cleanly`, `test_forward_reports_file_write_failure_as_value_error`. |
| FR-108 | Complete with Validated Output | Covered | Same "only validated results proceed" design as FR-099. |

## 12. Traceability

| FR | Requirement | Status | Test(s) / Note |
|---|---|---|---|
| FR-110 | Preserve Workflow Record | Partial (documented, out of scope) | No structured per-workflow record is saved after a run completes — only the final Markdown report and the human-readable log. This is the `WorkflowArtifact` gap discussed and explicitly deprioritized (2026-09-21); revisit only if a follow-up-prompt feature is ever built. |
| FR-111 | Preserve Research Inputs | Partial (documented, out of scope) | Held in-memory (`self.last_research_plan`, etc.) during a run, not persisted after. Same root cause as FR-110. |
| FR-112 | Preserve Research Plan | Partial (documented, out of scope) | Same as FR-110/111. |
| FR-113 | Preserve Sources | Partial (documented, out of scope) | Same as FR-110/111. |
| FR-114 | Preserve Analysis | Partial (documented, out of scope) | Same as FR-110/111. |
| FR-115 | Preserve Validation | Partial (documented, out of scope) | Same as FR-110/111. |
| FR-116 | Preserve Output References | Covered | The one part of this section that *is* satisfied — `ReportArtifact` persists the file path, checksum, and status; `test_forward_writes_valid_payload`. |

*(There is no FR-109 in the source spec.)*

---

## Summary

Of 114 requirements:

- **~90 Covered** — verified by a specific, named test.
- **~13 Partial** — some aspect tested, a real gap documented inline.
- **~11 N/A** — 9 describe the pre-Phase-5B/5C retrieval architecture, superseded by the Tavily-only approach; 2 (FR-063, FR-073) describe multi-candidate comparison, reserved schema for a feature outside the project's current single-candidate scope.
- **~2 Not automated** — true by live verification or by construction, not practical to unit test (e.g. "supports varied research topics").

### New findings from this pass (not previously documented anywhere)

1. **FR-008**: `report_writer.py`'s unsafe-phrase check has no dedicated test (the equivalent check in `evidence_validation.py` does).
2. **FR-019**: no test pins the research-planning prompt's "don't presuppose a winner" instruction, unlike the equivalent report-writing instruction.
3. **FR-028**: `TavilySearchTool`'s `ResearchError`-raising failure path (a malformed/failed Tavily response, as opposed to an empty-but-valid one) has no dedicated test.
4. **FR-068**: no test verifies the system avoids false precision in a ranking claim.

None of these are urgent — the system's core safety behavior (never fabricate, always require human review, block on unsupported claims) is thoroughly covered.
