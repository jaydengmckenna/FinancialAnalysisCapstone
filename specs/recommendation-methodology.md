# Recommendation Methodology

## Purpose

This document defines how Agentic Financial Analysis Automation evaluates
and compares potential investment candidates.

The methodology is designed to produce transparent research conclusions for
human review. It does not predict guaranteed returns and does not replace
professional financial advice.

## 1. Methodology Principles

The recommendation process shall follow these principles:

1. Research occurs before recommendation.
2. Candidates are evaluated using documented criteria.
3. Financial calculations use deterministic Python functions.
4. Investor preferences influence alignment, not factual evidence.
5. Supporting and opposing evidence are both considered.
6. Material risks cannot be removed because they weaken a candidate.
7. Missing data reduces confidence rather than being silently ignored.
8. A recommendation may be withheld when evidence is insufficient.
9. Scores support explanation but do not replace judgment.
10. Final decisions remain with the human user.

## 2. Research Outcome Types

The workflow may produce one of the following outcomes:

### Ranked Recommendation

Candidates are sufficiently comparable and supported by enough evidence to
produce an ordered result.

### Qualified Recommendation

One or more candidates appear aligned with the criteria, but material
limitations reduce confidence.

### Research Shortlist

Candidates appear worthy of additional research, but available evidence
does not support a final ranking.

### Insufficient Evidence

No recommendation is produced because the available evidence is incomplete,
conflicting, outdated, or unreliable.

### No Aligned Candidate

The researched candidates do not appear sufficiently aligned with the
supplied criteria.

## 3. Investor Profile

The investor profile may include:

- Investment objective.
- Risk tolerance.
- Time horizon.
- Geographic preference.
- Sector or industry preference.
- Asset-type preference.
- Growth or income preference.
- Liquidity preference.
- Excluded investments.
- Additional research constraints.

### Required Profile Information

For a personalized comparison, the initial methodology should require:

- Investment objective.
- Risk tolerance.
- Time horizon.

Geographic, sector, and asset preferences become required when the user
uses them to define the research scope.

### Missing Profile Information

When required profile information is missing, the system shall:

1. Request the missing information, or
2. Clearly label the output as general research rather than a personalized
   comparison.

Missing profile values shall not be silently inferred.

## 4. Candidate Eligibility

A candidate may enter the final comparison when:

- It matches the approved research scope.
- It is the correct type of investment.
- Sufficient public information can be collected.
- Relevant risks can be researched.
- The candidate can be evaluated using enough of the approved criteria.
- Candidate identity can be verified.

A candidate may be excluded when:

- It falls outside the requested scope.
- It cannot be reliably identified.
- Material evidence cannot be retrieved.
- It cannot be meaningfully compared with the other candidates.
- Its inclusion would violate an explicit user exclusion.

Candidate exclusion shall be recorded.

## 5. Evaluation Categories

The initial methodology may evaluate the following categories.

### 5.1 Financial Growth

Potential evidence may include:

- Revenue growth.
- Earnings growth when applicable.
- Cash-flow growth when available.
- Growth consistency across reported periods.

### 5.2 Profitability

Potential evidence may include:

- Operating margin.
- Net margin.
- Return measures when supported.
- Profitability trend.

### 5.3 Balance-Sheet Strength

Potential evidence may include:

- Debt levels.
- Debt-related ratios.
- Cash position.
- Liquidity measures.
- Ability to support business obligations.

### 5.4 Valuation

Potential evidence may include:

- Price-to-earnings ratio when applicable.
- Price-to-sales ratio.
- Other supported valuation measures.
- Valuation relative to comparable candidates.
- Valuation limitations.

A valuation metric shall not be forced when it is not applicable.

### 5.5 Competitive Position

Potential evidence may include:

- Market position.
- Product or service differentiation.
- Business diversification.
- Customer concentration.
- Competitive threats.
- Documented strategic advantages.

Qualitative competitive claims require supporting evidence.

### 5.6 Risk Profile

Potential evidence may include:

- Market risk.
- Company-specific risk.
- Industry concentration.
- Geographic exposure.
- Political or regulatory exposure.
- Currency exposure.
- Liquidity risk.
- Valuation risk.
- Data-quality risk.
- Source-availability risk.

