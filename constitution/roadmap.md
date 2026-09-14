# Project Roadmap

## Purpose

This roadmap defines the development trajectory for Agentic Financial
Analysis Automation.

The roadmap organizes the project into phases so that specifications,
architecture, implementation, validation, testing, and documentation are
completed in a deliberate order.

This is a living planning document. Phase status, deliverables, and
sequencing may change when implementation, testing, or technical
discoveries require the plan to be revised.

Roadmap changes must remain consistent with:

- `constitution/mission.md`
- `constitution/tech-stack.md`
- Approved project specifications

## Project Trajectory

The project follows a specification-driven development process:

1. Define the project mission and technical boundaries.
2. Document functional and non-functional requirements.
3. Define data contracts, agent responsibilities, and architecture.
4. Create the project structure and development environment.
5. Build the web-search and scraping vertical slice.
6. Implement financial calculations and candidate analysis.
7. Implement evidence validation and safety controls.
8. Implement report and artifact generation.
9. Integrate the complete multi-agent workflow.
10. Complete quality, adversarial, and acceptance testing.
11. Finalize documentation and prepare the capstone submission.

Each phase must satisfy its exit criteria before it is marked complete.

## Phase Status Definitions

The roadmap uses the following statuses:

- **Not Started**: Work on the phase has not begun.
- **In Progress**: Work on the phase is currently active.
- **Blocked**: Work cannot continue until a dependency or issue is resolved.
- **Completed**: The phase deliverables and exit criteria have been
  satisfied.
- **Deferred**: The phase or capability has been intentionally postponed.
- **Out of Scope**: The work is not part of the current capstone version.

## Current Project Status

| Phase | Status |
|---|---|
| Phase 1: Project Foundation and Constitution | Completed |
| Phase 2: Detailed Specifications | Completed |
| Phase 3: Data Contracts and Agent Architecture | Completed |
| Phase 4: Project Structure and Development Environment | Completed |
| Phase 5: Web Research Vertical Slice | Not Started |
| Phase 6: Financial Analysis and Recommendation Logic | Not Started |
| Phase 7: Evidence Validation and Safety | Not Started |
| Phase 8: Report and Artifact Generation | Not Started |
| Phase 9: Complete Workflow Integration | Not Started |
| Phase 10: Testing and Quality Verification | Not Started |
| Phase 11: Documentation and Submission Preparation | Not Started |

## Current Focus

The project is currently beginning Phase 4: Project Structure and
Development Environment.

The current work will include:

- Creating the approved repository structure.
- Creating the Python source package.
- Creating the initial test structure.
- Creating `requirements.txt`.
- Creating `.env.example`.
- Creating `.gitignore`.
- Implementing environment configuration.
- Implementing logging and exception foundations.
- Translating the approved data contracts into Pydantic models.
- Writing the first model-validation tests.

No agent workflow logic will be implemented until the project foundation
and core contracts can be imported and tested successfully.

---

## Phase 1: Project Foundation and Constitution

### Status

Completed

### Goal

Establish the project's purpose, boundaries, approved technologies, and
development trajectory before implementation begins.

### Completed Deliverables

- Initial `README.md` outline.
- `constitution/mission.md`
- `constitution/tech-stack.md`
- `constitution/roadmap.md`
- Repository naming conventions.
- Defined system boundaries.
- Defined capstone artifact requirements.

### Completed Decisions

- The system is an investment research and decision-support application.
- The system produces informational recommendations for human review.
- The system does not execute trades.
- The system does not access brokerage accounts.
- The system does not control user funds.
- The system does not guarantee investment performance.
- The final investment decision remains with the human user.
- Python 3.12.3 is the approved programming language.
- `smolagents` is the approved agent framework.
- Pydantic is the approved structured-data framework.
- Tavily is the approved web-search provider.
- Requests and Beautiful Soup 4 are the approved retrieval and parsing
  libraries.
- Pytest is the approved test framework.

### Exit Criteria

Phase 1 was completed when:

- The README contained an initial project overview.
- The mission defined the problem, audience, capabilities, boundaries, and
  success criteria.
- The technology stack defined approved technologies and responsibilities.
- The roadmap defined the initial development trajectory.
- The constitution documents were mutually consistent.
- The project scope was sufficiently clear to begin detailed
  specifications.

---

## Phase 2: Detailed Specifications

### Status

Completed

### Goal

Translate the project mission into explicit, testable system requirements.

### Completed Deliverables

- `specs/functional-requirements.md`
- `specs/non-functional-requirements.md`
- `specs/source-policy.md`
- `specs/safety-requirements.md`
- `specs/recommendation-methodology.md`
- `specs/acceptance-criteria.md`

### Completed Specification Areas

The specifications define:

- Natural-language research input.
- Investor-profile input.
- Missing-input and clarification behavior.
- Research-plan creation.
- Web-search behavior.
- Source-selection behavior.
- Website retrieval and scraping.
- Evidence extraction and traceability.
- Financial-calculation requirements.
- Candidate-analysis behavior.
- Recommendation outcomes.
- Claim and citation validation.
- Risk and limitation disclosure.
- Report and artifact output.
- Workflow failure behavior.
- Human-review requirements.
- Adversarial safety requirements.

### Exit Criteria

Phase 2 was completed when:

- Functional requirements were numbered and documented.
- Non-functional requirements were documented.
- Required investor-profile fields were defined.
- Source-quality and citation rules were defined.
- Recommendation-methodology requirements were defined.
- Safety and untrusted-content requirements were defined.
- Acceptance criteria mapped to the major requirements.
- Major behaviors could be verified through testing or inspection.
- No major workflow behavior depended on an undocumented assumption.

### Dependencies

Phase 2 depended on completion of Phase 1.

---

## Phase 3: Data Contracts and Agent Architecture

### Status

Completed

### Goal

Define the structured data exchanged throughout the workflow and assign
clear responsibilities to agents, tools, and deterministic Python code.

### Completed Deliverables

- `specs/data-contracts.md`
- `specs/agent-workflows.md`
- `docs/architecture.md`
- `docs/architecture.mmd`
- `docs/architecture.png`

### Approved Agent Architecture

The system uses five specialized agents:

1. Research Planning Agent.
2. Source Selection Agent.
3. Financial Analysis Agent.
4. Evidence Validation Agent.
5. Report Writing Agent.

The agents are coordinated by a deterministic Python orchestrator.

### Approved Agent Responsibilities

#### Research Planning Agent

- Interprets the natural-language request.
- Produces structured intake data.
- Identifies missing investor information.
- Creates the approved `ResearchPlan`.

#### Source Selection Agent

- Reviews structured search results.
- Selects candidate sources for retrieval.
- Evaluates evidence coverage.
- Identifies duplicate or derivative-source concerns.
- Requests additional searches when necessary.

