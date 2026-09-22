# Data Contracts

## Purpose

This document defines the structured data exchanged between the agents,
tools, services, and orchestrator in Agentic Financial Analysis Automation.

These contracts will be implemented as Pydantic models.

The contracts define:

- Required and optional fields.
- Field types.
- Allowed status values.
- Validation rules.
- Producing components.
- Consuming components.
- Relationships between records.

The contracts describe data structure and validation. They do not define
agent prompts, financial formulas, or workflow implementation.

## General Contract Rules

All structured workflow records shall follow these rules:

1. Every workflow record shall belong to one `workflow_id`.
2. Major records shall have unique identifiers.
3. Timestamps shall use timezone-aware ISO 8601 values.
4. Missing information shall not be represented as zero or empty text.
5. Unavailable and non-applicable values shall remain distinct.
6. Source-derived facts shall preserve evidence references.
7. Material calculations shall preserve their inputs and evidence
   references.
8. Agent outputs shall be validated before entering a dependent stage.
9. Unknown fields should be rejected unless a contract explicitly permits
   them.
10. Enumerated statuses shall use the values defined in this specification.

## Common Types

The implementation should use the following Python-compatible types:

- Identifiers: `UUID`
- Timestamps: timezone-aware `datetime`
- Dates: `date`
- URLs: `HttpUrl`
- Decimal financial values: `Decimal`
- Percentages and scores: `Decimal`
- Lists: `list[...]`
- Optional values: `... | None`
- Enumerated values: `StrEnum` or string-based `Enum`

Financial values should use `Decimal` rather than binary floating-point
types when arithmetic precision matters.

---

# 1. Enumerations

## RiskTolerance

Allowed values:

- `low`
- `moderate`
- `high`

## InvestmentObjective

Allowed values:

- `growth`
- `income`
- `capital_preservation`
- `balanced`
- `unspecified`

## TimeHorizon

Allowed values:

- `short_term`
- `medium_term`
- `long_term`
- `unspecified`

## RequestType

Allowed values:

- `candidate_discovery`
- `candidate_comparison`
- `single_candidate_analysis`

## AssetType

Initial allowed values:

- `public_stock`
- `adr`

Additional asset types require an intentional specification change.

## SourceCategory

Allowed values:

- `primary`
- `secondary`
- `discovery`
- `unsupported`

## SearchPurpose

Allowed values:

- `candidate_discovery`
- `financial_growth`
- `profitability`
- `balance_sheet`
- `valuation`
- `competitive_position`
- `risk_research`
- `source_corroboration`

## SourceSelectionStatus

Allowed values:

- `ready_for_retrieval`
- `additional_search_required`
- `insufficient_candidate_sources`

## RetrievalStatus

Allowed values:

- `success`
- `failed`
- `unsupported_content`
- `blocked`
- `timed_out`

## ParsingStatus

Allowed values:

- `success`
- `partial`
- `failed`
- `not_attempted`

## DataAvailabilityStatus

Allowed values:

- `available`
- `missing`
- `unavailable`
- `invalid`
- `insufficient`
- `not_applicable`

## CalculationType

Initial allowed values:

- `revenue_growth`
- `net_profit_margin`
- `operating_profit_margin`
- `debt_to_equity`
- `price_to_earnings`
- `weighted_score`

## CalculationStatus

Allowed values:

- `completed`
- `missing_input`
- `invalid_input`
- `not_applicable`
- `failed`

## AnalysisStatus

Allowed values:

- `completed`
- `partial`
- `insufficient_evidence`
- `not_comparable`
- `failed`

## RecommendationOutcome

Allowed values:

- `ranked_recommendation`
- `qualified_recommendation`
- `research_shortlist`
- `no_aligned_candidate`
- `insufficient_evidence`

## ConfidenceLevel

Allowed values:

- `high`
- `moderate`
- `low`
- `insufficient`

A confidence value describes evidence strength. It does not predict
investment performance.

## ValidationOutcome

Allowed values:

- `approved`
- `analysis_correction_required`
- `additional_research_required`
- `insufficient_evidence`
- `rejected`

## ValidationSeverity

Allowed values:

- `information`
- `warning`
- `error`
- `blocking`

## ValidationCategory

Initial allowed values:

