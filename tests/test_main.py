"""Tests for the application entry point's failure handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fin_automation.exceptions import WorkflowError
from fin_automation.main import main


def _fake_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.output_directory = tmp_path
    settings.openai_api_key.get_secret_value.return_value = "sk-test"
    settings.tavily_api_key.get_secret_value.return_value = "tvly-test"
    return settings


def test_unrecoverable_workflow_error_exits_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unrecoverable failure must print a clear message and exit
    with a non-zero status, rather than propagate as an unhandled
    traceback."""

    with (
        patch("fin_automation.main.get_settings", return_value=_fake_settings(tmp_path)),
        patch("fin_automation.main.configure_logging"),
        patch("builtins.input", return_value="Research Example Inc"),
        patch("fin_automation.main.ResearchOrchestrator") as mock_orchestrator_cls,
    ):
        mock_orchestrator_cls.return_value.run.side_effect = WorkflowError(
            "Source selection failed after 3 attempts."
        )

        with pytest.raises(SystemExit) as exit_info:
            main()

    assert exit_info.value.code == 1
    output = capsys.readouterr().out
    assert "unrecoverable error" in output
    assert "Source selection failed after 3 attempts." in output
