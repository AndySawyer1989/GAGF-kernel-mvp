import copy
from pathlib import Path
from typing import Any, Dict

import yaml


class GPLLoader:
    def __init__(self, policy_path: str):
        self._policy_path = Path(policy_path)
        self._manifest = self._load_and_validate()

    def _load_and_validate(self) -> Dict[str, Any]:
        with open(self._policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data.get("policy_version") != "0.1":
            raise ValueError("Unsupported policy version")

        if data.get("mode") != "declarative":
            raise ValueError("GPL policy must be declarative")

        return data

    @property
    def manifest(self) -> Dict[str, Any]:
        return copy.deepcopy(self._manifest)

    @property
    def version(self) -> str:
        return self._manifest["policy_version"]

    @property
    def policy_id(self) -> str:
        return self._manifest["policy_id"]