- `unsupported_claim`
- `invalid_citation`
- `irrelevant_citation`
- `missing_evidence`
- `calculation_input_problem`
- `incompatible_comparison`
- `undisclosed_conflict`
- `missing_risk_or_limitation`
- `overstated_confidence`
- `prompt_alignment_failure`
- `human_review_boundary_failure`

## CorrectionTarget

Allowed values:

- `source_selection`
- `retrieval`
- `parsing`
- `financial_calculation`
- `financial_analysis`
- `orchestrator`
- `report_writing`
- `human_clarification`

## WorkflowStatus

Allowed values:

- `not_started`
- `in_progress`
- `awaiting_clarification`
- `additional_research_required`
- `correction_required`
- `completed`
- `failed`
- `insufficient_evidence`

## WorkflowStage

Allowed values:

- `request_intake`
- `intake_validation`
- `research_planning`
- `web_search`
- `source_selection`
- `web_retrieval`
- `content_parsing`
- `financial_analysis`
- `evidence_validation`
- `report_writing`
- `report_validation`
- `artifact_writing`
- `human_review`

---

# 2. Intake Contracts

## ResearchRequest

### Purpose

Represents the user's financial research question after structured intake.

### Fields

- `request_id: UUID`
- `workflow_id: UUID`
- `original_prompt: str`
- `research_question: str`
- `request_type: RequestType`
- `created_at: datetime`

### Validation Rules

- `original_prompt` shall not be empty.
- `research_question` shall not be empty.
- The original prompt shall be preserved without semantic rewriting.
- `created_at` shall be timezone-aware.

### Produced By

- Research Planning Agent in intake mode.

### Consumed By

- Orchestrator.
- Research Planning Agent in planning mode.
- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.

## InvestorProfile

### Purpose

Represents investor preferences explicitly supplied by the user.

### Fields

- `profile_id: UUID`
- `workflow_id: UUID`
- `risk_tolerance: RiskTolerance | None`
- `investment_objective: InvestmentObjective | None`
- `time_horizon: TimeHorizon | None`
- `growth_or_income_preference: str | None`
- `geographic_preferences: list[str]`
- `industry_preferences: list[str]`
- `excluded_regions: list[str]`
- `excluded_industries: list[str]`
- `explicit_constraints: list[str]`

### Validation Rules

- Missing preferences shall remain `None` or an empty list.
- The agent shall not create values that were not stated or confirmed.
- Geographic preferences and exclusions shall not directly contradict each
  other.
- The initial personalized workflow requires risk tolerance, investment
  objective, and time horizon.

### Produced By

- Research Planning Agent in intake mode.

### Consumed By

- Orchestrator.
- Research Planning Agent in planning mode.
- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.

## ResearchScope

### Purpose

Defines the boundaries of the requested research.

### Fields

- `scope_id: UUID`
- `workflow_id: UUID`
- `asset_types: list[AssetType]`
- `named_candidates: list[str]`
- `candidate_limit: int`
- `geographic_scope: list[str]`
- `industry_scope: list[str]`
- `excluded_candidates: list[str]`
- `additional_constraints: list[str]`

### Validation Rules

- `candidate_limit` shall be at least 1.
- The initial default maximum shall be 3 candidates.
- Named and excluded candidates shall not overlap.
- At least one supported asset type shall be present.

### Produced By

- Research Planning Agent in intake mode.

### Consumed By

- Orchestrator.
- Research Planning Agent in planning mode.
- Source Selection Agent indirectly through `ResearchPlan`.
- Evidence Validation Agent.

## IntakeResult

### Purpose

Combines structured request interpretation and clarification status.

### Fields

- `intake_id: UUID`
- `workflow_id: UUID`
- `research_request: ResearchRequest`
- `investor_profile: InvestorProfile`
- `research_scope: ResearchScope`
- `assumptions: list[str]`
- `missing_fields: list[str]`
- `requires_clarification: bool`
- `clarification_questions: list[str]`
- `created_at: datetime`

### Validation Rules

- All nested records shall use the same `workflow_id`.
- `requires_clarification` shall be `true` when required fields are missing.
- `clarification_questions` shall not be empty when clarification is
  required.
- Assumptions shall be visible and shall not silently replace missing user
  preferences.

### Produced By

