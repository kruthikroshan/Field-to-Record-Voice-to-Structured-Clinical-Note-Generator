"""Store-and-forward sync: push the FHIR-lite bundle to a hospital endpoint when online."""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone

from .fhir import to_fhir_bundle


def sync_incident(incident: dict, url: str | None, timeout: float = 5.0) -> tuple[bool, str]:
    """Return (ok, message). Never raises on network failure: the record just stays queued."""
    if not url:
        return False, "No sync endpoint configured; incident stays queued on this device."
    body = json.dumps(to_fhir_bundle(incident)).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/fhir+json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ok = 200 <= resp.status < 300
        msg = f"Synced at {datetime.now(timezone.utc).isoformat(timespec='seconds')}" if ok else "Server rejected bundle"
        return ok, msg
    except Exception as exc:  # offline, DNS failure, refused, timeout...
        return False, f"Offline or unreachable ({type(exc).__name__}); will retry later."
