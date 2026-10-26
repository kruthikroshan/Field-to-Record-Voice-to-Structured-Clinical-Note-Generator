"""High-level API used by the CLI and web app."""
from __future__ import annotations

from .models import Entry
from .ner import parse_note
from .store import IncidentStore


def entry_to_payload(e: dict, confirmed: bool = True, edited: bool = False) -> dict:
    keys = ["kind", "name", "dose_value", "dose_unit", "route", "time", "details", "source_text",
            "confidence", "flags"]
    p = {k: e.get(k) for k in keys}
    p["details"] = p.get("details") or {}
    p["flags"] = list(p.get("flags") or [])
    p["confirmed"] = confirmed
    p["edited"] = edited
    return p


def record_note(store: IncidentStore, incident_id: str, text: str, auto_confirm: bool = False) -> dict:
    """Parse a note and append ALL entries to the chain (CLI shortcut; the web UI confirms first)."""
    res = parse_note(text)
    payloads = [entry_to_payload(e.to_dict(), confirmed=auto_confirm) for e in res.entries]
    return store.append_entries(incident_id, payloads)