- Research Planning Agent in intake mode.

### Consumed By

- Orchestrator.

---

# 3. Research Planning Contracts

## EvidenceRequirement

### Purpose

Defines a category of evidence required by the research plan.

### Fields

- `requirement_id: UUID`
- `name: str`
- `description: str`
- `candidate_name: str | None`
- `search_purpose: SearchPurpose`
- `preferred_source_categories: list[SourceCategory]`
- `required: bool`

### Validation Rules

- Name and description shall not be empty.
- Candidate name may be omitted for candidate-discovery requirements.
- At least one preferred source category shall be identified.

## SearchQuery

### Purpose

Represents one approved web-search query.

### Fields

- `query_id: UUID`
- `query: str`
- `purpose: SearchPurpose`
- `candidate_name: str | None`
- `evidence_requirement_ids: list[UUID]`

### Validation Rules

- `query` shall not be empty.
- Every evidence requirement identifier shall exist in the containing
  `ResearchPlan`.

## ResearchPlan

### Purpose

Defines what must be researched and how the initial search should proceed.

### Fields

- `plan_id: UUID`
- `workflow_id: UUID`
- `research_objective: str`
- `candidate_discovery_required: bool`
- `candidate_names: list[str]`
- `comparison_criteria: list[str]`
- `risk_categories: list[str]`
- `evidence_requirements: list[EvidenceRequirement]`
- `search_queries: list[SearchQuery]`
- `preferred_source_categories: list[SourceCategory]`
- `candidate_limit: int`
- `source_limit_per_candidate: int`
- `assumptions: list[str]`
- `created_at: datetime`

### Validation Rules

- Research objective shall not be empty.
- At least one comparison criterion shall be present.
- At least one evidence requirement shall be present.
- At least one search query shall be present.
- Candidate limit shall agree with `ResearchScope`.
- All nested identifiers shall be unique within the plan.
- Every search-query evidence reference shall resolve to an evidence
  requirement in the plan.

### Produced By

- Research Planning Agent in planning mode.

### Consumed By

- Orchestrator.
- Web Search Tool.
- Source Selection Agent.
- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.

---

# 4. Search and Source-Selection Contracts

## SearchResult

### Purpose

Represents one result returned by the Web Search Tool.

### Fields

- `search_result_id: UUID`
- `workflow_id: UUID`
- `query_id: UUID`
- `title: str`
- `url: HttpUrl`
- `snippet: str | None`
- `domain: str`
- `result_position: int | None`
- `retrieved_from_search_at: datetime`

### Validation Rules

- Title and URL shall be present.
- URL shall use a supported public HTTP scheme.
- Result position, when available, shall be positive.
- The query identifier shall reference an executed `SearchQuery`.

### Produced By

- Web Search Tool.

### Consumed By

- Source Selection Agent.
- Orchestrator.

## SelectedSource

### Purpose

Represents the Source Selection Agent's decision about one search result.

### Fields

- `selection_id: UUID`
- `search_result_id: UUID`
- `selected: bool`
- `selection_reason: str`
- `candidate_name: str | None`
- `evidence_requirement_ids: list[UUID]`
- `expected_source_category: SourceCategory`
- `possible_duplicate: bool`
- `possible_derivative_source: bool`
- `exclusion_reason: str | None`

### Validation Rules

- Selection reason shall not be empty.
- A selected result shall reference at least one evidence requirement.
- An excluded result should include an exclusion reason.
- Preliminary source category shall not be interpreted as final source
  validation.

## AdditionalResearchRequest

### Purpose

Requests another bounded research pass to resolve a material evidence gap.

### Fields

- `request_id: UUID`
- `workflow_id: UUID`
- `requested_by_stage: WorkflowStage`
- `candidate_name: str | None`
- `missing_evidence: str`
- `evidence_requirement_id: UUID | None`
- `reason: str`
- `suggested_search_purpose: SearchPurpose`
- `blocks_recommendation: bool`

### Validation Rules

- Missing evidence and reason shall not be empty.
- Requested stage shall identify the component creating the request.
- The orchestrator decides whether the request may be executed.

## SourceSelection

### Purpose

Represents the Source Selection Agent's complete source-selection decision.

### Fields

