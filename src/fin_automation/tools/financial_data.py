"""Deterministic lookup of empirical financial metrics via yfinance.

This is intentionally plain Python, not a smolagents `Tool`. Fetching a
named company's specific metric for a specific fiscal period involves
no judgment: the mapping from ticker + metric + period to a value is
mechanical, the same way the deterministic financial-calculation tool
performs arithmetic without agent involvement. `FinancialAnalysisAgent`
owns and calls this directly to fill evidence gaps before it asks the
model to select calculations.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

import yfinance as yf


# Recognized metric names, mapped to their yfinance financial-statement
# row label. Deliberately minimal: only what the project currently asks
# for. Extend this mapping as new metric types are actually needed.
_SUPPORTED_METRICS: dict[str, str] = {
    "revenue": "Total Revenue",
    "total revenue": "Total Revenue",
    "net income": "Net Income",
    "gross profit": "Gross Profit",
}

_BILLION = Decimal("1000000000")


@dataclass(frozen=True)
class FinancialDataPoint:
    """One empirical metric value retrieved from yfinance."""

    ticker: str
    company_name: str
    metric_name: str
    value: Decimal
    unit: str
    currency: str
    fiscal_period_end: date
    source_url: str


class FinancialDataTool:
    """Fetch one fiscal-year metric value for one ticker via yfinance.

    Values are always normalized to billions. yfinance always reports
    an exact, unscaled amount (there is no per-request ambiguity about
    "millions" vs "billions" coming from the data source itself), so
    normalizing once here means every value this tool produces is
    self-consistent, and comparable to any other value this tool
    produces, without needing to detect or reconcile mixed units later.
    """

    def resolve_metric_row(self, metric_name: str) -> str | None:
        """Map a free-text metric name to a supported statement row.

        Args:
            metric_name: Free-text metric description, e.g. "Total
                Revenue" or "FY2024 revenue in USD billions". Matching
                is a simple case-insensitive substring check against
                the supported metric keywords.

        Returns:
            The yfinance financial-statement row label, or None if no
            supported metric keyword was found.
        """

        normalized = metric_name.casefold()
        for keyword, row_label in _SUPPORTED_METRICS.items():
            if keyword in normalized:
                return row_label

        return None

    def fetch_metric(
        self,
        ticker: str,
        metric_name: str,
        period_offset: int = 0,
    ) -> FinancialDataPoint | None:
        """Fetch one fiscal-year metric value for one ticker.

        Args:
            ticker: Stock ticker symbol, e.g. "AAPL".
            metric_name: Free-text metric description. Must contain a
                recognized keyword (see `resolve_metric_row`).
            period_offset: 0 for the most recently completed fiscal
                year available, 1 for the year before that, and so on.
                Different companies have different fiscal year-end
                months, so this is relative position, not a specific
                calendar year.

        Returns:
            A `FinancialDataPoint` with the value normalized to
            billions, or None if the ticker, metric, or period could
            not be resolved. Never raises for ordinary "not found"
            cases; callers should treat None the same as any other
            missing-evidence case.
        """

        row_label = self.resolve_metric_row(metric_name)
        if row_label is None:
            return None
        if period_offset < 0:
            return None
        
        try:
            ticker_obj = yf.Ticker(ticker=ticker.strip().upper())
            financials = ticker_obj.financials
        except Exception:
             # yfinance is an unofficial wrapper around Yahoo's endpoints
            # and can fail for reasons unrelated to whether the data
            # exists (network errors, upstream format changes, rate
            # limiting). Treat any failure as "no data available."
            return None

        if financials is None or financials.empty:
            return None

        if row_label not in financials.index:
            return None

        row = financials.loc[row_label].dropna()
        if period_offset >= len(row):
            return None

        fiscal_year_end = row.index[period_offset]
        raw_value = row.iloc[period_offset]

        try:
            billions_value = (
                Decimal(str(raw_value)) / _BILLION
            ).quantize(Decimal("0.001"))
        except (InvalidOperation, TypeError, ValueError):
            return None

        try:
            info = ticker_obj.info
        except Exception:
            info = {}

        currency = info.get("currency") or "USD"
        company_name = info.get("longName") or ticker.strip().upper()

        return FinancialDataPoint(
            ticker=ticker.strip().upper(),
            company_name=company_name,
            metric_name=row_label,
            value=billions_value,
            unit="billion",
            currency=currency,
            fiscal_period_end=fiscal_year_end.date(),
            source_url=(
                f"https://finance.yahoo.com/quote/{ticker.strip().upper()}/financials"
            ),
        )

        