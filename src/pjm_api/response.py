"""OASIS response wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pjm_api.exceptions import PJMOasisError


@dataclass(frozen=True)
class OasisResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes
    template: str
    environment: str
    output_format: str | None = None

    def text(self, encoding: str = "utf-8") -> str:
        return self.content.decode(encoding, errors="replace")

    def json(self) -> Any:
        try:
            return json.loads(self.content.decode())
        except json.JSONDecodeError as exc:
            raise PJMOasisError(f"Response is not valid JSON: {exc}") from exc

    def save(self, path: Path | str) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.content)
        return target

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300