- `source_selection_id: UUID`
- `workflow_id: UUID`
- `plan_id: UUID`
- `status: SourceSelectionStatus`
- `selections: list[SelectedSource]`
- `uncovered_evidence_requirement_ids: list[UUID]`
- `additional_research_requests: list[AdditionalResearchRequest]`
- `created_at: datetime`

### Validation Rules

- All referenced search-result identifiers shall be unique.
- `ready_for_retrieval` requires at least one selected result.
- `additional_search_required` requires at least one additional research
  request.
- `insufficient_candidate_sources` shall identify uncovered evidence
  requirements when applicable.

### Produced By

- Source Selection Agent.

### Consumed By

- Orchestrator.
- URL-validation and retrieval functions.

---

# 5. Retrieval and Evidence Contracts

## RetrievalResult

### Purpose

Records the result of retrieving one selected webpage. Tavily returns
raw page content directly in the same search call used for source
selection, so there is no separate retrieval step in the implemented
system — this contract exists in the schema but is not constructed by
any current agent or tool.

### Fields

- `retrieval_id: UUID`
- `workflow_id: UUID`
- `search_result_id: UUID`
- `requested_url: HttpUrl`
- `final_url: HttpUrl | None`
- `status: RetrievalStatus`
- `http_status_code: int | None`
- `content_type: str | None`
- `retrieved_at: datetime | None`
- `error_message: str | None`

### Validation Rules

- Successful retrieval requires a final URL and retrieval timestamp.
- Failed retrieval requires an error message.
- Secret values shall not appear in error messages.

### Produced By

- Not produced in the implemented system; see Purpose above.

### Consumed By

- Not consumed in the implemented system; see Purpose above.

## SourceRecord

### Purpose

Represents a retrieved and parsed public source.

### Fields

- `source_id: UUID`
- `workflow_id: UUID`
- `retrieval_id: UUID`
- `search_result_id: UUID`
- `title: str`
- `url: HttpUrl`
- `publisher: str | None`
- `author: str | None`
- `publication_date: date | None`
- `retrieval_date: date`
- `source_category: SourceCategory`
- `parsing_status: ParsingStatus`
- `candidate_names: list[str]`
- `evidence_requirement_ids: list[UUID]`
- `content_summary: str | None`
- `limitations: list[str]`

### Validation Rules

- Title, URL, retrieval date, and parsing status are required.
- Missing author or publication date shall remain `None`.
- Successful parsing requires an available content summary or extracted
  evidence.
- Source category shall be based on the retrieved source rather than only
  the search snippet.
- Search snippets shall not be stored as retrieved source evidence.

### Produced By

- Deterministic metadata-extraction and parsing functions.

### Consumed By

- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.
- Evidence-Lookup Tool.

## ExtractedEvidence

### Purpose

Represents one factual passage or structured value extracted from a source.

### Fields

- `evidence_id: UUID`
- `workflow_id: UUID`
- `source_id: UUID`
- `candidate_name: str | None`
- `evidence_requirement_id: UUID | None`
- `evidence_type: str`
- `content: str`
- `section_heading: str | None`
- `reported_value: Decimal | None`
- `currency: str | None`
- `unit: str | None`
- `reporting_period: str | None`
- `supports_candidate: bool | None`
- `extraction_notes: list[str]`

### Validation Rules

- Content shall not be empty.
- Every evidence item shall reference an existing source.
- Numeric evidence shall preserve available currency, unit, and reporting
  period.
- `supports_candidate` may remain `None` before financial interpretation.
- Extraction notes shall distinguish direct source content from
  parser-generated context.
- Webpage instructions shall remain evidence content and shall never become
  application instructions.

### Produced By

- Deterministic parser and evidence-extraction functions.

### Consumed By

- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.
- Evidence-Lookup Tool.

---

# 6. Financial Analysis Contracts

The current Phase 6 implementation uses `CalculatedMetric` as the
calculation-tool output. `CalculationRecord` remains a broader contract for
future status-oriented calculation workflows, but Phase 7 claim validation
must understand the evidence lineage on `CalculatedMetric` records.

## FinancialInput

### Purpose

Represents one validated numeric value that may enter a financial
calculation.

### Fields