### 5.7 Investor-Profile Alignment

Alignment may consider:

- Compatibility with stated risk tolerance.
- Compatibility with stated time horizon.
- Compatibility with investment objective.
- Compatibility with geographic preference.
- Compatibility with sector preference.
- Compatibility with stated exclusions.

Profile alignment shall not transform weak evidence into strong financial
evidence.

## 6. Initial Scoring Framework

The initial project may use the following scoring categories:

| Category | Initial Weight |
|---|---:|
| Financial Growth | 20% |
| Profitability | 15% |
| Balance-Sheet Strength | 15% |
| Valuation | 15% |
| Competitive Position | 15% |
| Risk Profile | 10% |
| Investor-Profile Alignment | 10% |
| Total | 100% |

These weights are project-defined research weights. They are not universal
financial rules and do not guarantee investment performance.

The weights may be revised before implementation if testing shows that they
do not support the intended research use case.

Any weight change shall be documented in this file and the roadmap change
log when it materially affects project scope.

## 7. Category Scores

Each category may be scored on a normalized scale from 0 to 100.

A general interpretation may be:

- 80 to 100: Strong evidence of favorable alignment.
- 60 to 79: Generally favorable with meaningful limitations.
- 40 to 59: Mixed or neutral evidence.
- 20 to 39: Generally unfavorable or materially incomplete.
- 0 to 19: Strongly unfavorable or unsupported.

A category score shall include:

- Score.
- Evidence used.
- Calculation or reasoning summary.
- Missing information.
- Relevant risks.
- Confidence in the category score.

A low score and an unavailable score are not the same.

## 8. Weighted Score

When all required category scores are available, the weighted candidate
score may be calculated as:

```text
Weighted Score =
    Sum of each Category Score multiplied by its Category Weight
```

Example structure:

```text
Growth Score × 0.20
+ Profitability Score × 0.15
+ Balance-Sheet Score × 0.15
+ Valuation Score × 0.15
+ Competitive-Position Score × 0.15
+ Risk-Profile Score × 0.10
+ Investor-Alignment Score × 0.10
```

The calculation shall be implemented as a deterministic Python function.

The language model may explain the result but shall not perform the final
weighted arithmetic.

## 9. Missing Category Data

When category data is missing, the system shall not silently assign zero.

The methodology shall distinguish:

- **Unavailable:** The evidence could not be obtained.
- **Not applicable:** The metric does not apply to the candidate.
- **Invalid:** The collected value cannot be used.
- **Insufficient:** Some evidence exists but does not support a reliable
  score.

The initial implementation should avoid redistributing missing category
weight automatically.

When a material category cannot be evaluated, the system should:

1. Mark the category unavailable or insufficient.
2. Reduce confidence.
3. Explain the limitation.
4. Avoid precise ranking when the missing category could change the result.

## 10. Risk-Tolerance Interpretation

Risk tolerance affects how the system interprets candidate alignment.

### High Risk Tolerance

A high-risk profile may be more compatible with:

- Greater price volatility.
- Emerging-market exposure.
- Currency exposure.
- Concentrated growth opportunities.
- Regulatory uncertainty.
- Smaller or less established candidates.

High risk tolerance does not mean:

- Risk should be ignored.
- Evidence standards should be reduced.
- Any speculative candidate is suitable.
- Losses are acceptable without disclosure.
- The system can guarantee higher returns.

### Moderate Risk Tolerance

A moderate-risk profile may favor a balance between:

- Growth opportunity.
- Financial stability.
- Diversification.
- Valuation.
- Risk exposure.

### Low Risk Tolerance

A low-risk profile may place greater emphasis on:

- Financial stability.
- Lower volatility when evidence is available.
- Balance-sheet strength.
- Predictable performance.
- Lower concentration.
- Liquidity.

The implementation shall not claim that a risk category alone determines
investment suitability.

## 11. Time-Horizon Interpretation

The time horizon shall affect the interpretation of evidence.

A longer time horizon may place more emphasis on:

- Sustainable growth.
- Competitive position.
- Long-term industry conditions.
- Ability to endure temporary volatility.

A shorter time horizon may require greater attention to:

