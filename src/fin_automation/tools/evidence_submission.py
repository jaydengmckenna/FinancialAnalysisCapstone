"""Structured submission tool for extracted evidence."""

from collections.abc import Mapping
from uuid import UUID

from pydantic import ValidationError
from smolagents import Tool

from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import ExtractedEvidence, SourceRecord


class SubmitExtractedEvidenceTool(Tool):
    """Validate and store evidence extracted by the agent."""

    name = "submit_extracted_evidence"

    description = """
    Submit all evidence extracted from the supplied source.

    Use payload.evidence_records for proposed ExtractedEvidence records and
    payload.evidence_gaps for approved evidence needs that the source did not
    satisfy.

    Do not generate evidence_id, workflow_id, or source_id. The application
    attaches those authoritative fields. Every submitted evidence record must
    use an approved evidence_requirement_id.
    """.strip()

    inputs = {
        "payload": {
            "type": "object",
            "description": (
                "Object containing evidence_records and evidence_gaps."
            ),
        },
    }

    output_type = "string"

    def __init__(self) -> None:
        """Initialize an unconfigured submission tool."""

        self._source_record: SourceRecord | None = None
        self._requirements_by_id: dict[UUID, EvidenceRequirement] = {}
        self._accepted_evidence: list[ExtractedEvidence] = []
        self._evidence_gaps: list[str] = []
        super().__init__()

    @property
    def accepted_evidence(self) -> list[ExtractedEvidence]:
        """Return evidence accepted during the current run."""

        return list(self._accepted_evidence)

    @property
    def evidence_gaps(self) -> list[str]:
        """Return evidence gaps submitted during the current run."""

        return list(self._evidence_gaps)

    def begin_run(
        self,
        source_record: SourceRecord,
        evidence_requirements: list[EvidenceRequirement],
    ) -> None:
        """Configure authoritative context for one extraction run."""

        self._source_record = source_record
        self._requirements_by_id = {
            requirement.requirement_id: requirement
            for requirement in evidence_requirements
        }
        self._accepted_evidence = []
        self._evidence_gaps = []

    def forward(self, payload: dict[str, object]) -> str:
        """Validate and store submitted evidence records."""

        if self._source_record is None:
            raise ValueError(
                "Evidence submission was not configured for a source."
            )

        raw_records = payload.get("evidence_records", [])
        raw_gaps = payload.get("evidence_gaps", [])

        if not isinstance(raw_records, list):
            raise ValueError("evidence_records must be a list.")

        if not isinstance(raw_gaps, list) or not all(
            isinstance(gap, str) and gap.strip()
            for gap in raw_gaps
        ):
            raise ValueError("evidence_gaps must be a list of nonempty strings.")

        accepted: list[ExtractedEvidence] = []
        allowed_candidates = {
            candidate.casefold()
            for candidate in self._source_record.candidate_names
        }

        for raw_record in raw_records:
            if not isinstance(raw_record, Mapping):
                raise ValueError("Each evidence record must be an object.")

            record = dict(raw_record)
            record.pop("evidence_id", None)
            record.pop("workflow_id", None)
            record.pop("source_id", None)

            raw_requirement_id = record.get("evidence_requirement_id")

            try:
                requirement_id = UUID(str(raw_requirement_id))
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "Every evidence record must include a valid "
                    "evidence_requirement_id."
                ) from error

            if requirement_id not in self._requirements_by_id:
                raise ValueError(
                    "An evidence record references an evidence requirement "
                    "outside the approved extraction scope."
                )

            candidate_name = record.get("candidate_name")

            if candidate_name is None and len(self._source_record.candidate_names) == 1:
                record["candidate_name"] = self._source_record.candidate_names[0]
                candidate_name = record["candidate_name"]

            if (
                isinstance(candidate_name, str)
                and allowed_candidates
                and candidate_name.casefold() not in allowed_candidates
            ):
                raise ValueError(
                    "An evidence record references a candidate outside the "
                    "source record."
                )

            record.update(
                {
                    "workflow_id": self._source_record.workflow_id,
                    "source_id": self._source_record.source_id,
                    "evidence_requirement_id": requirement_id,
                }
            )

            try:
                evidence = ExtractedEvidence.model_validate(record)
            except ValidationError as error:
                raise ValueError(
                    "Submitted evidence does not satisfy the "
                    f"ExtractedEvidence contract: {error}"
                ) from error

            accepted.append(evidence)

        self._accepted_evidence = accepted
        self._evidence_gaps = [gap.strip() for gap in raw_gaps]

        return (
            "Extracted evidence accepted. "
            f"Records: {len(accepted)}. "
            f"Evidence gaps: {len(self._evidence_gaps)}."
        )