- `input_id: UUID`
- `workflow_id: UUID`
- `candidate_name: str`
- `metric_name: str`
- `value: Decimal | None`
- `currency: str | None`
- `unit: str | None`
- `reporting_period: str`
- `availability_status: DataAvailabilityStatus`
- `evidence_id: UUID`

### Validation Rules

- Available input requires a numeric value.
- Missing, unavailable, invalid, and non-applicable input shall not contain
  a usable numeric value.
- Every input shall reference collected evidence.
- Inputs used together shall belong to compatible candidates and reporting
  periods.
- Currency and units shall be preserved when relevant.

## CalculationRecord

### Purpose

Preserves one deterministic financial calculation and its source lineage.

### Fields

- `calculation_id: UUID`
- `workflow_id: UUID`
- `candidate_name: str | None`
- `calculation_type: CalculationType`
- `status: CalculationStatus`
- `formula_name: str`
- `input_ids: list[UUID]`
- `result: Decimal | None`
- `result_unit: str | None`
- `reporting_period: str | None`
- `limitations: list[str]`
- `created_at: datetime`

### Validation Rules

- Completed calculations require a numeric result.
- Failed, missing-input, invalid-input, or non-applicable calculations may
  not contain a final usable result.
- Every input identifier shall resolve to a `FinancialInput`.
- A weighted score may omit candidate name only when it represents a
  workflow-level comparison.
- Formula name shall identify the approved deterministic formula.
- Calculation records are immutable after creation. Corrections create a
  replacement record.

### Produced By

- Deterministic financial-calculation functions.

### Consumed By

- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent.
- Evidence-Lookup Tool.

## CalculatedMetric

### Purpose

Represents one completed generic calculation accepted by the Phase 6
financial-calculation tool.

### Fields

- `calculation_id: UUID`
- `workflow_id: UUID`
- `operation: CalculationOperation`
- `metric_name: str`
- `candidate_names: list[str]`
- `value: Decimal`
- `unit: str | None`
- `currency: str | None`
- `input_evidence_ids: list[UUID]`
- `formula: str`
- `reporting_periods: list[str]`
- `limitations: list[str]`

### Validation Rules

- Exactly two distinct evidence identifiers are required.
- Both evidence records shall belong to the same workflow.
- The operation shall be one of the supported generic operations:
  growth, margin, ratio, or difference.
- Candidate names shall be unique within the calculation.
- The formula, value, units, currency, periods, and input evidence shall be
  preserved for later claim validation.

### Produced By

- Deterministic financial-calculation tool.

### Consumed By

- Financial Analysis Agent.
- Evidence Validation Agent.
- Report Writing Agent after validation.

## CategoryEvaluation

### Purpose

Represents the Financial Analysis Agent's evaluation of one methodology
category for one candidate.

### Fields

- `evaluation_id: UUID`
- `workflow_id: UUID`
- `candidate_name: str`
- `category_name: str`
- `availability_status: DataAvailabilityStatus`
- `score: Decimal | None`
- `calculation_ids: list[UUID]`
- `supporting_evidence_ids: list[UUID]`
- `opposing_evidence_ids: list[UUID]`
- `risks: list[str]`
- `missing_information: list[str]`
- `rationale: str`
- `confidence: ConfidenceLevel`

### Validation Rules

- Score, when present, shall be between 0 and 100.
- Missing or non-applicable categories shall not receive a score.
- Rationale shall not be empty.
- Evidence and calculation identifiers shall resolve within the same
  workflow.
- Confidence shall describe evidence strength rather than expected return.

## CandidateAnalysis

### Purpose

Represents the completed analysis of one investment candidate.

### Fields

- `analysis_id: UUID`
- `workflow_id: UUID`
- `candidate_name: str`
- `status: AnalysisStatus`
- `category_evaluations: list[CategoryEvaluation]`
- `calculation_ids: list[UUID]`
- `strengths: list[str]`
- `weaknesses: list[str]`
- `material_risks: list[str]`
- `supporting_evidence_ids: list[UUID]`
- `opposing_evidence_ids: list[UUID]`
- `missing_information: list[str]`
- `unresolved_conflicts: list[str]`
- `weighted_score: Decimal | None`
- `confidence: ConfidenceLevel`
- `rationale: str`

### Validation Rules