#### Financial Analysis Agent

- Interprets validated evidence.
- Requests deterministic calculations.
- Compares investment candidates.
- Evaluates investor-profile alignment.
- Produces candidate analyses.
- Produces the preliminary recommendation outcome.

#### Evidence Validation Agent

- Verifies claim support.
- Verifies evidence and calculation traceability.
- Checks recommendation alignment with the original request.
- Identifies unsupported conclusions.
- Approves, redirects, or rejects the preliminary result.

#### Report Writing Agent

- Converts approved findings into a Markdown research report.
- Uses only approved evidence and calculations.
- Includes risks, limitations, citations, and human-review language.
- Produces a validated `ReportDraft`.

### Approved Deterministic Components

Deterministic Python code is responsible for:

- Workflow orchestration.
- Pydantic validation.
- Tavily search execution.
- URL validation.
- Duplicate URL detection.
- HTTP retrieval.
- HTML parsing.
- Evidence-record creation.
- Financial arithmetic.
- Structural report validation.
- Markdown file writing.
- JSON artifact writing.
- Retry-limit enforcement.
- Error handling.

### Approved Financial Tools

The initial Financial Analysis Agent may use:

- Revenue-Growth Calculator.
- Profit-Margin Calculator.
- Debt-to-Equity Calculator.
- Price-to-Earnings Calculator.
- Weighted-Score Calculator.
- Evidence-Lookup Tool.

Currency conversion, liquidity ratios, technical indicators, discounted
cash-flow models, and advanced market-analysis calculations are not part of
the initial implementation.

### Approved Data-Contract Areas

The approved contracts cover:

- Intake and investor profile.
- Research planning.
- Search results and source selection.
- Retrieval and extracted evidence.
- Financial inputs and calculations.
- Candidate analyses and recommendations.
- Validation findings and results.
- Report drafts and artifacts.
- Workflow state and structured errors.

Important approved contracts include:

- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`
- `IntakeResult`
- `ResearchPlan`
- `EvidenceRequirement`
- `SearchQuery`
- `SearchResult`
- `SourceSelection`
- `RetrievalResult`
- `SourceRecord`
- `ExtractedEvidence`
- `FinancialInput`
- `CalculationRecord`
- `CategoryEvaluation`
- `CandidateAnalysis`
- `RecommendationResult`
- `ValidationFinding`
- `ValidationResult`
- `ReportDraft`
- `ReportArtifact`
- `WorkflowArtifact`
- `WorkflowState`
- `WorkflowError`

### Approved Architecture Flow

The primary system flow is:

```text
Human User
→ Python Orchestrator
→ Research Planning Agent
→ Source Selection Agent
→ Web Search and Scraping Tools
→ Financial Analysis Agent
→ Financial Calculation Tools
→ Evidence Validation Agent
→ Report Writing Agent
→ Markdown and JSON File Writers
→ Research Report
→ Human Review
```

Detailed correction paths are documented in `docs/architecture.md` and
`specs/agent-workflows.md`.

The architecture diagram intentionally presents a simplified high-level
view rather than every workflow status, contract, and failure path.

### Exit Criteria

Phase 3 was completed when:

- Major workflow data models were documented.
- Required and optional fields were identified.
- Agent responsibilities were clearly separated.
- Agent stopping conditions were defined.
- Deterministic Python responsibilities were separated from agent
  responsibilities.
- The five-agent architecture was documented.
- The deterministic orchestrator responsibility was documented.
- Workflow order and correction paths were documented.
- Validation gates were defined.
- Human-review boundaries were preserved.
- The Mermaid architecture diagram matched the approved high-level
  architecture.
- The architecture diagram was exported as a PNG.
- The architecture supported the approved functional requirements.

### Dependencies

Phase 3 depended on completion of Phase 2.

---

## Phase 4: Project Structure and Data-Contract Implementation

### Status

Completed

### Goal

Create a reproducible Python project foundation and implement the Pydantic
models defined in `specs/data-contracts.md`.

Phase 4 converts the approved data-contract specification into tested
Python models before the agents and workflow logic are implemented.

### Planned Deliverables

- Python source and test structure.
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `pyproject.toml`
- Application configuration.
- Custom exception hierarchy.
- Logging configuration.
- Pydantic data-contract models.
- Model-validation tests.
- JSON serialization and deserialization tests.

### Repository Structure

```text
src/
└── fin_automation/
    ├── __init__.py
    ├── config.py
    ├── exceptions.py
    ├── logging_config.py
    └── models/
        ├── common.py
        ├── intake.py
        ├── research.py
        ├── sources.py
        ├── financial.py
        ├── validation.py
        ├── reports.py
        └── workflow.py

tests/
├── test_config.py
├── test_exceptions.py
├── test_logging_config.py
└── test_models/
    ├── test_intake.py
    ├── test_research.py
    ├── test_sources.py
    ├── test_financial.py
    ├── test_validation.py
    ├── test_reports.py
    └── test_workflow.py
```

Files shall be created when their implementation unit begins rather than
as empty placeholders.

### Implementation Order

Phase 4 shall be implemented in the following order.

#### 4.1 Project Configuration

Status: **Completed**

Implementation:

- `src/fin_automation/config.py`
- `tests/test_config.py`

Includes:

- Environment-variable loading.
- Required-setting validation.
- Secret-value protection.
- OpenAI base-URL validation.
- Isolated configuration testing.

#### 4.2 Exception Hierarchy

Status: **Completed**

Implementation:

- `src/fin_automation/exceptions.py`
- `tests/test_exceptions.py`

Includes:

- Common application exception.
- Configuration errors.
- Workflow errors.
- Research, retrieval, and parsing errors.
- Calculation errors.
- Evidence-validation errors.
- Report-generation errors.

#### 4.3 Logging Configuration

Status: **Completed**

Implementation:

- `src/fin_automation/logging_config.py`
- `tests/test_logging_config.py`

Includes:

- Standard application logging.
- Configurable logging levels.
- Prevention of duplicate handlers.
- Configured secret-value redaction.

#### 4.4 Intake Contracts

Status: **Completed**

Implementation:

- `src/fin_automation/models/common.py`
- `src/fin_automation/models/intake.py`
- `tests/test_models/test_intake.py`

Contracts:

- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`
- `IntakeResult`

Shared enums:

- `RiskTolerance`
- `InvestmentObjective`
- `TimeHorizon`
- `RequestType`
- `AssetType`

#### 4.5 Research-Planning Contracts

Status: **Completed**

Implementation:

- Update `src/fin_automation/models/common.py`
- Create `src/fin_automation/models/research.py`
- Create `tests/test_models/test_research.py`

Contracts:

