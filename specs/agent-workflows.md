# Agent Workflows

## Purpose

This document defines the responsibilities, inputs, tools, outputs, stopping
conditions, and scope boundaries of the agents used in Agentic Financial
Analysis Automation.

Each agent owns one coherent decision-making objective and produces a
validated output for the next workflow stage.

Deterministic operations such as workflow routing, HTTP retrieval, HTML
parsing, financial arithmetic, schema validation, file writing, and retry
enforcement are controlled by Python code rather than language-model
reasoning.

## Agent Summary

| Agent | Objective | Primary Output |
|---|---|---|
| Research Planning Agent | Interpret the request and define the research plan | `IntakeResult` and `ResearchPlan` |
| Source Selection Agent | Select relevant search results for retrieval | `SourceSelection` |
| Financial Analysis Agent | Compare candidates and produce a preliminary conclusion | `CandidateAnalysis` and `RecommendationResult` |
| Evidence Validation Agent | Determine whether the preliminary conclusion is defensible | `ValidationResult` |
| Report Writing Agent | Communicate the approved conclusion | `ReportDraft` |

## Deterministic Python Orchestrator

### Objective

Control the workflow order, preserve workflow state, validate stage
outputs, route correction requests, enforce retry limits, and prevent
invalid downstream processing.

The orchestrator does not interpret financial evidence or generate
investment recommendations.

### Responsibilities

The orchestrator shall:

- Receive and preserve the original user prompt.
- Invoke the Research Planning Agent in intake mode.
- Validate the returned `IntakeResult`.
- Stop for clarification when required information is missing.
- Invoke the Research Planning Agent in planning mode.
- Execute the approved workflow stages in order.
- Validate structured outputs before passing them to dependent stages.
- Maintain the current `WorkflowState`.
- Route additional-research requests to the appropriate stage.
- Route analysis corrections to the Financial Analysis Agent.
- Enforce configured search, correction, and retry limits.
- Prevent failed required stages from producing an approved final report.
- Invoke deterministic file writers after report validation.
- Return the final workflow result to the user.

### Workflow Order

The primary workflow order is:

1. Request intake.
2. Intake validation.
3. Clarification when required.
4. Research planning.
5. Web search and source selection (Tavily returns each result's raw
   page content in the same search response — see
   `constitution/techstack.md`).
6. Evidence extraction.
7. Financial analysis and calculations.
8. Evidence validation.
9. Report writing.
10. Structural report validation.
11. Markdown file writing.
12. Human review.

### Routing Outcomes

The orchestrator may route:

- Missing intake information to the user for clarification.
- Missing research evidence to the Source Selection Agent.
- Retrieval failures to deterministic retrieval handling.
- Invalid calculation inputs to the financial-calculation stage.
- Unsupported interpretation to the Financial Analysis Agent.
- Approved conclusions to the Report Writing Agent.
- Insufficient-evidence outcomes to limitation-report generation.
- Unrecoverable failures to workflow termination.

### Scope Boundary

The orchestrator does not:

- Infer missing investor preferences.
- Select investment candidates.
- Determine source relevance.
- Interpret financial results.
- Choose a preferred investment.
- Approve evidence through its own reasoning.
- Draft the final report.

The orchestrator coordinates the workflow but does not replace the
specialized agents.


## Research Planning Agent

### Objective

Interpret the user's investment research request and determine what must
be researched. The agent preserves the distinction between information explicitly stated
by the user and assumptions introduced during request interpretation.

### Input Modes

The Research Planning Agent operates in two modes:

1. Intake Interpretation
2. Research Plan Creation

### Intake Interpretation Inputs

- Original natural-language user prompt.
- Optional structured fields supplied directly by the user.
- Supported investment-profile field definitions.
- Supported research-scope field definitions.

### Intake Interpretation Responsibilities

- Preserve the meaning of the original request.
- Extract the primary research question.
- Extract explicitly stated investor preferences.
- Extract explicitly stated scope constraints.
- Identify missing required information.
- Identify assumptions requiring human visibility.
- Avoid inventing unstated investor preferences.
- Produce structured intake data.