- Candidate name and rationale shall not be empty.
- Completed analysis requires at least one category evaluation.
- Weighted score, when present, shall be between 0 and 100.
- Insufficient-evidence analysis shall not require a weighted score.
- Evidence and calculation identifiers shall resolve within the workflow.
- Material risks shall not be removed because they weaken the candidate.
- Supporting and opposing evidence may not contain unknown identifiers.

### Produced By

- Financial Analysis Agent.

### Consumed By

- Evidence Validation Agent.
- Report Writing Agent.

## RecommendationResult

### Purpose

Represents the preliminary financial research conclusion.

### Fields

- `recommendation_id: UUID`
- `workflow_id: UUID`
- `outcome: RecommendationOutcome`
- `preferred_candidate: str | None`
- `alternative_candidates: list[str]`
- `ranked_candidates: list[str]`
- `candidate_analysis_ids: list[UUID]`
- `supporting_evidence_ids: list[UUID]`
- `opposing_evidence_ids: list[UUID]`
- `material_risks: list[str]`
- `missing_information: list[str]`
- `unresolved_conflicts: list[str]`
- `rationale: str`
- `confidence: ConfidenceLevel`
- `human_review_required: bool`

### Validation Rules

- Rationale shall not be empty.
- Human review shall always be required.
- Ranked or qualified recommendations require a preferred candidate.
- Research-shortlist outcomes shall not require one preferred candidate.
- No-aligned-candidate and insufficient-evidence outcomes shall not identify
  a preferred candidate.
- Ranked candidates shall correspond to available candidate analyses.
- Evidence references shall resolve within the workflow.
- The result shall not contain trade instructions or guarantees.

### Produced By

- Financial Analysis Agent.

### Consumed By

- Evidence Validation Agent.
- Report Writing Agent only after approval.

---

# 7. Validation Contracts

## ValidationClaim

### Purpose

Represents one material claim submitted to Phase 7 validation. Claims may
cite source evidence, deterministic calculations, or both.

### Fields

- `claim_id: UUID`
- `workflow_id: UUID`
- `text: str`
- `candidate_name: str | None`
- `source_ids: list[UUID]`
- `evidence_ids: list[UUID]`
- `calculation_id: UUID | None`
- `expected_value: Decimal | None`
- `expected_unit: str | None`
- `expected_currency: str | None`
- `expected_reporting_periods: list[str]`

### Validation Rules

- A claim shall reference at least one source, evidence, or calculation.
- Expected calculation metadata requires a calculation identifier.
- Source and evidence identifiers shall be unique within the claim.
- Calculated claims shall be checked against the recorded result and
  calculation lineage.

### Produced By

- Financial Analysis Agent or report-preparation boundary.

### Consumed By

- Evidence Validation Agent.

## ValidationFinding

### Purpose

Represents one problem discovered during evidence validation.

### Fields

- `finding_id: UUID`
- `workflow_id: UUID`
- `category: ValidationCategory`
- `severity: ValidationSeverity`
- `candidate_name: str | None`
- `affected_claim: str | None`
- `affected_calculation_id: UUID | None`
- `source_ids: list[UUID]`
- `evidence_ids: list[UUID]`
- `description: str`
- `required_correction: str | None`
- `correction_target: CorrectionTarget`

### Validation Rules

- Description shall not be empty.
- Blocking findings require a correction or workflow-stopping explanation.
- Referenced identifiers shall exist in the same workflow.
- A finding shall identify enough context for the orchestrator to route it.

## ValidationResult

### Purpose

Represents the Evidence Validation Agent's decision about the preliminary
recommendation.

### Fields

- `validation_id: UUID`
- `workflow_id: UUID`
- `recommendation_id: UUID`
- `outcome: ValidationOutcome`
- `findings: list[ValidationFinding]`
- `approved_candidate_analysis_ids: list[UUID]`
- `approved_source_ids: list[UUID]`
- `approved_evidence_ids: list[UUID]`
- `approved_calculation_ids: list[UUID]`
- `additional_research_requests: list[AdditionalResearchRequest]`
- `summary: str`
- `validated_at: datetime`

### Validation Rules

