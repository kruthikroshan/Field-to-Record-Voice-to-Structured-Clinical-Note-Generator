"""Command line interface:  python -m fieldscribe.cli <command>"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from . import asr, chain as chainmod
from .fhir import to_fhir_bundle
from .ner import parse_note
from .pdfgen import build_pdf
from .pipeline import record_note
from .store import IncidentStore

DEMO = ("Started an IV at 10:40. Gave epi 1 mg IV at 10:42, aspirin 324 mg PO at 10:44. "
        "Defibrillated 200 J at 10:46. Gave 500 ml normal saline IV at 10:50.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fieldscribe")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse", help="extract entries from text and print JSON")
    p.add_argument("text")
    p = sub.add_parser("record", help="parse text and append to an incident's audit chain")
    p.add_argument("incident_id"); p.add_argument("text")
    p = sub.add_parser("transcribe", help="offline ASR on an audio file (needs faster-whisper or vosk)")
    p.add_argument("audio")
    p = sub.add_parser("verify", help="verify an incident's hash chain")
    p.add_argument("incident_id")
    p = sub.add_parser("export", help="write FHIR JSON and PDF for an incident")
    p.add_argument("incident_id"); p.add_argument("--out", default=".")
    sub.add_parser("demo", help="run an end-to-end demo and write outputs to ./demo_output")
    a = ap.parse_args(argv)
    store = IncidentStore()

    if a.cmd == "parse":
        print(json.dumps(parse_note(a.text).to_dict(), indent=2))
    elif a.cmd == "record":
        store.create(a.incident_id)
        inc = record_note(store, a.incident_id, a.text)
        print(f"{a.incident_id}: {len(inc['chain'])} chained entries, head {inc['chain'][-1]['hash'][:16]}...")
    elif a.cmd == "transcribe":
        try:
            print(asr.transcribe(a.audio))
        except asr.AsrUnavailable as exc:
            print(exc, file=sys.stderr); return 2
    elif a.cmd == "verify":
        ok, bad = chainmod.verify(store.load(a.incident_id)["chain"])
        print("VERIFIED" if ok else f"TAMPERED at entry index {bad}")
        return 0 if ok else 1
    elif a.cmd == "export":
        inc = store.load(a.incident_id); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / f"{a.incident_id}.fhir.json").write_text(json.dumps(to_fhir_bundle(inc), indent=2))
        (out / f"{a.incident_id}.pdf").write_bytes(build_pdf(inc))
        print(f"Wrote {out / (a.incident_id + '.fhir.json')} and {out / (a.incident_id + '.pdf')}")
    elif a.cmd == "demo":
        out = Path("demo_output"); out.mkdir(exist_ok=True)
        store = IncidentStore(out / "incidents")
        store.create("DEMO-001", responder="Medic 12", patient_label="Patient A", incident_date="2026-10-26")
        inc = record_note(store, "DEMO-001", DEMO, auto_confirm=True)
        (out / "DEMO-001.fhir.json").write_text(json.dumps(to_fhir_bundle(inc), indent=2))
        (out / "DEMO-001.pdf").write_bytes(build_pdf(inc))
        print(f"Parsed {len(inc['chain'])} entries. Chain verified: {chainmod.verify(inc['chain'])[0]}")
        print(f"Wrote {out}/DEMO-001.fhir.json and {out}/DEMO-001.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