### Intake Interpretation Outputs

- `ResearchRequest`
- `InvestorProfile`
- `ResearchScope`
- `IntakeResult`

### Intake Stopping Condition

Intake interpretation ends when the agent has produced a structured
`IntakeResult` for Pydantic validation.

The agent does not decide whether the workflow may proceed. The
orchestrator applies that decision using validated fields such as
`requires_clarification` and `missing_fields`.

### Research Plan Creation Inputs

- Validated `ResearchRequest`
- Validated `InvestorProfile`
- Validated `ResearchScope`

### Research Plan Creation Responsibilities

- Define the research objective.
- Define candidate discovery or comparison criteria.
- Identify relevant financial metrics.
- Identify relevant risk categories.
- Define evidence requirements.
- Generate search queries.
- Identify preferred source types.
- Define the initial research limits.

### Research Plan Creation Output

- `ResearchPlan`

### Final Stopping Condition

The Research Planning Agent's responsibility ends when a validated
`ResearchPlan` has been produced.

The agent does not execute searches, retrieve webpages, analyze
investments, validate report claims, or write the final report.

## Source Selection Agent

### Objective

Discover and select relevant candidate sources that can satisfy the
evidence requirements defined in the approved `ResearchPlan`.

The Source Selection Agent evaluates search results and determines which
pages should proceed to webpage retrieval.

Search results are treated as candidate sources rather than verified
evidence.

### Inputs

The Source Selection Agent receives:

- Validated `ResearchPlan`
- Structured `SearchResult` objects
- Existing `SourceRecord` objects from earlier research passes, when
  available
- Existing evidence-coverage information, when available
- Optional `ValidationResult` requesting additional research

The initial source-selection pass requires:

- Validated `ResearchPlan`
- Structured `SearchResult` objects

### Available Tools

The Source Selection Agent may use:

- Web Search Tool
- Evidence-Lookup Tool

The Web Search Tool executes approved search queries and returns structured
`SearchResult` objects.

The Evidence-Lookup Tool retrieves existing source and evidence records
from the current workflow.

Tavily returns each result's raw page content directly in the same
search call, so there is no separate HTTP-retrieval or HTML-parsing
stage. Duplicate-source avoidance is handled by the Source Selection
Agent's own judgment (its system prompt instructs it not to treat
same-publisher or same-domain results as independent corroboration
without materially distinct reporting) rather than a deterministic
check.

### Responsibilities

The Source Selection Agent shall:

- Use the search queries defined in the `ResearchPlan`.
- Request additional searches when the initial results do not adequately
  cover the research objective.
- Review search results for relevance to the research objective.
- Associate relevant results with candidates and evidence requirements.
- Identify potentially useful primary, secondary, and discovery sources.
- Prefer authoritative and directly relevant sources when reasonably
  available.
- Select the search results that should proceed to webpage retrieval.
- Explain why each selected result appears useful.
- Assign a preliminary source category to each selected result.
- Identify results that may duplicate or derive from another source.
- Identify evidence requirements that remain uncovered.
- Seek both favorable and unfavorable information when both are available.
- Preserve material source disagreement for later analysis and validation.
- Avoid selecting sources solely because they support a preferred
  candidate.
- Determine whether the available search results are sufficient to proceed
  to webpage retrieval.

The preliminary source categories are:

- Primary source.
- Reputable secondary source.
- Discovery or commentary source.
- Unsupported or excluded source.

Source classification remains preliminary until the selected webpage has
been successfully retrieved and parsed.

### Evidence Coverage and Sufficiency

Source sufficiency shall be based on evidence coverage, relevance, source
quality, and source independence rather than a fixed count of agreeing
webpages.

The selected results should provide reasonable coverage of:

- Candidate identification.
- Relevant financial evidence.
- Material risk areas.
- Competitive-position evidence.
- Geographic or currency considerations when relevant.
- Investor-profile alignment requirements.
- Favorable and unfavorable information.

The source-selection process should seek:

- Coverage of material evidence requirements.
- At least one authoritative or directly relevant source when reasonably
  available.
- Independent corroboration for material claims when reasonably available.
- Enough source diversity to evaluate material risks and limitations.

Multiple pages repeating the same original claim shall not automatically
count as independent corroboration.

One authoritative primary source may provide stronger evidence for a
reported fact than several secondary pages repeating that fact.

Conflicting sources shall be preserved rather than combined through a
simple numeric agreement rule.

### Additional Research Condition

The Source Selection Agent may request another search pass when:

- A material evidence requirement remains uncovered.
- Only weak discovery sources are available for a material claim.
- Relevant risk information is missing.
- Search results are dominated by duplicate or derivative sources.
- Available sources appear outdated for a time-sensitive claim.
- A material source conflict may require another source.
- A `ValidationResult` identifies a correctable evidence gap.

An additional research request shall identify:

- The missing evidence.
- The affected candidate.
- The related evidence requirement.
- The reason additional research is needed.
- A suggested search purpose.

The orchestrator shall determine whether another search pass is allowed
under the configured workflow limits.

### Outputs

The Source Selection Agent shall produce one validated `SourceSelection`.

The `SourceSelection` shall identify:

- Selected search results.
- Excluded search results.
- Selection rationale.
- Preliminary source categories.
- Candidate and evidence-requirement associations.
- Potential duplicate or derivative-source concerns.
- Uncovered evidence requirements.
- Additional search requests, when needed.
- Source-selection status.

After source selection, deterministic Python tools shall produce:

- `RetrievalResult`
- `SourceRecord`
- `ExtractedEvidence`

The Source Selection Agent does not produce those records directly because
they require successful webpage retrieval and parsing.

### Final Stopping Condition

The Source Selection Agent's responsibility ends when it produces a
validated `SourceSelection` with one of these statuses:

- `ready_for_retrieval`
- `additional_search_required`
- `insufficient_candidate_sources`

The agent may return `ready_for_retrieval` when:

- Selected results reasonably cover the material evidence requirements
  needed for the next stage.
- Remaining evidence gaps are documented.
- Duplicate or derivative-source concerns are documented.
- Known source disagreements are preserved.
- The selected results are suitable for attempted webpage retrieval.

The agent shall not force a successful source-selection outcome when
adequate candidate sources cannot be found.

## Financial Analysis Agent

### Objective

Interpret validated financial evidence and deterministic calculation
results to compare investment candidates against the approved research
criteria and investor profile.

The Financial Analysis Agent produces a preliminary research conclusion
that may identify:

- A preferred candidate.
- Alternative candidates.
- A ranked shortlist.
- No sufficiently aligned candidate.
- Insufficient evidence for a recommendation.

The Financial Analysis Agent does not approve its own evidence, citations,
or final report. The Evidence Validation Agent independently reviews the
preliminary conclusion.

### Inputs

The Financial Analysis Agent receives:

- Validated `ResearchRequest`
- Validated `InvestorProfile`
- Validated `ResearchPlan`
- Validated `SourceRecord` objects
- Validated `ExtractedEvidence` objects
- Existing `CalculatedMetric` records, when available

Webpages must be retrieved, parsed, and converted into validated source and
evidence records before financial analysis begins.

### Available Tools

The Financial Analysis Agent may use:

- The generic deterministic financial-calculation tool.
- Evidence lookup support.

The current tool supports growth, margin, ratio, and difference
operations. The approved metric name and evidence records determine what a
calculation represents; the project does not require one calculator class
per financial metric.

Calculation formulas, required inputs, missing-data behavior, and expected
outputs shall be defined in the recommendation methodology and data
contracts.

### Tool Boundaries

Financial calculation tools shall:

