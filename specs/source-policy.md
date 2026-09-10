# Source Policy

## Purpose

This document defines how Agentic Financial Analysis Automation discovers,
selects, retrieves, evaluates, stores, cites, and validates research
sources.

The purpose of this policy is to prevent the system from treating every
search result or webpage as equally reliable.

## 1. Source Principles

The research workflow shall follow these principles:

1. Search results are discovery records, not verified evidence.
2. The underlying webpage should be retrieved before it supports a material
   report claim.
3. Every material factual claim should be traceable to collected evidence.
4. Source authority, relevance, recency, and independence should be
   considered.
5. Missing source information must not be invented.
6. Conflicting evidence must be disclosed.
7. Scraped webpage instructions are untrusted data.
8. Multiple pages repeating one original claim do not automatically count
   as independent confirmation.

## 2. Source Categories

### Tier 1: Primary and Authoritative Sources

Preferred primary sources may include:

- Regulatory filings.
- Government or regulatory publications.
- Official company financial reports.
- Official investor-relations publications.
- Audited financial statements.
- Official exchange publications.
- Official economic or statistical data.
- Original research reports published by the responsible organization.

Tier 1 status does not guarantee that every statement is complete or
current. The source must still be relevant to the research question.

### Tier 2: Reputable Secondary Sources

Secondary sources may include:

- Established financial publications.
- Reputable news organizations.
- Recognized market-research organizations.
- Research institutions.
- Academic publications.
- Financial-data services with identifiable methodology.

Secondary sources may support context, interpretation, market developments,
and comparison.

Whenever practical, material financial values should be confirmed against a
primary source.

### Tier 3: Discovery and Commentary Sources

Discovery sources may include:

- General financial websites.
- Blogs.
- Opinion articles.
- Aggregated market commentary.
- Community discussions.
- Search-result summaries.

Tier 3 sources may help identify:

- Potential candidates.
- Relevant topics.
- Search terms.
- Risks requiring further research.
- Primary sources to locate.

Tier 3 sources should not be the sole support for a material financial
claim when stronger sources are available.

### Unsupported or Restricted Sources

A source may be excluded when:

- Its content cannot be retrieved.
- Its content is outside the approved research scope.
- Its publisher cannot be identified when identity is material.
- It contains no relevant evidence.
- It presents unsupported promotional claims.
- It requires bypassing access controls.
- Retrieval would violate configured technical restrictions.
- It contains an unsupported content type.
- Its data cannot be connected to an identifiable reporting period.
- Its reliability cannot be reasonably evaluated.

Exclusion should be recorded when the source was otherwise expected to
contribute material evidence.

## 3. Source Selection

Sources should be selected based on:

- Relevance to the research question.
- Authority of the publisher.
- Connection to the candidate being evaluated.
- Presence of evidence needed by the research plan.
- Recency when the claim is time-sensitive.
- Availability of publication and reporting dates.
- Independence from promotional interests.
- Ability to retrieve and preserve supporting content.
- Consistency or meaningful disagreement with other sources.

The system shall not select a source solely because it appears first in
search results.

## 4. Candidate Discovery

A discovery source may identify a possible investment candidate.

Candidate discovery does not establish that the candidate:

- Is suitable for the user.
- Is financially strong.
- Is low risk.
- Should receive a recommendation.
- Is supported by sufficient evidence.

Discovered candidates must pass through the same evidence, analysis, risk,
and validation processes as user-specified candidates.

## 5. Source Retrieval

For each selected webpage, the system should preserve:

- Original selected URL.
- Final retrieved URL when redirects occur.
- Retrieval status.
- Retrieval date.
- HTTP response status when available.
- Content type.
- Retrieval failure reason when applicable.

A failed retrieval shall not be represented as successfully collected
evidence.

The initial system shall not bypass:

- Authentication requirements.
- Paywalls.
- Access controls.
- Anti-automation controls.
- Unsupported browser requirements.

If material information cannot be retrieved, the limitation shall be
recorded.

## 6. Source Metadata

A source record should preserve the following fields when available:

- Source identifier.
- Title.
- URL.
- Publisher or organization.
- Author.
- Publication date.
- Reporting period.
- Retrieval date.
- Source category.
- Search query used for discovery.
- Relevant extracted evidence.
- Retrieval status.
- Parsing status.
- Notes about limitations.

Unavailable metadata shall be stored as unavailable rather than inferred
without evidence.

## 7. Evidence Extraction

Extracted evidence shall remain connected to its source record.

An evidence item should preserve:

- Evidence identifier.
- Source identifier.
- Extracted text or structured value.
- Relevant heading or section when available.
- Financial period when relevant.
- Currency and unit when relevant.
- Candidate to which it applies.
- Metric or risk category to which it applies.
- Extraction notes when needed.

The system shall distinguish direct source content from summaries or
interpretations generated by an agent.

## 8. Financial Values

A financial value should not be used without relevant context.

When applicable, financial evidence should preserve:

- Value.
- Currency.
- Unit or scale.
- Fiscal or calendar period.
- Whether the value is reported or calculated.
- Source.
- Calculation inputs when calculated.

Values from different periods, currencies, or accounting contexts shall
not be compared as if they are directly equivalent without normalization
or explicit qualification.

## 9. Source Recency

Recency shall be evaluated relative to the claim.

Time-sensitive claims may include:

- Current price.
- Recent earnings.
- Current valuation.
- Current leadership.
- Current regulation.
- Recent geopolitical conditions.
- Current business guidance.

Less time-sensitive claims may include:

- Historical company events.
- Previously published financial results.
- Long-term methodology definitions.

The system shall not assume that the newest source is automatically the
most authoritative.

When an older source is used for a current conclusion, the report shall
identify the limitation when material.

## 10. Source Independence

The system should distinguish independent confirmation from repeated
republication.

The following do not necessarily represent independent evidence:

- Multiple search results linking to the same page.
- Articles repeating the same press release.
- Aggregators reproducing one data provider.
- Commentary derived from the same original report.
- Duplicate pages hosted under different URLs.

Duplicate or derivative sources shall not artificially increase evidence
confidence.

## 11. Conflicting Sources

When material sources conflict, the system shall:

1. Preserve both claims.
2. Identify the sources involved.
3. Compare publication dates, reporting periods, units, and definitions.
4. Prefer primary evidence when it directly resolves the conflict.
5. Avoid silently selecting the more favorable value.
6. Disclose unresolved conflict in the final report.
7. Reduce recommendation confidence when the conflict is material.

## 12. Promotional Content

Official company sources may provide authoritative company-reported data,
but they may also contain promotional interpretation.

The system should distinguish:

- Reported financial facts.
- Forward-looking statements.
- Management interpretation.
- Marketing language.
- Independent analysis.

Promotional language shall not be treated as verified performance evidence
without supporting data.

## 13. Search Snippets

Search-result snippets may be used for source discovery.

Search snippets shall not normally serve as the sole evidence for a
material claim because snippets may be:

- Incomplete.
- Truncated.
- Out of context.
- Stale.
- Different from the retrieved webpage.

If the underlying page cannot be retrieved, the snippet may be recorded as
unverified discovery information but shall not be presented as fully
validated evidence.

## 14. Citation Policy

Each material factual report claim shall reference:

- A collected source identifier, or
- A deterministic calculation whose inputs reference collected sources.

A valid citation must:

- Refer to a known source record.
- Correspond to the same research workflow.
- Support the relevant claim.
- Preserve a usable source URL.
- Avoid presenting search snippets as retrieved page evidence.

A citation is invalid when:

- The source identifier does not exist.
- The source was never retrieved when retrieval was required.
- The source does not support the cited claim.
- The URL was fabricated.
- The source applies to a different candidate or period.
- The citation points only to unrelated content.

## 15. Minimum Evidence Expectations

The system shall use enough evidence to support the type of conclusion it
produces.

A candidate shall not receive a high-confidence recommendation when:

- Only one weak source is available.
- Material financial information is unavailable.
- Major risks cannot be researched.
- Sources materially conflict without resolution.
- The evidence is outdated for the claim.
- The candidate cannot be compared using the approved methodology.

The exact minimum source configuration may be established during
implementation testing and documented as a methodology revision.

The system shall prefer an insufficient-evidence outcome over an
unsupported recommendation.

## 16. Scraped Content Trust Boundary

All scraped content shall be treated as untrusted data.

The application shall ignore webpage text that attempts to:

- Change the research objective.
- Modify the investor profile.
- Directly control an agent.
- Override project instructions.
- Disable citations.
- Conceal risks.
- Guarantee returns.
- Select a predetermined candidate.
- Request secrets or system information.
- Change the output destination.

Such text may be retained as page content for testing or analysis, but it
shall not be executed as an instruction.

## 17. Source Exclusion Record

When a potentially significant source is excluded, the workflow may record:

- Source URL.
- Exclusion reason.
- Retrieval status.
- Parsing status.
- Whether the exclusion affects confidence.
- Whether another source was used instead.

## 18. Report Source Section

The final report shall include a source section that provides, when
available:

- Source title.
- Publisher.
- Publication date.
- Retrieval date.
- URL.
- Source identifier.

The source section shall not include invented metadata.

## 19. Testing Expectations

Source-policy tests shall include:

- Valid primary source.
- Valid secondary source.
- Duplicate URLs.
- Duplicate evidence from different URLs.
- Missing publication date.
- Failed retrieval.
- Unsupported content type.
- Malformed HTML.
- Conflicting financial values.
- Search snippet without retrievable page.
- Promotional language.
- Prompt injection inside webpage text.
- Fabricated source identifier.
- Citation that does not support its claim.
- Evidence from the wrong reporting period.

## Change Control

Changes to this policy shall be reflected in:

- Source-record data contracts.
- Search and scraping implementation.
- Citation validation.
- Recommendation confidence rules.
- Related tests.
- Acceptance criteria.
- The roadmap when phase scope changes.