- `EvidenceRequirement`
- `SearchQuery`
- `ResearchPlan`
- `AdditionalResearchRequest`

Shared enums:

- `SearchPurpose`
- `SourceCategory`
- Required `WorkflowStage` values

Required validation includes:

- Nonempty research objective.
- At least one comparison criterion.
- At least one evidence requirement.
- At least one search query.
- Unique nested identifiers.
- Valid search-query references to evidence requirements.
- Bounded candidate and source limits.

#### 4.6 Source and Evidence Contracts

Status: **Completed**

Implementation:

- Update `src/fin_automation/models/common.py`
- Create `src/fin_automation/models/sources.py`
- Create `tests/test_models/test_sources.py`

Contracts:

- `SearchResult`
- `SelectedSource`
- `SourceSelection`
- `RetrievalResult`
- `SourceRecord`
- `ExtractedEvidence`

Required validation includes:

- Supported public HTTP URLs.
- Valid search-query references.
- Evidence-requirement references for selected results.
- Selected sources for ready-for-retrieval outcomes.
- Error information for failed retrievals.
- Source references for extracted evidence.
- Currency, unit, and reporting-period preservation when available.

#### 4.7 Financial Contracts

Status: **Completed**

Implementation:

- Update `src/fin_automation/models/common.py`
- Create `src/fin_automation/models/financial.py`
- Create `tests/test_models/test_financial.py`

Contracts:

- `FinancialInput`
- `CalculationRecord`
- `CategoryEvaluation`
- `CandidateAnalysis`
- `RecommendationResult`

Required validation includes:

- Numeric values for available financial inputs.
- No usable values for missing or non-applicable inputs.
- Results for completed calculations.
- Scores between zero and one hundred.
- No low substitute score for missing data.
- Preferred candidate for ranked recommendations.
- No preferred candidate for insufficient-evidence outcomes.
- Mandatory human review.

#### 4.8 Validation Contracts

Status: **Completed**

Implementation:

- Update `src/fin_automation/models/common.py`.
- Create `src/fin_automation/models/validation.py`.
- Create `tests/test_models/test_validation.py`.

Contracts:

- `ValidationFinding`
- `ValidationResult`

Shared enums:

- `ValidationOutcome`
- `ValidationSeverity`
- `ValidationCategory`
- `CorrectionTarget`

Required validation includes:

- Correction details for blocking findings.
- An affected claim for unsupported-claim findings.
- An affected calculation for calculation-input findings.
- Source or evidence references for citation findings.
- Unique source and evidence identifiers.
- No blocking findings in approved results.
- At least one finding for analysis-correction outcomes.
- At least one additional research request for additional-research
  outcomes.
- At least one blocking finding for rejected outcomes.
- Matching workflow identifiers for nested findings.
- Matching workflow identifiers for additional research requests.
- Unique approved-record identifiers.
- Timezone-aware validation timestamps.
- JSON serialization and reconstruction.

#### 4.9 Report Contracts

Status: **Not Started**

Implementation:

- Update `src/fin_automation/models/common.py`.
- Create `src/fin_automation/models/reports.py`.
- Create `tests/test_models/test_reports.py`.

Contracts:

- `ReportDraft`
- `ReportArtifact`
- `WorkflowArtifact`

Shared enums:

- `ReportType`
- `ArtifactType`
- `ArtifactStatus`

Required validation includes:

- Nonempty report titles.
- Nonempty Markdown report content.
- A valid validation-result reference.
- Approved candidate-analysis references.
- Approved source references.
- Approved evidence references.
- Approved calculation references.
- Unique record identifiers.
- A recommendation outcome consistent with the validation result.
- No preferred candidate for insufficient-evidence reports.
- Required risk and limitation sections.
- Required human-review language.
- Predictable output file names.
- Output paths restricted to the approved output directory.
- Required report artifacts for completed workflow artifacts.
- Timezone-aware creation timestamps.
- JSON serialization and reconstruction.

#### 4.10 Workflow Contracts

Status: **Completed**

Implementation:

- Update `src/fin_automation/models/common.py`.
- Create `src/fin_automation/models/workflow.py`.
- Create `tests/test_models/test_workflow.py`.

Contracts:

- `WorkflowError`
- `StageResult`
- `WorkflowState`

Shared enums:

- `WorkflowStatus`
- `StageStatus`
- `ErrorSeverity`
- Additional `WorkflowStage` values when required

Required validation includes:

- Nonnegative retry counters.
- Attempt numbers beginning at one.
- Unique record identifiers.
- A start timestamp for every stage result.
- A completion timestamp for completed stages.
- Error details for failed stages.
- No error details for successful stages.
- Completion timestamps that do not precede start timestamps.
- Matching workflow identifiers across nested records.
- A valid current workflow stage.
- A completion timestamp for completed workflows.
- No completion timestamp for workflows that have not completed.
- Final report-artifact references for completed workflows.
- Structured workflow errors for failed workflows.
- Timezone-aware workflow timestamps.
- JSON serialization and reconstruction.

### Implementation Process

Each Phase 4 implementation unit shall follow this process:

1. Review the corresponding section of `specs/data-contracts.md`.
2. Identify the required enums and dependent models.
3. Implement one bounded model group.
4. Add tests for its application-specific validation rules.
5. Run the focused test file.
6. Run the complete test suite.
7. Review the Git changes.
8. Commit the completed unit.
9. Update the implementation-unit status in this roadmap.

Focused tests shall be run using the corresponding test file.

For example:

```bash
python -m pytest tests/test_models/test_validation.py -v
```

The complete test suite shall then be run:

```bash
python -m pytest -v
```

Git changes shall be reviewed before committing:

```bash
git status
git --no-pager diff --cached --stat
```

### Scope Boundary

Phase 4 implements project foundations and data contracts only.

Phase 4 includes:

- Python project configuration.
- Environment-variable validation.
- Custom exception definitions.
- Logging configuration.
- Shared enumerations.
- Pydantic data models.
- Field-level validation.
- Cross-field validation.
- Nested-model validation.
- JSON serialization and reconstruction tests.

Phase 4 does not implement:

- Agent prompts.
- Agent execution.
- OpenAI requests.
- Tavily searches.
- Source-selection logic.
- Webpage retrieval.
- HTML parsing.
- Evidence-extraction logic.
- Financial-calculation functions.
- Candidate-analysis logic.
- Recommendation-generation logic.
- Evidence-validation logic.
- Report-generation logic.
- Markdown or JSON file-writing logic.
- Workflow orchestration.

Those behaviors begin in Phases 5 through 9.

### Exit Criteria

Phase 4 is complete when:

