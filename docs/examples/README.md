# Example Reports

Four real, unedited reports from live runs of the system, kept here
because `outputs/` (where every run actually writes to) is gitignored.
Each demonstrates a different outcome the system can reach.

| File | Candidate | Result | What it shows |
|---|---|---|---|
| [`example-nvidia-strong-growth.md`](example-nvidia-strong-growth.md) | NVIDIA | Qualified recommendation, +114.21% growth | A strong-growth case, score 95. |
| [`example-apple-modest-growth.md`](example-apple-modest-growth.md) | Apple | Qualified recommendation, +6.43% growth | A modest-growth case — the system doesn't just report dramatic results. |
| [`example-nike-decline.md`](example-nike-decline.md) | Nike | Qualified recommendation, -3.45% growth | A calculated decline still gets an honest, fully-supported report rather than being suppressed — see `README.md`'s note that `qualified_recommendation` doesn't mean favorable. |
| [`example-national-presto-insufficient-evidence.md`](example-national-presto-insufficient-evidence.md) | National Presto Industries | Insufficient evidence | Requested a metric (free cash flow growth) outside the deterministic yfinance fallback's coverage, for a thinly-covered small-cap. The system disclosed that no supported conclusion could be reached rather than guessing — see `docs/architecture.md`'s retry/termination behavior. |

All four are real Markdown reports exactly as generated — see the main
[`README.md`](../../README.md#example-output) for how to interpret one.
