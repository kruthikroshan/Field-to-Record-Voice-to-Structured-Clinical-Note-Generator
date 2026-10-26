"""Tamper-evident, hash-linked audit chain (the 'first link in an audit chain')."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone

GENESIS = "0" * 64


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def link_hash(prev_hash: str, index: int, recorded_at: str, payload: dict) -> str:
    body = f"{prev_hash}|{index}|{recorded_at}|{canonical(payload)}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def append(chain: list, payload: dict, now: str | None = None) -> dict:
    prev = chain[-1]["hash"] if chain else GENESIS
    idx = len(chain)
    ts = now or datetime.now(timezone.utc).isoformat(timespec="seconds")
    link = {"index": idx, "recorded_at": ts, "payload": payload, "prev_hash": prev,
            "hash": link_hash(prev, idx, ts, payload)}
    chain.append(link)
    return link


def verify(chain: list) -> tuple[bool, int | None]:
    """Return (ok, first_bad_index)."""
    prev = GENESIS
    for i, link in enumerate(chain):
        if link.get("index") != i or link.get("prev_hash") != prev:
            return False, i
        if link_hash(prev, i, link["recorded_at"], link["payload"]) != link.get("hash"):
            return False, i
        prev = link["hash"]
    return True, None