- Accept validated inputs.
- Apply documented deterministic formulas.
- Preserve relevant units, reporting periods, and evidence references.
- Return validated `CalculatedMetric` objects with evidence lineage.
- Identify missing, invalid, unavailable, or non-applicable inputs.
- Produce the same output for the same validated input.

The Financial Analysis Agent may select calculation tools and interpret
their results, but important financial arithmetic shall be performed by
deterministic Python code.

### Responsibilities

The Financial Analysis Agent shall:

- Associate evidence and calculations with the correct candidate.
- Request approved financial calculations when needed.
- Interpret calculation results.
- Compare candidates using the approved recommendation methodology.
- Evaluate candidate alignment with the investor profile.
- Identify financial strengths and weaknesses.
- Evaluate growth, profitability, debt, valuation, and competitive
  position when supported by collected evidence.
- Identify material market, company, geographic, political, regulatory,
  currency, valuation, and competitive risks when relevant.
- Consider favorable and unfavorable evidence.
- Identify missing or conflicting information.
- Determine whether candidate data is meaningfully comparable.
- Explain why candidates rank differently.
- Determine whether the evidence supports a ranking.
- Produce a preliminary recommendation outcome.

The agent shall not alter or omit a calculation merely because the result
weakens a candidate.

### Candidate Analysis

The Financial Analysis Agent shall create one `CandidateAnalysis` for every
candidate that can be evaluated.

Each `CandidateAnalysis` shall include:

- Candidate identity.
- Analysis status.
- Relevant calculation records.
- Financial-growth evaluation.
- Profitability evaluation.
- Balance-sheet evaluation.
- Valuation evaluation.
- Competitive-position evaluation.
- Risk evaluation.
- Investor-profile alignment.
- Supporting evidence.
- Opposing evidence.
- Missing information.
- Unresolved conflicts.
- Category scores when supported.
- Weighted score when supported.
- Analysis confidence.
- Analysis rationale.

Missing, unavailable, invalid, insufficient, and non-applicable values
shall remain distinct.

A low score shall not be used to represent missing or non-applicable data.

### Comparability

Before ranking candidates, the Financial Analysis Agent shall consider:

- Reporting periods.
- Currency and units.
- Metric definitions.
- Candidate industries.
- Evidence completeness.
- Availability of material evaluation categories.

When material values are not directly comparable, the agent shall qualify
the comparison and avoid a precise ranking when the limitation could
change the result.

### Investor-Profile Alignment

The Financial Analysis Agent shall evaluate each candidate using only the
preferences preserved in the validated `InvestorProfile`.

Relevant preferences may include:

- Investment objective.
- Risk tolerance.
- Time horizon.
- Geographic preference.
- Industry or sector preference.
- Growth or income preference.
- Explicit exclusions.

The agent shall not infer missing investor preferences.

Risk tolerance may affect candidate alignment, but it shall not reduce the
evidence standard or eliminate material risks.

### Preliminary Recommendation

The Financial Analysis Agent shall produce a preliminary
`RecommendationResult` using one of these outcomes:

- `ranked_recommendation`
- `qualified_recommendation`
- `research_shortlist`
- `no_aligned_candidate`
- `insufficient_evidence`

When supported, the preliminary result shall identify:

- Preferred candidate.
- Alternative candidates.
- Candidate ranking.
- Recommendation rationale.
- Supporting and opposing evidence.
- Material risks.
- Missing information.
- Unresolved conflicts.
- Recommendation confidence.
- Human-review requirement.

The Financial Analysis Agent shall not force a preferred candidate when
the evidence does not support one.

### Outputs

The Financial Analysis Agent shall produce:

- One validated `CandidateAnalysis` for each evaluated candidate.
- One preliminary `RecommendationResult`.
- An `AdditionalResearchRequest` when more evidence may resolve a material
  gap.
- A structured `WorkflowErrorRecord` when analysis cannot continue.

The preliminary recommendation shall not proceed to report generation until
it passes evidence validation.

### Additional Research Condition

The Financial Analysis Agent may request additional research when:

