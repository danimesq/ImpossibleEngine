"""JSON project persistence."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Project


def save_project(project: Project, path: str | Path) -> None:
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(project.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_project(path: str | Path) -> Project:
    source = Path(path).expanduser()
    return Project.from_dict(json.loads(source.read_text(encoding="utf-8")))