- Summary shall not be empty.
- Approved outcome shall contain no blocking findings.
- Analysis-correction outcome shall identify at least one correction finding.
- Additional-research outcome shall contain at least one research request.
- Rejected outcome shall include at least one blocking finding.
- Approval lists shall contain only identifiers from the same workflow.
- Approval does not authorize trade execution or remove human review.

### Produced By

- Evidence Validation Agent.

### Consumed By

- Orchestrator.
- Report Writing Agent.
- Report structural validator.

---

# 8. Report Contracts

## ReportDraft

### Purpose

Represents the Markdown report content produced before deterministic file
writing.

### Fields

- `report_id: UUID`
- `workflow_id: UUID`
- `title: str`
- `markdown_content: str`
- `recommendation_outcome: RecommendationOutcome`
- `source_ids: list[UUID]`
- `evidence_ids: list[UUID]`
- `calculation_ids: list[UUID]`
- `human_review_statement: str`
- `validation_id: UUID`
- `created_at: datetime`

### Validation Rules

- Title and Markdown content shall not be empty.
- The validation identifier shall reference an approved or
  insufficient-evidence `ValidationResult`.
- Source, evidence, and calculation identifiers shall be approved by the
  referenced validation result.
- Human-review statement shall not be empty.
- Recommendation outcome shall match the validated outcome.
- The draft shall not contain a preferred candidate for an
  insufficient-evidence result.

### Produced By

- Report Writing Agent.

### Consumed By

- Deterministic report validator.
- Markdown file writer.

## ReportArtifact

### Purpose

Records the result of writing one final report file.

### Fields

- `artifact_id: UUID`
- `workflow_id: UUID`
- `report_id: UUID`
- `artifact_type: str`
- `filename: str`
- `relative_path: str`
- `created_at: datetime`
- `write_successful: bool`
- `error_message: str | None`

### Validation Rules

- Artifact type shall initially be `markdown_report`.
- Relative path shall remain inside the approved output directory.
- Successful write shall not contain an error message.
- Failed write shall contain an error message.
- Absolute developer-specific paths shall not be preserved in shared JSON
  artifacts.

### Produced By

- Deterministic Markdown file writer.

### Consumed By

- Orchestrator.
- Workflow artifact writer.

## WorkflowArtifact

### Purpose

Represents the structured JSON record of the completed workflow.

### Fields

- `artifact_id: UUID`
- `workflow_id: UUID`
- `research_request: ResearchRequest`
- `investor_profile: InvestorProfile`
- `research_scope: ResearchScope`
- `research_plan: ResearchPlan`
- `source_records: list[SourceRecord]`
- `evidence_records: list[ExtractedEvidence]`
- `calculation_records: list[CalculationRecord]`
- `candidate_analyses: list[CandidateAnalysis]`
- `recommendation_result: RecommendationResult`
- `validation_result: ValidationResult`
- `report_artifact: ReportArtifact | None`
- `workflow_status: WorkflowStatus`
- `created_at: datetime`

### Validation Rules

- All nested records shall use the same workflow identifier.
- Completed status requires a validation result and report artifact.
- An approved recommendation requires successful report creation.
- Insufficient-evidence status may contain a limitation report.
- Failed workflows may omit a report artifact.
- Secret credentials and raw HTML shall not be included.

### Produced By

- Deterministic workflow artifact writer.

### Consumed By

- Human reviewer.
- Tests.
- Debugging and traceability processes.

---

# 9. Workflow Contracts

## WorkflowError

### Purpose

Represents a structured workflow failure.

### Fields

- `error_id: UUID`
- `workflow_id: UUID`
- `stage: WorkflowStage`
- `error_type: str`
- `message: str`
- `recoverable: bool`
- `correction_target: CorrectionTarget | None`
- `related_record_ids: list[UUID]`
- `created_at: datetime`

### Validation Rules

- Error type and message shall not be empty.
- Recoverable errors should identify a correction target.
- Error messages shall not contain API keys, tokens, or secret values.

## StageResult

### Purpose

Records the completion status and output identifiers of one workflow stage.

### Fields

- `stage_result_id: UUID`
- `workflow_id: UUID`
- `stage: WorkflowStage`
- `status: WorkflowStatus`
- `output_record_ids: list[UUID]`
- `errors: list[WorkflowError]`
- `started_at: datetime`
- `completed_at: datetime | None`
- `attempt_number: int`

### Validation Rules

