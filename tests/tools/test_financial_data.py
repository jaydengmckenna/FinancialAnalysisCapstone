"""Focused tests for the deterministic yfinance-backed data lookup."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fin_automation.tools.financial_data import FinancialDataTool


def make_financials_frame() -> pd.DataFrame:
    """Build a small financials DataFrame shaped like yfinance's own."""

    columns = [
        pd.Timestamp("2024-09-30"),
        pd.Timestamp("2023-09-30"),
        pd.Timestamp("2022-09-30"),
    ]
    return pd.DataFrame(
        {
            columns[0]: {"Total Revenue": 391035000000.0, "Net Income": 93736000000.0},
            columns[1]: {"Total Revenue": 383285000000.0, "Net Income": 96995000000.0},
            columns[2]: {"Total Revenue": float("nan"), "Net Income": float("nan")},
        }
    )


def make_mock_ticker(
    financials: pd.DataFrame | None = None,
    info: dict | None = None,
) -> MagicMock:
    mock_ticker = MagicMock()
    mock_ticker.financials = (
        financials if financials is not None else make_financials_frame()
    )
    mock_ticker.info = info if info is not None else {
        "currency": "USD",
        "longName": "Apple Inc.",
    }
    return mock_ticker


def test_resolve_metric_row_matches_known_keywords() -> None:
    """Free-text metric descriptions should map to a statement row."""

    tool = FinancialDataTool()

    assert tool.resolve_metric_row("FY2024 revenue in USD billions") == "Total Revenue"
    assert tool.resolve_metric_row("Total Revenue") == "Total Revenue"
    assert tool.resolve_metric_row("Net Income for FY2023") == "Net Income"


def test_resolve_metric_row_rejects_unsupported_metric() -> None:
    """An unrecognized metric should not silently match anything."""

    tool = FinancialDataTool()

    assert tool.resolve_metric_row("qualified research conclusion") is None


def test_fetch_metric_returns_normalized_value() -> None:
    """A valid lookup should return billions-normalized values."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(),
    ):
        result = tool.fetch_metric("AAPL", "FY2024 total revenue in USD billions", 0)

    assert result is not None
    assert result.ticker == "AAPL"
    assert result.company_name == "Apple Inc."
    assert result.metric_name == "Total Revenue"
    assert result.value == Decimal("391.035")
    assert result.unit == "billion"
    assert result.currency == "USD"
    assert result.fiscal_period_end == date(2024, 9, 30)
    assert result.source_url == "https://finance.yahoo.com/quote/AAPL/financials"


def test_fetch_metric_period_offset_selects_prior_year() -> None:
    """A period_offset of 1 should select the year before the most recent."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(),
    ):
        result = tool.fetch_metric("AAPL", "revenue", 1)

    assert result is not None
    assert result.value == Decimal("383.285")
    assert result.fiscal_period_end == date(2023, 9, 30)


def test_fetch_metric_returns_none_for_unrecognized_metric() -> None:
    """An unsupported metric name should return None, not raise."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(),
    ):
        result = tool.fetch_metric("AAPL", "market sentiment", 0)

    assert result is None


def test_fetch_metric_returns_none_for_out_of_range_offset() -> None:
    """An offset beyond the available (non-NaN) history should return None."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(),
    ):
        result = tool.fetch_metric("AAPL", "revenue", 5)

    assert result is None


def test_fetch_metric_returns_none_for_negative_offset() -> None:
    """A negative offset is not a valid request."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(),
    ):
        result = tool.fetch_metric("AAPL", "revenue", -1)

    assert result is None


def test_fetch_metric_returns_none_when_row_missing() -> None:
    """A metric yfinance doesn't report for this ticker should return None."""

    tool = FinancialDataTool()
    frame = make_financials_frame().drop(index="Net Income")

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(financials=frame),
    ):
        result = tool.fetch_metric("AAPL", "net income", 0)

    assert result is None


def test_fetch_metric_returns_none_on_empty_financials() -> None:
    """An empty financials frame (e.g. invalid ticker) should return None."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(financials=pd.DataFrame()),
    ):
        result = tool.fetch_metric("NOTATICKER", "revenue", 0)

    assert result is None


def test_fetch_metric_returns_none_on_library_error() -> None:
    """A yfinance/network failure should be treated as no data, not a crash."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        side_effect=RuntimeError("network unreachable"),
    ):
        result = tool.fetch_metric("AAPL", "revenue", 0)

    assert result is None


def test_fetch_metric_defaults_currency_when_missing() -> None:
    """A missing currency field should fall back to USD."""

    tool = FinancialDataTool()

    with patch(
        "fin_automation.tools.financial_data.yf.Ticker",
        return_value=make_mock_ticker(info={}),
    ):
        result = tool.fetch_metric("AAPL", "revenue", 0)

    assert result is not None
    assert result.currency == "USD"
    assert result.company_name == "AAPL"
