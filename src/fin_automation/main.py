"""Application entry point for the current research workflow."""

from fin_automation.config import get_settings
from fin_automation.logging_config import (
    configure_logging,
    next_available_log_path,
)
from fin_automation.workflow.orchestrator import ResearchOrchestrator


def main() -> None:
    """Prompt for a research request and hand it to the orchestrator."""

    settings = get_settings()
    log_directory = settings.output_directory / "logs"
    log_file = next_available_log_path(log_directory)
    configure_logging(
        secrets=[
            settings.openai_api_key.get_secret_value(),
            settings.tavily_api_key.get_secret_value(),
        ],
        log_file=log_file,
    )
    print(f"Logging this run to: {log_file}")

    raw_user_req = input("Enter a research request: ").strip()

    if not raw_user_req:
        raise ValueError("Research request cannot be empty.")

    orchestrator = ResearchOrchestrator()
    research_plan, source_selection = orchestrator.run(raw_user_req)

    print("Research plan:")
    print(research_plan.model_dump_json(indent=2))
    print("\nSource selection:")
    print(source_selection.model_dump_json(indent=2))

    validation_result = orchestrator.last_validation_result
    report_artifact = orchestrator.last_report_artifact

    print("\n=== Workflow outcome ===")

    if report_artifact is not None:
        print(
            "A Markdown research report was written to: "
            f"{report_artifact.relative_path}"
        )
        print(
            "This report is informational only. The final investment "
            "decision remains with the human reviewer."
        )
    elif validation_result is not None:
        print(
            "No report was written. Validation outcome: "
            f"{validation_result.outcome.value}"
        )
        print(f"Summary: {validation_result.summary}")
        for finding in validation_result.findings:
            print(
                f"- [{finding.severity.value}] {finding.category.value}: "
                f"{finding.description}"
            )
    else:
        print(
            "The workflow stopped before evidence validation completed. "
            "Check the logged steps above for the stage that did not "
            "produce a usable result."
        )


if __name__ == "__main__":
    main()