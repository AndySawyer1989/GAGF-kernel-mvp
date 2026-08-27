from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.diagnostic_calibration_scenario import (
    DiagnosticCalibrationScenarioBundle,
    DiagnosticCalibrationScenarioService,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


DIAGNOSTIC_CALIBRATION_CORPUS_VERSION = "1.0.0"

PUBLIC_SCENARIO_FILENAME = (
    "public_scenario.json"
)

SEALED_ORACLE_FILENAME = (
    "sealed_oracle.json"
)

CALIBRATION_MANIFEST_FILENAME = (
    "manifest.json"
)


class DiagnosticCalibrationCorpusError(
    RuntimeError
):
    """
    Raised when a sealed calibration corpus package cannot
    be written or verified deterministically.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticCalibrationCorpusManifest:
    scenario_id: str

    public_scenario_filename: str
    sealed_oracle_filename: str

    public_hash: str
    oracle_hash: str
    bundle_hash: str

    manifest_hash: str

    schema_version: str = (
        DIAGNOSTIC_CALIBRATION_CORPUS_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "public_scenario_filename":
                self.public_scenario_filename,

            "sealed_oracle_filename":
                self.sealed_oracle_filename,

            "public_hash":
                self.public_hash,

            "oracle_hash":
                self.oracle_hash,

            "bundle_hash":
                self.bundle_hash,

            "manifest_hash":
                self.manifest_hash,

            "schema_version":
                self.schema_version,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticCalibrationCorpusWriteResult:
    scenario_id: str

    scenario_directory: str

    public_scenario_path: str
    sealed_oracle_path: str
    manifest_path: str

    manifest: (
        DiagnosticCalibrationCorpusManifest
    )

    reused_existing: bool

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "scenario_directory":
                self.scenario_directory,

            "public_scenario_path":
                self.public_scenario_path,

            "sealed_oracle_path":
                self.sealed_oracle_path,

            "manifest_path":
                self.manifest_path,

            "manifest":
                self.manifest.to_dict(),

            "reused_existing":
                self.reused_existing,
        }


class DiagnosticCalibrationCorpusService:
    """
    Write a sealed calibration scenario bundle to disk.

    Package structure:

        <root>/<scenario_id>/
            public_scenario.json
            sealed_oracle.json
            manifest.json

    public_scenario.json may cross into evidence generation.

    sealed_oracle.json is calibration-only and must remain
    isolated from diagnostic execution.
    """

    def __init__(
        self,
        *,
        scenario_service: (
            DiagnosticCalibrationScenarioService
            | None
        ) = None,
    ) -> None:
        self._scenario_service = (
            scenario_service
            or
            DiagnosticCalibrationScenarioService()
        )

    def write_bundle(
        self,
        *,
        bundle: (
            DiagnosticCalibrationScenarioBundle
        ),
        corpus_root: str | Path,
    ) -> DiagnosticCalibrationCorpusWriteResult:
        if (
            self._scenario_service
            .verify_bundle(
                bundle=bundle
            )
            is not True
        ):
            raise (
                DiagnosticCalibrationCorpusError(
                    "Calibration scenario bundle "
                    "failed deterministic verification."
                )
            )

        scenario_id = (
            bundle
            .public_scenario
            .scenario_id
        )

        if (
            scenario_id
            != bundle.oracle.scenario_id
        ):
            raise (
                DiagnosticCalibrationCorpusError(
                    "Public scenario and oracle "
                    "scenario_id values do not match."
                )
            )

        root = Path(
            corpus_root
        )

        scenario_directory = (
            root
            / scenario_id
        )

        scenario_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        public_path = (
            scenario_directory
            / PUBLIC_SCENARIO_FILENAME
        )

        oracle_path = (
            scenario_directory
            / SEALED_ORACLE_FILENAME
        )

        manifest_path = (
            scenario_directory
            / CALIBRATION_MANIFEST_FILENAME
        )

        public_payload = (
            bundle
            .public_scenario
            .to_dict()
        )

        oracle_payload = (
            bundle
            .oracle
            .to_dict()
        )

        manifest = (
            self._build_manifest(
                bundle=bundle
            )
        )

        manifest_payload = (
            manifest.to_dict()
        )

        expected = (
            (
                public_path,
                public_payload,
            ),
            (
                oracle_path,
                oracle_payload,
            ),
            (
                manifest_path,
                manifest_payload,
            ),
        )

        existing_count = sum(
            path.exists()
            for path, _
            in expected
        )

        if (
            existing_count
            not in (
                0,
                len(
                    expected
                ),
            )
        ):
            raise (
                DiagnosticCalibrationCorpusError(
                    "Calibration package is partially "
                    "present and cannot be reused safely."
                )
            )

        if (
            existing_count
            ==
            len(
                expected
            )
        ):
            for path, payload in expected:
                existing_payload = (
                    self._read_json(
                        path
                    )
                )

                if canonical_json(
                    existing_payload
                ) != canonical_json(
                    payload
                ):
                    raise (
                        DiagnosticCalibrationCorpusError(
                            "Existing calibration package "
                            "does not match deterministic "
                            f"content: {path}"
                        )
                    )

            reused_existing = True

        else:
            for path, payload in expected:
                self._write_json(
                    path=path,
                    payload=payload,
                )

            reused_existing = False

        if (
            self.verify_package(
                scenario_directory=(
                    scenario_directory
                )
            )
            is not True
        ):
            raise (
                DiagnosticCalibrationCorpusError(
                    "Calibration package failed "
                    "post-write verification."
                )
            )

        return (
            DiagnosticCalibrationCorpusWriteResult(
                scenario_id=(
                    scenario_id
                ),

                scenario_directory=str(
                    scenario_directory
                ),

                public_scenario_path=str(
                    public_path
                ),

                sealed_oracle_path=str(
                    oracle_path
                ),

                manifest_path=str(
                    manifest_path
                ),

                manifest=(
                    manifest
                ),

                reused_existing=(
                    reused_existing
                ),
            )
        )

    def verify_package(
        self,
        *,
        scenario_directory: str | Path,
    ) -> bool:
        directory = Path(
            scenario_directory
        )

        public_path = (
            directory
            / PUBLIC_SCENARIO_FILENAME
        )

        oracle_path = (
            directory
            / SEALED_ORACLE_FILENAME
        )

        manifest_path = (
            directory
            / CALIBRATION_MANIFEST_FILENAME
        )

        if not all(
            path.is_file()
            for path
            in (
                public_path,
                oracle_path,
                manifest_path,
            )
        ):
            return False

        try:
            public_payload = (
                self._read_json(
                    public_path
                )
            )

            oracle_payload = (
                self._read_json(
                    oracle_path
                )
            )

            manifest_payload = (
                self._read_json(
                    manifest_path
                )
            )

        except (
            DiagnosticCalibrationCorpusError
        ):
            return False

        scenario_id = (
            public_payload.get(
                "scenario_id"
            )
        )

        if (
            not isinstance(
                scenario_id,
                str,
            )
            or not scenario_id
        ):
            return False

        if (
            oracle_payload.get(
                "scenario_id"
            )
            != scenario_id
        ):
            return False

        if (
            manifest_payload.get(
                "scenario_id"
            )
            != scenario_id
        ):
            return False

        public_hash = (
            public_payload.get(
                "public_hash"
            )
        )

        oracle_hash = (
            oracle_payload.get(
                "oracle_hash"
            )
        )

        bundle_hash = (
            manifest_payload.get(
                "bundle_hash"
            )
        )

        if (
            manifest_payload.get(
                "public_hash"
            )
            != public_hash
        ):
            return False

        if (
            manifest_payload.get(
                "oracle_hash"
            )
            != oracle_hash
        ):
            return False

        if not isinstance(
            bundle_hash,
            str,
        ):
            return False

        manifest_hash = (
            manifest_payload.get(
                "manifest_hash"
            )
        )

        if not isinstance(
            manifest_hash,
            str,
        ):
            return False

        manifest_hash_payload = dict(
            manifest_payload
        )

        manifest_hash_payload.pop(
            "manifest_hash",
            None,
        )

        expected_manifest_hash = (
            sha256_text(
                canonical_json(
                    manifest_hash_payload
                )
            )
        )

        return (
            expected_manifest_hash
            == manifest_hash
        )

    def _build_manifest(
        self,
        *,
        bundle: (
            DiagnosticCalibrationScenarioBundle
        ),
    ) -> DiagnosticCalibrationCorpusManifest:
        payload = {
            "scenario_id":
                bundle
                .public_scenario
                .scenario_id,

            "public_scenario_filename":
                PUBLIC_SCENARIO_FILENAME,

            "sealed_oracle_filename":
                SEALED_ORACLE_FILENAME,

            "public_hash":
                bundle
                .public_scenario
                .public_hash,

            "oracle_hash":
                bundle
                .oracle
                .oracle_hash,

            "bundle_hash":
                bundle
                .bundle_hash,

            "schema_version":
                DIAGNOSTIC_CALIBRATION_CORPUS_VERSION,
        }

        manifest_hash = (
            sha256_text(
                canonical_json(
                    payload
                )
            )
        )

        return (
            DiagnosticCalibrationCorpusManifest(
                scenario_id=(
                    bundle
                    .public_scenario
                    .scenario_id
                ),

                public_scenario_filename=(
                    PUBLIC_SCENARIO_FILENAME
                ),

                sealed_oracle_filename=(
                    SEALED_ORACLE_FILENAME
                ),

                public_hash=(
                    bundle
                    .public_scenario
                    .public_hash
                ),

                oracle_hash=(
                    bundle
                    .oracle
                    .oracle_hash
                ),

                bundle_hash=(
                    bundle
                    .bundle_hash
                ),

                manifest_hash=(
                    manifest_hash
                ),
            )
        )

    def _write_json(
        self,
        *,
        path: Path,
        payload: Mapping[
            str,
            Any,
        ],
    ) -> None:
        path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                DiagnosticCalibrationCorpusError(
                    "Calibration package file "
                    f"does not exist: {path}"
                )
            )

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise (
                DiagnosticCalibrationCorpusError(
                    "Unable to read calibration "
                    f"package file: {path}"
                )
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise (
                DiagnosticCalibrationCorpusError(
                    "Calibration package file must "
                    f"contain a JSON object: {path}"
                )
            )

        return payload