- Liquidity.
- Near-term uncertainty.
- Current valuation.
- Upcoming financial or regulatory risks.

The application shall avoid inventing a time horizon.

## 12. Foreign Investment Considerations

When the user requests foreign investments, the analysis should consider
relevant evidence concerning:

- Currency exposure.
- Political conditions.
- Regulatory environment.
- Local market structure.
- Accounting and reporting differences.
- Geographic concentration.
- Access and liquidity.
- Depositary receipt structure when applicable.
- Tax considerations as a limitation.

The application may identify tax considerations but shall not provide tax
advice.

## 13. Evidence Strength

Evidence strength should consider:

- Source authority.
- Source relevance.
- Source recency.
- Source independence.
- Availability of primary evidence.
- Agreement across sources.
- Completeness of financial context.
- Availability of both supporting and opposing evidence.

Evidence strength shall be recorded separately from the candidate score.

A high candidate score with weak evidence shall not be represented as a
high-confidence recommendation.

## 14. Recommendation Confidence

Recommendation confidence may be:

- High.
- Moderate.
- Low.
- Insufficient.

Confidence should consider:

- Evidence quality.
- Evidence completeness.
- Source agreement.
- Metric availability.
- Candidate comparability.
- Recency of time-sensitive information.
- Number of unresolved limitations.

Confidence is not a prediction of investment success.

## 15. Candidate Ranking

Candidates may be ranked when:

- The same approved methodology can be applied.
- Relevant periods and units are comparable.
- Material categories contain enough evidence.
- Source quality is sufficient.
- Unresolved conflicts do not invalidate the comparison.

Candidates shall not be ranked solely because the system is expected to
produce a winner.

## 16. Recommendation Content

A recommendation shall include:

- Candidate or candidates evaluated.
- Candidate that appears most aligned, when supported.
- Alternative candidates.
- Supporting evidence.
- Opposing evidence.
- Important calculations.
- Material risks.
- Missing information.
- Methodology limitations.
- Evidence strength.
- Recommendation confidence.
- Human-review statement.

## 17. Required Recommendation Language

Recommended language:

> Based on the collected evidence and the documented evaluation
> methodology, this candidate appears most aligned with the supplied
> research criteria and may merit additional human investigation.

Acceptable alternatives may describe:

- Highest research score.
- Strongest alignment with supplied criteria.
- Most compelling candidate for further research.
- Qualified recommendation.
- Insufficient evidence.

The report shall not state:

- The user must buy the investment.
- The investment will produce a profit.
- The investment is guaranteed to outperform.
- The investment is suitable for every investor.
- The investment has no risk.

## 18. Methodology Limitations

The report shall disclose that:

- The methodology is project-defined.
- Public information may be incomplete.
- Market conditions can change.
- Scores depend on selected criteria and weights.
- Qualitative interpretation may involve model judgment.
- Historical information does not guarantee future outcomes.
- The system does not execute trades or make the final decision.

## 19. Deterministic Calculation Requirements

Each implemented financial calculation shall document:

- Formula.
- Required inputs.
- Accepted units.
- Missing-input behavior.
- Non-applicable behavior.
- Output type.
- Rounding behavior.
- Tests.

Calculation details will be finalized during Phase 3 data-contract design
and Phase 6 implementation planning.

## 20. Methodology Testing

Tests shall include:

- Complete comparable candidates.
- Missing category data.
- Non-applicable valuation metric.
- Conflicting source values.
- Different currencies.
- Different reporting periods.
- High-risk investor profile.
- Low-risk investor profile.
- Missing time horizon.
- Foreign investment request.
- Weak evidence with a high raw score.
- Strong evidence with mixed financial results.
- Candidate that cannot be meaningfully compared.
- Insufficient-evidence outcome.
- Deterministic weighted-score calculation.

## Change Control

Methodology changes shall be documented when they affect:

- Evaluation categories.
- Scoring ranges.
- Category weights.
- Missing-data behavior.
- Risk interpretation.
- Investor-profile alignment.
- Recommendation confidence.
- Candidate-ranking rules.

A methodology change shall trigger review of:

- Functional requirements.
- Data contracts.
- Calculation functions.
- Architecture.
- Tests.
- Acceptance criteria.
- Example reports.