- The application runs in the approved Python virtual environment.
- Required dependencies install from `requirements.txt`.
- The project can be installed in editable mode.
- `.env` is excluded from version control.
- `.venv` is excluded from version control.
- Python bytecode caches are excluded from version control.
- Pytest caches are excluded from version control.
- Generated package metadata is excluded from version control.
- The source package imports successfully.
- Application configuration is validated.
- Secret values are protected from accidental display.
- Logging is configured without exposing secret values.
- Custom application exceptions are defined.
- Intake contracts are implemented and tested.
- Research-planning contracts are implemented and tested.
- Source and evidence contracts are implemented and tested.
- Financial contracts are implemented and tested.
- Validation contracts are implemented and tested.
- Report contracts are implemented and tested.
- Workflow contracts are implemented and tested.
- All approved Phase 4 Pydantic contracts are implemented.
- Required and optional fields match `specs/data-contracts.md`.
- Shared enums contain the approved values.
- Required text fields reject blank values.
- Unknown fields are rejected where required.
- Duplicate identifiers are rejected where required.
- Nested records use matching workflow identifiers.
- Invalid status and field combinations fail validation.
- Cross-field validation rules have automated tests.
- Time-related records require timezone-aware timestamps.
- Models serialize to JSON successfully.
- Serialized models can be reconstructed successfully.
- Reconstructed models match their original model instances.
- Focused tests for every implementation unit pass.
- The complete test suite passes.
- Phase 4 changes are committed to Git.
- The working tree is clean after the final Phase 4 commit.
- The roadmap is updated to mark Phase 4 as completed.

### Phase 4 Completion Verification

Before Phase 4 is marked complete, run:

```bash
python -m pytest -v
```

Verify the package can be imported:

```bash
python - <<'PY'
from fin_automation.config import get_settings
from fin_automation.models.financial import RecommendationResult
from fin_automation.models.intake import IntakeResult
from fin_automation.models.reports import ReportDraft
from fin_automation.models.research import ResearchPlan
from fin_automation.models.sources import ExtractedEvidence
from fin_automation.models.validation import ValidationResult
from fin_automation.models.workflow import WorkflowState

print("Phase 4 modules imported successfully.")
PY
```

Verify the Git working tree:

```bash
git status
```

The expected final Git status is:

```text
nothing to commit, working tree clean
```

### Dependencies

Phase 4 depends on completion of Phase 3.

Phase 5 shall not be marked complete until the Phase 4 contracts required
by its web-research components have been implemented and tested.


## Phase 5: Web Research Vertical Slice

### Status

In Progress

### Goal

Implement the first complete application slice from validated intake through
research planning, web search, source selection, retrieval, parsing, and
validated evidence extraction.

Phase 5 is divided into three bounded implementation units:

```text
Phase 5A: Research Planning
Phase 5B: Search, Source Selection, and Retrieval
Phase 5C: Parsing and Evidence Extraction
```

Each unit shall be implemented, tested, reviewed, and committed before the
next unit begins.

---

## Phase 5A: Research Planning

### Status

Completed

### Goal

Implement the Research Planning Agent behavior that converts a validated
`IntakeResult` into a validated `ResearchPlan`.

Phase 4 defined the research-planning data contracts. Phase 5A implements
the behavior that creates records conforming to those contracts.

### Inputs