- A material evaluation category lacks evidence.
- Candidate data cannot be meaningfully compared.
- Material risk evidence is missing.
- A source conflict could materially change the ranking.
- The available evidence cannot answer the original request.

The request shall identify the missing evidence, affected candidate,
related evaluation criterion, and whether the missing information blocks
the recommendation.

The orchestrator shall determine whether another research pass is allowed
under the configured workflow limits.

### Final Stopping Condition

The Financial Analysis Agent's responsibility ends when it produces:

- Validated candidate analyses and a preliminary recommendation, or
- A structured request for additional research, or
- A structured analysis-stage failure.

A preliminary recommendation shall be passed to the Evidence Validation
Agent.

### Scope Boundary

The Financial Analysis Agent does not:

- Search the web.
- Select sources for retrieval.
- Extract evidence from a source's Tavily-retrieved content.
- Invent missing financial values.
- Perform important arithmetic through language-model reasoning.
- Treat incompatible data as directly comparable.
- Approve its own evidence or citations.
- Guarantee investment performance.
- Issue trade instructions.
- Execute financial transactions.
- Write the final report.
- Write output files.

The Financial Analysis Agent creates the preliminary financial conclusion.

The Evidence Validation Agent determines whether that conclusion is
traceable, supported, internally consistent, responsive to the original
request, appropriately qualified, and compliant with project requirements.


## Evidence Validation Agent

### Objective

Independently determine whether the preliminary financial conclusion is
supported by the collected evidence, deterministic calculations, approved
methodology, investor profile, and original research request.

The Evidence Validation Agent does not create a separate investment
recommendation.

The agent reviews the preliminary `RecommendationResult` and determines
whether the result can proceed to report generation, requires correction,
requires additional research, or cannot be supported by the available
evidence.

### Inputs

The Evidence Validation Agent receives:

- Validated `ResearchRequest`
- Validated `InvestorProfile`
- Validated `ResearchPlan`
- Validated `SourceRecord` objects
- Validated `ExtractedEvidence` objects
- Validated `CalculatedMetric` objects
- Validated `ValidationClaim` objects containing claim text and source or
  calculation references
- Validated `CandidateAnalysis` objects
- Preliminary `RecommendationResult`

### Available Tools

The Evidence Validation Agent may use:

- Evidence-Lookup Tool
- Calculation-Record Lookup Tool
- Citation-Reference Checker
- Requirement-Compliance Checker

These tools may retrieve or check existing workflow records.

They shall not:

- Search the web.
- Retrieve new webpages.
- Create new evidence.
- Change financial calculations.
- Select a different preferred candidate.
- Approve unsupported claims.

### Evidence Validation Responsibilities

The Evidence Validation Agent shall determine whether:

- Material claims are supported by collected evidence.
- Evidence belongs to the correct candidate.
- Evidence references known `SourceRecord` objects.
- Source identifiers and evidence identifiers are valid.
- Evidence is relevant to the claim it supports.
- Financial calculations use traceable source values.
- Calculation inputs use compatible units and reporting periods.
- Missing information is disclosed.
- Conflicting evidence is disclosed.
- Favorable and unfavorable evidence are both represented.
- Material risks are included.
- Duplicate or derivative sources have not inflated confidence.
- Recommendation confidence matches the strength of the evidence.

The Evidence Validation Agent shall not treat the existence of a citation
as proof that the citation supports the claim.

### Prompt-Alignment Responsibilities

The Evidence Validation Agent shall determine whether the preliminary
recommendation:

- Answers the original research question.
- Uses the validated investor profile.
- Remains within the approved research scope.
- Applies the comparison criteria defined in the `ResearchPlan`.
- Respects explicit user preferences and exclusions.
- Distinguishes general research from personalized comparison.
- Preserves the human decision boundary.

A recommendation that does not answer the original request shall not be
approved even when its individual claims are supported.

### Calculation Validation Responsibilities

The Evidence Validation Agent shall verify that material calculations:

