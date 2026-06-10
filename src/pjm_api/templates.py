"""Template catalog metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any, cast


@dataclass(frozen=True)
class TemplateInfo:
    name: str
    type: str
    supported_methods: tuple[str, ...]
    description: str
    common_params: dict[str, str]
    pjm_custom: bool
    naesb_version_default: str = "3.3"


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    data = files("pjm_api.data").joinpath("template_catalog.json").read_text(encoding="utf-8")
    return cast(dict[str, Any], json.loads(data))


def list_templates(*, pjm_custom_only: bool = False) -> list[TemplateInfo]:
    catalog = _load_catalog()
    version = catalog.get("naesb_version_default", "3.3")
    results: list[TemplateInfo] = []
    for entry in catalog.get("templates", []):
        if pjm_custom_only and not entry.get("pjm_custom"):
            continue
        results.append(
            TemplateInfo(
                name=entry["name"],
                type=entry["type"],
                supported_methods=tuple(entry.get("supported_methods", ["GET"])),
                description=entry.get("description", ""),
                common_params=dict(entry.get("common_params", {})),
                pjm_custom=entry.get("pjm_custom", False),
                naesb_version_default=version,
            )
        )
    return results


def get_template_info(name: str) -> TemplateInfo | None:
    normalized = (name or "").strip().upper()
    for info in list_templates():
        if info.name.upper() == normalized:
            return info
    return None


def suggest_params(template: str) -> dict[str, str]:
    info = get_template_info(template)
    return dict(info.common_params) if info else {}
