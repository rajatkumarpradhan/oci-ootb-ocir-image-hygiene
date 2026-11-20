"""Data model + export loading for the OCIR hygiene audit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime


class ExportError(ValueError):
    """Raised when an export file is malformed."""


STALE_LATEST_DAYS = 180
PROD_LIKE_TAGS = {"prod", "production", "release", "stable"}


def parse_date(value: str, what: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ExportError(f"invalid date for {what}: {value!r} (expected YYYY-MM-DD)") from exc


@dataclass(frozen=True)
class Image:
    tag: str
    pushed_at: date

    def is_prod_like(self) -> bool:
        return self.tag.lower() in PROD_LIKE_TAGS

    def age_days(self, as_of: date) -> int:
        return (as_of - self.pushed_at).days


@dataclass(frozen=True)
class Repo:
    name: str
    is_public: bool
    images: tuple = ()


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("repos"), list):
        raise ExportError(f"{path}: top level must be an object with a 'repos' list")
    out = []
    for i, r in enumerate(raw["repos"]):
        where = f"repos[{i}]"
        if "name" not in r:
            raise ExportError(f"{where}: missing required field 'name'")
        images = []
        for j, im in enumerate(r.get("images", [])):
            iwhere = f"{where}.images[{j}]"
            for req in ("tag", "pushed_at"):
                if req not in im:
                    raise ExportError(f"{iwhere}: missing required field {req!r}")
            images.append(Image(tag=im["tag"], pushed_at=parse_date(im["pushed_at"], f"{iwhere}.pushed_at")))
        out.append(Repo(name=r["name"], is_public=bool(r.get("is_public", False)), images=tuple(images)))
    return tuple(out)