- Reference known `CalculatedMetric` objects or other validated calculation
  records supplied by the workflow.
- Use documented formulas.
- Preserve their input evidence references.
- Use appropriate candidates, units, currencies, and reporting periods.
- Handle missing, invalid, unavailable, or non-applicable data correctly.
- Have not been altered or selectively omitted to improve a candidate.
- Support the interpretation attributed to them.

The Evidence Validation Agent does not recalculate every value through
language-model reasoning.

Deterministic tests and calculation tools remain responsible for verifying
the arithmetic itself.

### Recommendation Validation Responsibilities

The Evidence Validation Agent shall determine whether:

- The preferred candidate follows from the candidate analyses.
- Alternative candidates are represented accurately.
- Candidate rankings are supported by comparable evidence.
- The recommendation rationale is consistent with the recorded scores.
- Material risks could change the conclusion.
- Missing information could change the conclusion.
- Unresolved source conflicts could change the conclusion.
- The outcome type is appropriate for the available evidence.
- The recommendation avoids guarantees and trade instructions.
- The conclusion is appropriately qualified.

The Evidence Validation Agent shall reject a forced ranking when the
available evidence supports only a shortlist or insufficient-evidence
outcome.

### Validation Findings

Each validation issue shall be returned as a structured
`ValidationFinding`.

A validation finding shall identify:

- Finding category.
- Severity.
- Affected candidate.
- Affected claim or calculation.
- Related source or evidence identifiers.
- Description of the issue.
- Required correction.
- Correction target.

Finding categories may include:

- Unsupported claim.
- Invalid citation.
- Irrelevant citation.
- Missing source evidence.
- Calculation-input problem.
- Reporting-period mismatch.
- Unit or currency mismatch.
- Undisclosed conflict.
- Missing material risk.
- Missing limitation.
- Overstated confidence.
- Prompt-alignment failure.
- Human-review boundary failure.

The exact fields and enum values shall be defined in
`specs/data-contracts.md`.

### Validation Outcomes

The Evidence Validation Agent shall produce a `ValidationResult` with one
of these outcomes:

- `approved`
- `analysis_correction_required`
- `additional_research_required`
- `insufficient_evidence`
- `rejected`

#### Approved

The recommendation is sufficiently supported and may proceed to report
generation.

#### Analysis Correction Required

The available evidence is sufficient, but the Financial Analysis Agent
must correct an interpretation, comparison, confidence level, risk
disclosure, or recommendation outcome.

#### Additional Research Required

A material evidence gap or unresolved conflict may be resolved through
another research pass.

#### Insufficient Evidence

The available evidence cannot support the proposed recommendation, and
additional research is unavailable, unnecessary, or outside workflow
limits.

#### Rejected

The result violates a project boundary or contains a failure that prevents
safe continuation.

### Correction Routing

When validation fails, the Evidence Validation Agent shall identify the
appropriate correction target.

Correction targets may include:

- Source Selection Agent for missing evidence.
- Retrieval and parsing tools for failed source extraction.
- Financial calculation tools for invalid calculation inputs.
- Financial Analysis Agent for unsupported interpretation or ranking.
- Orchestrator for workflow, input, or scope problems.

The Evidence Validation Agent shall not perform the correction itself.

The orchestrator shall route the structured finding to the appropriate
component and enforce the configured retry limit.

### Outputs

The Evidence Validation Agent shall produce:

- One validated `ValidationResult`.
- One or more `ValidationFinding` objects when issues exist.
- Any required `AdditionalResearchRequest`.
- Any validation-stage `WorkflowErrorRecord`.

An approved `ValidationResult` shall identify the candidate analyses,
recommendation result, calculations, evidence, and sources approved for
report generation.

### Final Stopping Condition

The Evidence Validation Agent's responsibility ends when it produces a
validated outcome of:

- Approved.
- Analysis correction required.
- Additional research required.
- Insufficient evidence.
- Rejected.