- `IntakeResult`
- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`

### Outputs

- `EvidenceRequirement`
- `SearchQuery`
- `ResearchPlan`
- `AdditionalResearchRequest`, when later research gaps require another
  bounded planning pass

### Planned Deliverables

- Research Planning Agent instructions.
- Structured-output configuration for `ResearchPlan`.
- Intake-to-research-plan conversion.
- Evidence-requirement generation.
- Search-query generation.
- Candidate-discovery planning.
- Candidate-specific research planning.
- Comparison-criteria planning.
- Risk-category planning.
- Source-category preference planning.
- Clarification and insufficient-input handling.
- Research-plan validation tests.
- Mocked model-response tests.
- Prompt-alignment tests.

### Planned Workflow

1. Receive a validated `IntakeResult`.
2. Confirm that intake does not require clarification.
3. Read the approved research request.
4. Read the investor profile.
5. Read the research scope.
6. Determine whether candidate discovery is required.
7. Define the research objective.
8. Define comparison criteria.
9. Define risk categories.
10. Create evidence requirements.
11. Create approved search queries.
12. Associate each query with one or more evidence requirements.
13. Apply candidate and source limits.
14. Produce a validated `ResearchPlan`.
15. Return the plan to the deterministic workflow orchestrator.

### Scope Boundary

Phase 5A includes:

- Interpretation of validated intake.
- Research-objective generation.
- Evidence-requirement generation.
- Search-query generation.
- Research-plan construction.
- Structured-output validation.

Phase 5A does not include:

- Tavily API calls.
- Live web searches.
- Source selection.
- URL retrieval.
- HTML parsing.
- Evidence extraction.
- Financial calculations.
- Candidate recommendations.

### Exit Criteria

Phase 5A is complete when:

- A complete `IntakeResult` can produce a validated `ResearchPlan`.
- Intake requiring clarification does not proceed to research planning.
- The plan includes at least one comparison criterion.
- The plan includes at least one evidence requirement.
- The plan includes at least one approved search query.
- Search queries reference valid evidence requirements.
- Candidate limits remain within the approved scope.
- Source limits remain within the approved scope.
- Candidate discovery is represented explicitly.
- Named-candidate research is represented explicitly.
- Risk categories are included when required.
- Unsupported source categories are not preferred.
- Model-generated output is validated before workflow continuation.
- Invalid structured output is rejected or corrected.
- Research-planning tests pass.
- The complete test suite passes.

---

## Phase 5B: Search and Source Selection

### Status

Completed

### Objective

Convert a validated `ResearchPlan` into a validated
`SourceSelection` containing relevant public sources and extracted
source content for downstream financial analysis.

### Implemented Workflow

1. Receive a validated `ResearchPlan`.
2. Read the approved `SearchQuery` records.
3. Provide the complete research plan to the Source Selection Agent.
4. Allow the agent to invoke the Tavily search tool using only approved
   query text, query identifiers, and workflow identifiers.
5. Execute each selected query through the Tavily Search API.
6. Request search-result metadata and extracted source content using
   `include_raw_content=True`.
7. Convert Tavily responses into validated `SearchResult` records.
8. Store complete `SearchResult` records inside the Tavily search tool
   for the duration of the source-selection run.
9. Return lightweight search-result metadata to the agent to avoid
   placing complete webpage content in the agent context.
10. Allow the Source Selection Agent to evaluate result relevance,
    source category, candidate association, and evidence coverage.
11. Require the agent to associate selected results with approved
    evidence requirements.
12. Require the agent to record selection reasons and exclusion reasons.
13. Require the agent to determine whether the available results are
    ready for downstream analysis, require additional search, or are
    insufficient.
14. Submit the source-selection decision through a structured
    `SubmitSourceSelectionTool`.
15. Remove application-generated identifiers and timestamps from the
    submitted payload so Python and Pydantic generate them.
16. Hydrate each submitted decision by looking up its original
    `SearchResult` using `search_result_id`.
17. Attach the original title, URL, domain, and raw source content to
    each `SelectedSource`.
18. Validate the completed payload as a `SourceSelection`.
19. Validate workflow, plan, candidate, and evidence-requirement
    references.
20. Return selected source content for Phase 5C financial analysis and
    evidence extraction.

### Implemented Components

- `prompts/source_selection.py`
  - Defines Source Selection Agent instructions.
  - Serializes the complete `ResearchPlan`.
  - Enforces approved-query usage.
  - Defines structured search and submission behavior.

- `tools/tavily_search.py`
  - Implements the Tavily search capability as a `smolagents` tool.
  - Executes approved search queries.
  - Requests extracted source content.
  - Maps provider responses into validated `SearchResult` records.
  - Applies a maximum raw-content character limit.
  - Stores complete search results by `search_result_id`.
  - Returns lightweight result metadata to the agent.

- `agents/source_selection.py`
  - Implements the Source Selection Agent using
    `smolagents.ToolCallingAgent`.
  - Provides the Tavily search and structured submission tools.
  - Coordinates search, selection, and final validation.
  - Verifies workflow, plan, candidate, status, and evidence references.

- `tools/source_selection_submission.py`
  - Accepts the agent's structured source-selection decision.
  - Removes identifiers and timestamps generated by the application.
  - Hydrates source decisions from stored `SearchResult` records.
  - Attaches original source metadata and raw content.
  - Validates and stores the final `SourceSelection`.

- `models/sources.py`
  - Stores extracted content on `SearchResult.raw_content`.
  - Stores selected source metadata and content on `SelectedSource`.
  - Preserves `search_result_id` for lineage.

- `scripts/smoke_test_source_selection.py`
  - Performs a live Source Selection Agent smoke test.
  - Confirms Tavily tool invocation.
  - Confirms source-selection submission.
  - Confirms source metadata and raw content are preserved.

### Validation Completed

The live smoke test confirmed:

- The Source Selection Agent received a validated `ResearchPlan`.
- The agent invoked the Tavily search tool.
- Tavily returned relevant public search results.
- Extracted raw content was returned for the selected sources.
- Search results were converted into validated `SearchResult` records.
- The agent selected relevant primary sources.
- Selected sources were linked to the intended candidate.
- The submission tool accepted a structured source-selection decision.
- Source decisions were hydrated from stored search results.
- Each selected source retained its title, URL, domain, and raw content.
- The final result was validated as a `SourceSelection`.
- Selected source content is available for Phase 5C.

### Intentional Scope Decisions

The following features were intentionally excluded to keep the
capstone focused on demonstrating agentic AI orchestration:

- Deterministic duplicate-URL detection.
- URL canonicalization and tracking-parameter removal.
- A separate Requests-based webpage-retrieval pipeline.
- Redirect-chain tracking.
- HTTP-status and content-type recording.
- A separate Tavily Extract API call.
- A persistent search-result database.
- Permanent storage of intermediate source-selection artifacts.

Instead, Phase 5B uses Tavily search with `include_raw_content=True` to
retrieve search metadata and extracted source content in one bounded
tool call.

### Data Handoff to Phase 5C

Phase 5C receives a validated `SourceSelection`.

Each selected `SelectedSource` may contain:

- `search_result_id`
- `title`
- `url`
- `domain`
- `candidate_name`
- `expected_source_category`
- `selection_reason`
- `evidence_requirement_ids`
- `raw_content`

The raw content is currently stored in the returned Python object for
the duration of the workflow. Permanent artifact storage will be
addressed only if required when the full orchestrated workflow is
assembled.

### Exit Criteria

- [x] A validated `ResearchPlan` can initiate source selection.
- [x] The agent can invoke Tavily using approved search queries.
- [x] Tavily responses are converted into `SearchResult` records.
- [x] Search results retain query and workflow lineage.
- [x] The Source Selection Agent can select and exclude results.
- [x] Selected results reference approved evidence requirements.
- [x] Selection and exclusion reasons are recorded.
- [x] Additional-research outcomes are supported.
- [x] The agent submits its decision through a structured tool.
- [x] Python hydrates selected records from original search results.
- [x] Selected records retain URLs and extracted source content.
- [x] The final output is validated as `SourceSelection`.
- [x] Selected source content is ready for Phase 5C.
## Phase 5C: Parsing and Evidence Extraction

### Status

Not Started

### Goal

Parse successfully retrieved HTML, preserve available source metadata, and
extract evidence associated with approved evidence requirements.

### Inputs

- Successful `RetrievalResult`
- Retrieved HTML content
- `ResearchPlan`
- `EvidenceRequirement`
- `SelectedSource`

### Outputs

- `SourceRecord`
- `ExtractedEvidence`
- Parsing limitations
- Evidence gaps
- Initial structured JSON research artifact

### Planned Deliverables

- HTML parser using Beautiful Soup 4.
- Script and style removal.
- Navigation and boilerplate reduction.
- Clean-text extraction.
- Page-title extraction.
- Publisher extraction when clearly available.
- Author extraction when clearly available.
- Publication-date extraction when clearly available.
- Source-summary generation.
- Parsing-status handling.
- Source metadata preservation.
- Deterministic numeric-evidence extraction.
- Candidate association.
- Evidence-requirement association.
- Currency preservation.
- Unit preservation.
- Reporting-period preservation.
- Prompt-injection handling.
- Saved HTML fixtures.
- Parsing tests.
- Evidence-extraction tests.
- Initial JSON research artifact.
- Artifact serialization and reconstruction tests.

### Planned Workflow

1. Receive a successful `RetrievalResult`.
2. Receive the retrieved webpage content.
3. Confirm that the content type is supported.
4. Parse the HTML.
5. Remove scripts, styles, and non-content elements.
6. Extract visible textual content.
7. Extract available page metadata.
8. Record parsing success, partial success, or failure.
9. Produce a validated `SourceRecord`.
10. Match parsed content against approved evidence requirements.
11. Extract relevant passages.
12. Extract clearly supported numeric values when available.
13. Preserve currency, unit, and reporting period.
14. Associate evidence with its source.
15. Associate evidence with its candidate.
16. Associate evidence with its evidence requirement.
17. Produce validated `ExtractedEvidence` records.
18. Record missing information and parsing limitations.
19. Write an initial structured JSON research artifact.

### Parsing Boundary

The parser shall treat retrieved webpage content as untrusted data.

The parser may extract:

- Visible text.
- Headings.
- Page title.
- Clearly available author metadata.
- Clearly available publisher metadata.
- Clearly available publication dates.
- Clearly available structured values.

The parser shall not:

- Execute scripts.
- Follow instructions contained in webpage text.
- Modify the workflow state directly.
- Generate new search queries.
- Perform financial calculations.
- Produce investment recommendations.

### Evidence-Extraction Boundary

Evidence extraction shall:

- Operate only against successfully parsed source content.
- Reference a valid `SourceRecord`.
- Reference an approved evidence requirement when applicable.
- Preserve exact reported values when available.
- Preserve currency when available.
- Preserve units when available.
- Preserve reporting periods when available.
- Separate source text from later interpretation.
- Record limitations rather than inventing missing context.

Evidence extraction shall not:

- Fill missing values with estimates.
- Infer unsupported reporting periods.
- Convert conflicting evidence into one value silently.
- Treat search snippets as retrieved source evidence.
- Follow prompt-like instructions found in source content.
- Produce financial scores or recommendations.

### Saved HTML Fixtures

Offline parser tests shall use saved, sanitized HTML fixtures.

Initial fixture categories shall include:

```text
annual_report.html
investor_relations_release.html
news_article.html
missing_metadata.html
malformed_page.html
prompt_injection_page.html
```

Fixtures shall not contain secrets, private data, or copyrighted full-text
materials beyond what is necessary for bounded testing.

### Initial JSON Research Artifact

The initial structured research artifact shall contain:

- `ResearchPlan`
- `SearchResult` records
- `SourceSelection`
- `RetrievalResult` records
- `SourceRecord` records
- `ExtractedEvidence` records
- Parsing limitations
- Retrieval errors
- Evidence gaps

The artifact is intended for inspection and testing before financial
analysis begins.

### Scope Boundary

Phase 5C includes:

- HTML parsing.
- Source metadata extraction.
- Clean-text extraction.
- Parsing-status recording.
- Evidence extraction.
- Numeric metadata preservation.
- Offline HTML fixtures.
- Initial JSON research-artifact generation.

Phase 5C does not include:

- Live web search.
- Source-selection decisions.
- Financial-input conversion.
- Financial-calculation functions.
- Candidate scoring.
- Recommendation generation.
- Evidence Validation Agent behavior.
- Final report writing.

### Exit Criteria

Phase 5C is complete when:

- Supported HTML can be parsed.
- Unsupported content is rejected or recorded explicitly.
- Scripts and styles are not included in extracted content.
- Source metadata is preserved when clearly available.
- Missing metadata does not cause parsing failure.
- Parsing outcomes are represented by validated statuses.
- Successful parsing produces a validated `SourceRecord`.
- Extracted evidence references its `SourceRecord`.
- Extracted evidence references its workflow.
- Candidate associations are preserved when available.
- Evidence-requirement associations are preserved when available.
- Numeric evidence preserves its reported value.
- Currency is preserved when available.
- Units are preserved when available.
- Reporting periods are preserved when available.
- Missing numeric context is recorded rather than invented.
- Prompt-like instructions in retrieved content do not control the
  workflow.
- Saved fixtures support offline parser testing.
- The initial JSON research artifact can be serialized.
- The initial JSON research artifact can be reconstructed.
- Parsing and evidence-extraction tests pass.
- The complete test suite passes.

---

## Phase 5 Completion Criteria

Phase 5 is complete only when Phase 5A, Phase 5B, and Phase 5C are all
marked completed.

Phase 5 is complete when:

- A validated `IntakeResult` can produce a validated `ResearchPlan`.
- Approved search queries can be executed through Tavily.
- Search responses are converted into validated `SearchResult` records.
- The Source Selection Agent produces a validated `SourceSelection`.
- Selected public webpages can be retrieved.
- Retrieval outcomes are represented by validated `RetrievalResult`
  records.
- Supported HTML can be parsed into validated `SourceRecord` records.
- Extracted evidence references its source and evidence requirement.
- Search, retrieval, parsing, and extraction remain separate operations.
- External content cannot control the workflow.
- Network-dependent tests are separated from offline tests.
- Saved fixtures support repeatable offline testing.
- The initial structured research artifact can be written and reopened.
- Focused tests for Phase 5A pass.
- Focused tests for Phase 5B pass.
- Focused tests for Phase 5C pass.
- The complete test suite passes.
- Phase 5 changes are committed to Git.
- The roadmap is updated to mark Phase 5 completed.

### Implementation Process

Each Phase 5 unit shall follow this process:

1. Review the applicable specifications and Phase 4 contracts.
2. Implement one bounded behavior group.
3. Use dependency injection for external clients.
4. Add focused unit tests.
5. Use mocked external responses in the default test suite.
6. Run the focused test file.
7. Run the complete test suite.
8. Review Git changes.
9. Commit the completed unit.
10. Update the unit status in this roadmap.

### Dependencies

Phase 5 depends on completion of Phase 4.

Phase 5B depends on completion of Phase 5A.

Phase 5C depends on completion of Phase 5B.

---
## Phase 6: Financial Analysis and Recommendation Logic

### Status

Not Started

### Goal

Implement deterministic financial calculations and the Financial Analysis
Agent using the approved recommendation methodology.

### Planned Deliverables

- Financial-input validation.
- Revenue-Growth Calculator.
- Profit-Margin Calculator.
- Debt-to-Equity Calculator.
- Price-to-Earnings Calculator.
- Weighted-Score Calculator.
- Evidence-Lookup Tool.
- Financial Analysis Agent.
- `CategoryEvaluation` implementation.
- `CandidateAnalysis` implementation.
- `RecommendationResult` implementation.
- Calculation and analysis tests.

### Initial Analysis Areas

The initial analysis will cover:

- Revenue growth.
- Net or operating profit margin.
- Debt-to-equity.
- Price-to-earnings when applicable.
- Competitive position when supported by evidence.
- Material candidate risks.
- Investor-profile alignment.
- Weighted candidate comparison when supported.

Currency, reporting-period, and unit differences must be preserved and
qualified.

The initial implementation will prefer ratios and percentage-based
comparisons when candidates report absolute values in different currencies.

### Excluded Initial Calculations

The initial implementation will not include:

- Discounted cash-flow valuation.
- Monte Carlo simulation.
- Historical volatility.
- Maximum drawdown.
- Technical-analysis indicators.
- Automated sentiment scoring.
- Portfolio optimization.
- Advanced currency conversion.
- Real-time market monitoring.

### Exit Criteria

Phase 6 is complete when:

- Financial inputs are validated before calculation.
- Calculation formulas are documented.
- Calculations use deterministic Python functions.
- The same valid input produces the same result.
- Missing and non-applicable values are distinguished.
- P/E returns a non-applicable result for zero or negative earnings.
- Calculation records preserve their input lineage.
- Candidate analyses contain favorable and unfavorable evidence.
- Candidate rankings can be explained.
- The system can produce an insufficient-evidence outcome.
- Recommendations remain subject to evidence validation and human review.
- Calculation and Financial Analysis Agent tests pass.

### Dependencies

Phase 6 depends on completion of Phases 4 and 5.

---

## Phase 7: Evidence Validation and Safety

### Status

Not Started

### Goal

Ensure that preliminary conclusions are supported, traceable, responsive to
the original request, and compliant with the project boundaries.

### Planned Deliverables

- Evidence Validation Agent.
- Evidence-Lookup Tool support for validation.
- Citation-Reference Checker.
- Deterministic identifier checks.
- `ValidationFinding` implementation.
- `ValidationResult` implementation.
- Correction-routing behavior.
- Prompt-injection test fixtures.
- Validation and adversarial tests.

### Planned Validation Areas

The validation stage will check:

- Material claim support.
- Source and evidence identifiers.
- Citation relevance.
- Calculation lineage.
- Candidate and reporting-period compatibility.
- Missing and conflicting information.
- Favorable and unfavorable evidence coverage.
- Material risk disclosure.
- Recommendation confidence.
- Original-prompt alignment.
- Investor-profile alignment.
- Human-review boundaries.
- Guaranteed-return and trade-instruction language.
- Duplicate or derivative-source confidence inflation.

### Validation Outcomes

The validation stage will support:

- `approved`
- `analysis_correction_required`
- `additional_research_required`
- `insufficient_evidence`
- `rejected`

### Exit Criteria

Phase 7 is complete when:

- Unsupported claims fail validation.
- Unknown source and evidence identifiers fail validation.
- Unrelated citations fail validation.
- Missing and conflicting evidence is disclosed.
- Calculation-input problems are identified.
- Recommendation confidence reflects evidence quality.
- Risks cannot be removed solely because they weaken a candidate.
- A forced ranking can be rejected.
- Scraped prompt-injection content does not control agent behavior.
- Validation failures route to the correct component.
- Failed validation prevents an invalid final report.
- Validation and adversarial tests pass.

### Dependencies

Phase 7 depends on completion of Phases 5 and 6.

---

## Phase 8: Report and Artifact Generation

### Status

Not Started

### Goal

Generate readable, cited, and traceable Markdown and JSON outputs from
approved workflow data.

### Planned Deliverables

- Report Writing Agent.
- Approved report template.
- Citation-formatting support.
- `ReportDraft` implementation.
- Deterministic report-structure validation.
- Markdown file writer.
- JSON workflow-artifact writer.
- Example research report.
- Example insufficient-evidence report.
- Report and file-output tests.

### Required Report Content

The final report will include:

- Research question.
- Investor profile.
- Research scope.
- Research methodology.
- Candidate analyses.
- Candidate comparison.
- Approved recommendation outcome.
- Material calculations.
- Supporting and opposing evidence.
- Material risks.
- Missing or conflicting information.
- Limitations.
- Recommendation confidence.
- Human-review statement.
- Sources and citations.

### Exit Criteria

Phase 8 is complete when:

- Approved workflow data can be converted into a `ReportDraft`.
- The report writer cannot introduce unapproved facts.
- Markdown reports can be written to the configured output directory.
- Structured workflow results can be written as JSON.
- Material claims include traceable citations.
- Risks and limitations are included.
- Missing and conflicting evidence is disclosed.
- Facts, calculations, interpretations, and recommendations remain
  distinguishable.
- An insufficient-evidence outcome produces a limitation report without a
  preferred candidate.
- Output paths remain inside the approved output directory.
- Report and file-output tests pass.

### Dependencies

Phase 8 depends on completion of Phase 7.

---

## Phase 9: Complete Workflow Integration

### Status

Not Started

### Goal

Connect all agents, deterministic tools, Pydantic contracts, validation
gates, correction paths, and output writers through the Python
orchestrator.

### Planned Deliverables

- Complete orchestrator implementation.
- `WorkflowState` implementation.
- Stage-result tracking.
- Agent and tool assignments.
- Intake clarification behavior.
- Research retry behavior.
- Analysis correction behavior.
- Validation routing.
- Final artifact handling.
- Integration tests.
- Example end-to-end execution.

### Planned Workflow

1. Receive the natural-language request.
2. Interpret and validate intake data.
3. Request clarification when required.
4. Create the research plan.
5. Execute web searches.
6. Select candidate sources.
7. Retrieve and parse selected webpages.
8. Create structured source and evidence records.
9. Perform deterministic financial calculations.
10. Analyze and compare candidates.
11. Produce a preliminary recommendation.
12. Validate evidence and recommendation support.
13. Route corrections when required.
14. Generate the approved report.
15. Validate the report structure.
16. Write Markdown and JSON artifacts.
17. Return the result for human review.

### Exit Criteria

Phase 9 is complete when:

- The orchestrator controls the complete workflow order.
- Agents receive only approved tools.
- All major stage outputs conform to Pydantic contracts.
- Failed required stages prevent invalid downstream processing.
- Required clarification stops research until resolved.
- Recoverable failures use bounded correction paths.
- Unrecoverable failures produce structured errors.
- Only validated results proceed to report generation.
- A complete research request produces Markdown and JSON artifacts.
- The workflow does not execute any financial transaction.
- Integration tests pass.

### Dependencies

Phase 9 depends on completion of Phases 5 through 8.

---

## Phase 10: Testing and Quality Verification

### Status

Not Started

### Goal

Verify that the integrated system satisfies its specifications, handles
expected failures, and resists adversarial inputs.

### Planned Deliverables

- Complete unit-test suite.
- Complete happy-path suite.
- Complete failure-path suite.
- Complete adversarial suite.
- End-to-end tests.
- Requirement-to-test traceability mapping.
- Test-results artifact.
- Defect corrections.
- Final acceptance review.

### Planned Happy-Path Coverage

Tests will verify that:

- A valid request is interpreted.
- Required intake values are validated.
- A research plan is created.
- Web search returns structured results.
- Sources are selected and retrieved.
- Webpages are parsed into evidence records.
- Financial calculations produce expected results.
- Candidates are compared.
- Evidence validation approves a supported result.
- A Markdown report is written.
- A JSON workflow artifact is written.

### Planned Adversarial Coverage

Tests will verify behavior when:

- Investor-profile information is missing.
- Search returns no relevant results.
- A webpage cannot be retrieved.
- Webpage content is malformed.
- Scraped content contains prompt injection.
- A source identifier is fabricated.
- A citation does not support its claim.
- Sources materially conflict.
- Financial values use incompatible periods or units.
- A financial value is missing or invalid.
- P/E is not applicable.
- Duplicate sources attempt to inflate confidence.
- A recommendation guarantees returns.
- A recommendation removes material risks.
- The Report Writing Agent introduces unsupported facts.
- An external service returns invalid structured output.
- A file path attempts to escape the output directory.
- File writing fails.

### Exit Criteria

Phase 10 is complete when:

- Required unit tests pass.
- Happy-path tests pass.
- Failure-path tests pass.
- Adversarial tests pass.
- Major requirements map to tests or acceptance checks.
- External dependencies are mocked appropriately.
- Saved fixtures support repeatable scraping tests.
- No known failure allows an unsupported recommendation to be approved.
- Test results are preserved as a project artifact.

### Dependencies

Phase 10 depends on completion of Phase 9.

---

## Phase 11: Documentation and Submission Preparation

### Status

Not Started

### Goal

Complete required capstone artifacts, verify repository integrity, and
prepare the project for evaluation.

### Planned Deliverables

- Completed `README.md`.
- Completed constitution.
- Completed specifications.
- Final architecture documentation.
- Final Mermaid source and PNG diagram.
- Happy-path and adversarial tests.
- Prompt and decision journal.
- `COPILOT.md`.
- Example research report.
- Example insufficient-evidence report.
- Structured JSON workflow artifact.
- Test-results artifact.
- Final repository review.
- Submission-ready project repository or archive.

### README Completion Areas

The final README will include:

- Project overview.
- Problem statement.
- Intended users.
- Core capabilities.
- System boundaries.
- Architecture summary.
- Repository structure.
- Installation instructions.
- Configuration instructions.
- Usage instructions.
- Testing instructions.
- Example input.
- Example output.
- Safety and limitations.
- Specification links.
- Required-artifact checklist.

### AI-Assistance Documentation

The project will preserve selected examples showing:

- How AI assistance was used during specification.
- How agent boundaries were selected.
- Which suggestions were accepted.
- Which suggestions were challenged or rejected.
- Why deterministic tools were separated from agents.
- Why the architecture diagram was simplified.
- How generated code was reviewed and tested.
- How the human developer retained final authority.

### Exit Criteria

Phase 11 is complete when:

- Every required capstone artifact is present.
- README instructions match the implementation.
- The architecture diagram matches the implemented high-level workflow.
- Specifications match implemented behavior.
- Test instructions work in a clean environment.
- Example outputs contain citations, risks, limitations, and human-review
  language.
- Secret credentials are absent.
- Virtual environments, caches, and temporary files are excluded.
- Required files are committed to version control.
- The repository can be reviewed without undocumented context.
- The final submission contains current files.

### Dependencies

Phase 11 depends on completion of Phase 10.

---

## Deferred Work

The following capabilities are deferred from the initial capstone version:

- Continuous market monitoring.
- Real-time market alerts.
- Brokerage-account integration.
- Automated trading.
- Portfolio rebalancing.
- User authentication.
- Persistent user accounts.
- Production database storage.
- Vector database storage.
- Production web interface.
- Mobile application.
- Cloud deployment.
- Container orchestration.
- Paid financial-data platform integration.
- Automated currency conversion.
- Automated market-sentiment scoring.
- Discounted cash-flow valuation.
- Monte Carlo simulation.
- Historical-volatility calculation.
- Maximum-drawdown calculation.
- Technical-analysis indicators.
- Portfolio optimization.
- Tax recommendation features.
- Legal recommendation features.
- Support for every financial instrument.

Deferred capabilities shall not be implemented unless the specifications,
technology stack, and roadmap are intentionally revised.

## Out-of-Scope Behavior

The project will not:

- Execute financial transactions.
- Access brokerage accounts.
- Transfer or control funds.
- Automatically manage a portfolio.
- Guarantee financial returns.
- Claim that an investment is risk-free.
- Hide missing or conflicting evidence.
- Fabricate sources, citations, or financial data.
- Make the final investment decision for the user.

## Phase Dependencies

The general dependency order is:

1. Project foundation establishes mission and technical boundaries.
2. Detailed specifications define expected behavior.
3. Data contracts and architecture define component interactions.
4. Project setup creates the implementation foundation.
5. Web research proves external research and scraping capabilities.
6. Financial analysis adds calculations and candidate comparisons.
7. Evidence validation verifies research quality and safety.
8. Report generation produces the required output artifacts.
9. Workflow integration connects all components.
10. Quality verification confirms specification compliance.
11. Submission preparation completes and verifies the deliverable.

A later phase may begin early for exploration, but it shall not be marked
complete until its dependencies and exit criteria are satisfied.

## Roadmap Maintenance

This roadmap may be updated when:

- A phase is completed.
- A phase becomes blocked.
- A phase must be divided or combined.
- A validated requirement changes.
- Implementation reveals a missing requirement.
- Testing identifies missing work.
- A technical discovery changes the implementation sequence.
- A planned feature is deferred.
- A new requirement is formally approved.
- A technology change affects the development plan.

Roadmap updates shall follow these rules:

1. Changes must remain consistent with the project mission.
2. Technology changes must update `tech-stack.md`.
3. Behavioral changes must update the relevant specification.
4. Data-handoff changes must update `data-contracts.md`.
5. Agent-responsibility changes must update `agent-workflows.md`.
6. Architecture changes must update the Mermaid source and PNG.
7. Completed phases shall remain visible.
8. Deferred work shall be recorded rather than silently removed.
9. Small implementation tasks shall not be added to this roadmap.

## Change Log

| Revision | Phase | Change | Reason |
|---|---|---|---|
| 0.1 | All | Established the initial project trajectory and development phases. | Initial planning. |
| 0.2 | Phases 1 and 2 | Completed the project constitution and began detailed specification work. | Phase 1 deliverables and exit criteria were satisfied. |
| 0.3 | Phases 2 and 3 | Completed detailed specifications and began data-contract and architecture design. | Phase 2 deliverables and exit criteria were satisfied. |
| 0.4 | Phases 3 and 4 | Completed data contracts, agent workflows, architecture documentation, and the architecture diagram. Began project setup and Pydantic implementation. | Phase 3 deliverables and exit criteria were satisfied. |
| 0.5 | Phases 5 through 8 | Refined future implementation phases to match the approved five-agent architecture and reduced financial tool set. | Phase 3 clarified the actual component boundaries, contracts, tools, and outputs. |

## Next Planned Work

The active phase is:

```text
Phase 4: Project Structure and Development Environment
```

The first implementation work will be:

1. Create the approved repository directories.
2. Create `requirements.txt`.
3. Create `.env.example`.
4. Create `.gitignore`.
5. Create the Python source package.
6. Implement shared enums and intake Pydantic models.
7. Write and run the initial model tests.