- Attempt number shall be at least 1.
- Completed stages require a completion timestamp.
- Failed stages require at least one workflow error.
- Completion time shall not precede start time.

## WorkflowState

### Purpose

Represents the current state of one research workflow.

### Fields

- `workflow_id: UUID`
- `status: WorkflowStatus`
- `current_stage: WorkflowStage`
- `original_prompt: str`
- `stage_results: list[StageResult]`
- `clarification_count: int`
- `search_pass_count: int`
- `analysis_correction_count: int`
- `validation_attempt_count: int`
- `record_ids: list[UUID]`
- `started_at: datetime`
- `updated_at: datetime`
- `completed_at: datetime | None`

### Validation Rules

- Counters shall not be negative.
- Current stage shall agree with the latest stage result.
- Completed workflow requires a completion timestamp.
- Failed workflow shall preserve the failure stage.
- Retry counters shall remain within configured workflow limits.
- Raw secrets shall not be stored in workflow state.

### Produced By

- Deterministic Python orchestrator.

### Consumed By

- Deterministic Python orchestrator.
- Logging and workflow-status components.
- Tests.

---

# 10. Contract Relationships

The primary contract handoff is:

```text
Original User Prompt
    ↓
IntakeResult
    ├── ResearchRequest
    ├── InvestorProfile
    └── ResearchScope
    ↓
ResearchPlan
    ├── EvidenceRequirement
    └── SearchQuery
    ↓
SearchResult
    ↓
SourceSelection
    └── SelectedSource
    ↓
RetrievalResult
    ↓
SourceRecord
    ↓
ExtractedEvidence
    ↓
FinancialInput
    ↓
  CalculatedMetric
    ↓
CategoryEvaluation
    ↓
CandidateAnalysis
    ↓
RecommendationResult
    ↓
ValidationResult
    └── ValidationFinding
    ↓
ReportDraft
    ↓
ReportArtifact
    ↓
WorkflowArtifact
```

`WorkflowState`, `StageResult`, `WorkflowError`, and
`AdditionalResearchRequest` operate across the primary handoff.

# 11. Implementation Organization

The Pydantic models may be implemented in separate modules:

```text
models/
├── common.py
├── intake.py
├── research.py
├── sources.py
├── financial.py
├── validation.py
├── reports.py
└── workflow.py
```

Suggested ownership:

- `common.py`: enumerations and shared types.
- `intake.py`: request, profile, scope, and intake-result models.
- `research.py`: research plan, search query, and evidence requirements.
- `sources.py`: search results, source selection, retrieval, sources, and
  evidence.
- `financial.py`: financial inputs, calculations, category evaluations,
  candidate analyses, and recommendations.
- `validation.py`: validation findings and validation results.
- `reports.py`: report drafts and output artifacts.
- `workflow.py`: workflow state, stage results, errors, and additional
  research requests.

The final code structure may be adjusted without changing these contracts,
provided the model responsibilities and field behavior remain consistent.

# 12. Contract Testing Requirements

Each contract shall have tests covering:

- Valid construction.
- Missing required fields.
- Invalid enum values.
- Invalid identifier relationships.
- Wrong data types.
- Boundary values.
- Cross-field validation.
- JSON serialization.
- JSON deserialization.

Required cross-model tests include:

- Mismatched workflow identifiers.
- Unknown source identifiers.
- Unknown evidence identifiers.
- Unknown calculation identifiers.
- Available financial input without a value.
- Completed calculation without a result.
- Non-applicable calculation with a usable result.
- Missing category data represented as a low score.
- Ranked recommendation without a preferred candidate.
- Insufficient-evidence result with a preferred candidate.
- Approved validation containing a blocking finding.
- Report draft referencing unapproved evidence.
- Output path escaping the approved output directory.
- Completed workflow without a final artifact.

# 13. Change Control

When a data contract changes:

1. The related functional requirements shall be reviewed.
2. The related agent-workflow section shall be reviewed.
3. Producers and consumers of the contract shall be identified.
4. Pydantic models shall be updated.
5. Contract tests shall be updated.
6. JSON example artifacts shall be updated.
7. Architecture documentation shall be updated when the handoff changes.
8. The roadmap shall be updated when the change affects phase scope or
   implementation order.