Only an approved result may proceed to the Report Writing Agent as a final
recommendation.

An insufficient-evidence result may proceed only for creation of a clearly
labeled limitation report that does not present a preferred investment.

### Scope Boundary

The Evidence Validation Agent does not:

- Produce an independent investment recommendation.
- Replace the preferred candidate with its own choice.
- Search the web.
- Retrieve or parse webpages.
- Create financial evidence.
- Perform financial analysis from scratch.
- Change deterministic calculation results.
- Resolve source conflicts by deleting unfavorable evidence.
- Invent missing sources or citations.
- Write the final report.
- Write output files.

The Evidence Validation Agent verifies whether the preliminary conclusion
can be defended.

The Report Writing Agent communicates only the conclusion and evidence
approved by the validation process.

## Report Writing Agent

### Objective

Transform the approved research findings into a clear, organized, and
cited financial research report for human review.

The Report Writing Agent communicates the validated analysis and
recommendation.

It does not perform new research, create new financial conclusions, or
change the approved recommendation.

### Inputs

The Report Writing Agent receives:

- Validated `ResearchRequest`
- Validated `InvestorProfile`
- Validated `ResearchPlan`
- Approved `SourceRecord` objects
- Approved `ExtractedEvidence` objects
- Approved calculation records, including `CalculatedMetric` objects
- Approved `CandidateAnalysis` objects
- Approved `RecommendationResult`
- Approved `ValidationResult`

When the approved workflow outcome is `insufficient_evidence`, the Report
Writing Agent may receive an approved insufficient-evidence result instead
of an approved recommendation.

### Available Tools

The Report Writing Agent may use:

- Evidence-Lookup Tool
- Citation-Formatting Tool
- Report-Template Tool

The Report Writing Agent does not write files directly.

After the report draft passes structural validation, a deterministic Python
function shall write the Markdown artifact to the approved output location.

### Report-Writing Responsibilities

The Report Writing Agent shall:

- Present the original research question.
- Summarize the relevant investor preferences.
- Describe the approved research scope.
- Explain the comparison methodology.
- Present each candidate analysis.
- Explain the approved recommendation outcome.
- Present supporting and opposing evidence.
- Present material financial calculations.
- Present material risks.
- Present missing information.
- Present unresolved conflicts.
- Present research and methodology limitations.
- Include citations for material factual claims.
- Include the recommendation-confidence level.
- Include a human-review statement.
- Use clear and professional language.

The report shall distinguish among:

- Sourced facts.
- Deterministic calculations.
- Agent interpretations.
- Preliminary or approved recommendations.
- Missing or uncertain information.

### Required Report Structure

The report shall contain:

1. Title.
2. Research question.
3. Investor profile.
4. Research scope.
5. Executive summary.
6. Research methodology.
7. Candidate analyses.
8. Candidate comparison.
9. Recommendation outcome.
10. Material risks.
11. Missing information and unresolved conflicts.
12. Limitations.
13. Human-review statement.
14. Sources.

The exact Markdown headings and data fields shall be defined in the report
contract and report template.

### Candidate Presentation

For each evaluated candidate, the report shall present:

- Candidate name.
- Relevant financial findings.
- Relevant calculation results.
- Strengths.
- Weaknesses.
- Material risks.
- Investor-profile alignment.
- Missing information.
- Analysis confidence.
- Supporting citations.

The Report Writing Agent shall not make one candidate appear stronger by
omitting approved unfavorable evidence.

### Recommendation Presentation

When the approved outcome is a ranked or qualified recommendation, the
report shall explain:

- Which candidate appears most aligned with the supplied criteria.
- Why the candidate received that result.
- Which alternatives were considered.
- Why the alternatives ranked differently.
- What risks could materially affect the conclusion.
- What missing information could change the conclusion.
- How strong the supporting evidence is.

The report shall describe the recommendation as a research conclusion for
human consideration.

It shall not describe the recommendation as:

