"""Convenience script to run and capture the real end-to-end workflow."""

from datetime import datetime
from pathlib import Path
import sys
import traceback

from fin_automation.main import main


class _Tee:
    """Write console output to both the terminal and a log file."""

    def __init__(self, log_file) -> None:
        self.log_file = log_file

    def write(self, text: str) -> int:
        sys.__stdout__.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        return len(text)

    def flush(self) -> None:
        sys.__stdout__.flush()
        self.log_file.flush()


if __name__ == "__main__":
    output_directory = Path(__file__).parent / "outputs"
    output_directory.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_directory / f"smoke_test_{timestamp}.txt"

    with output_path.open("w", encoding="utf-8") as log_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = _Tee(log_file)
        sys.stderr = _Tee(log_file)
        try:
            print(f"Smoke-test output: {output_path}")
            main()
        except BaseException:
            traceback.print_exc()
            raise
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"Smoke-test output saved to {output_path}")
