"""Local, offline-first incident storage (one JSON file per incident, atomic writes)."""
from __future__ import annotations
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import config
from . import chain as chainmod

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def valid_id(incident_id: str) -> bool:
    return bool(incident_id and _ID_RE.match(incident_id))


class IncidentStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base or config.INCIDENT_DIR)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, incident_id: str) -> Path:
        if not valid_id(incident_id):
            raise ValueError("Invalid incident id")
        return self.base / f"{incident_id}.json"

    def new_id(self) -> str:
        return "INC-" + datetime.now().strftime("%Y%m%d-%H%M%S")

    def create(self, incident_id=None, responder="unknown", patient_label="Unknown patient",
               incident_date=None) -> dict:
        incident_id = incident_id or self.new_id()
        if self._path(incident_id).exists():
            return self.load(incident_id)
        inc = {"incident_id": incident_id, "responder": responder, "patient_label": patient_label,
               "incident_date": incident_date or datetime.now().strftime("%Y-%m-%d"),
               "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "chain": [], "synced": False, "sync_log": []}
        self.save(inc)
        return inc

    def load(self, incident_id: str) -> dict:
        with open(self._path(incident_id), encoding="utf-8") as f:
            return json.load(f)

    def save(self, inc: dict) -> None:
        path = self._path(inc["incident_id"])
        fd, tmp = tempfile.mkstemp(dir=self.base, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inc, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    def append_entries(self, incident_id: str, payloads: list[dict]) -> dict:
        inc = self.load(incident_id)
        for p in payloads:
            chainmod.append(inc["chain"], p)
        inc["synced"] = False
        self.save(inc)
        return inc

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.base.glob("*.json"))