- A command to purchase or sell.
- A guaranteed outcome.
- A promise of profit.
- A risk-free opportunity.
- A substitute for professional financial advice.
- A decision made on behalf of the user.

### Insufficient-Evidence Report

When the approved outcome is `insufficient_evidence`, the Report Writing
Agent shall produce a limitation report that explains:

- What research was completed.
- Which candidates were considered.
- Which evidence was available.
- Which evidence was missing.
- Which conflicts could not be resolved.
- Why a recommendation could not be supported.
- What additional information would be needed.

An insufficient-evidence report shall not identify a preferred candidate.

### Citation Responsibilities

The Report Writing Agent shall:

- Cite material factual claims.
- Use only source identifiers approved by the `ValidationResult`.
- Place citations near the claims they support.
- Preserve accurate source titles and URLs.
- Avoid citing unrelated evidence.
- Avoid citing search snippets as retrieved source evidence.
- Include an organized source section.

The Report Writing Agent shall not create:

- New source identifiers.
- New URLs.
- New publication dates.
- New authors.
- New financial values.
- New factual claims not present in the validated workflow data.

### Calculation Presentation

When presenting a material calculated value, the report should identify:

- The metric.
- The candidate.
- The calculated result.
- The relevant reporting period.
- The interpretation approved during validation.
- The source evidence when material.

The report does not need to display every internal calculation field unless
the field is necessary to explain or reproduce the conclusion.

### Tone and Clarity

The report shall:

- Use neutral, evidence-based language.
- Avoid exaggerated certainty.
- Avoid unnecessary technical jargon.
- Explain important financial terms when needed.
- Use consistent candidate names and terminology.
- Clearly label uncertainty.
- Clearly label unavailable or non-applicable information.
- Remain readable in standard Markdown.

### Human-Review Statement

Every completed recommendation report shall include a statement equivalent
to:

> This report is an informational research artifact based on the cited
> public evidence and project-defined methodology. It does not execute
> financial transactions or make the final investment decision. The user
> remains responsible for reviewing the evidence, considering personal
> circumstances, and making any final decision.

The exact language may vary, but the meaning shall be preserved.

### Outputs

The Report Writing Agent shall produce a validated `ReportDraft`.

The `ReportDraft` shall contain:

- Report title.
- Markdown content.
- Recommendation outcome.
- Referenced source identifiers.
- Referenced calculation identifiers.
- Human-review statement.
- Draft status.

The exact fields shall be defined in `specs/data-contracts.md`.

After the `ReportDraft` passes structural validation, deterministic file
writers shall produce:

- Markdown research report.

### Report Validation

Before file writing, deterministic validation shall confirm that:

- Required report sections are present.
- Referenced source identifiers exist.
- Referenced calculation identifiers exist.
- The recommendation outcome matches the approved `ValidationResult`.
- The human-review statement is present.
- The report contains no unsupported output path.
- The output filename uses the approved naming convention.

If structural validation fails, the orchestrator may return the draft to
the Report Writing Agent with the validation errors.

The Report Writing Agent shall not receive permission to change the
approved financial conclusion during a formatting retry.

### Final Stopping Condition

The Report Writing Agent's responsibility ends when it produces a validated
`ReportDraft` that:

- Accurately reflects the approved recommendation or insufficient-evidence
  outcome.
- Contains all required sections.
- Uses only approved evidence and calculations.
- Includes required citations.
- Includes risks and limitations.
- Includes the human-review statement.
- Is ready for deterministic file writing.

### Scope Boundary

The Report Writing Agent does not:

- Search the web.
- Select or retrieve sources.
- Parse webpages.
- Perform new financial calculations.
- Reanalyze investment candidates.
- Change the approved candidate ranking.
- Increase recommendation confidence.
- Remove approved risks or limitations.
- Introduce new material facts.
- Invent sources or citations.
- Write to unrestricted file locations.
- Execute financial transactions.

The Report Writing Agent communicates the validated result.

Deterministic Python functions save the approved report and structured
workflow artifact to the configured output directory.

