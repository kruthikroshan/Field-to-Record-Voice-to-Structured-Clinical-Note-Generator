"""Flask web UI + JSON API. No external CDN or font calls: works with the network unplugged."""
from __future__ import annotations
import json
import tempfile
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, Response, abort

from .. import config, chain as chainmod, asr
from ..fhir import to_fhir_bundle
from ..ner import parse_note
from ..pdfgen import build_pdf
from ..pipeline import entry_to_payload
from ..store import IncidentStore, valid_id
from ..sync import sync_incident


def create_app(data_dir: Path | None = None) -> Flask:
    app = Flask(__name__)
    store = IncidentStore((Path(data_dir) / "incidents") if data_dir else None)
    mock_dir = (Path(data_dir) / "mock_ehr") if data_dir else config.MOCK_EHR_DIR
    mock_dir.mkdir(parents=True, exist_ok=True)

    def get_incident(incident_id):
        if not valid_id(incident_id):
            abort(400, "invalid incident id")
        try:
            return store.load(incident_id)
        except FileNotFoundError:
            abort(404, "incident not found")

    @app.get("/")
    def index():
        return render_template("index.html", asr_backends=asr.available_backends())

    @app.post("/api/parse")
    def api_parse():
        text = (request.get_json(silent=True) or {}).get("text", "")
        if not text.strip():
            return jsonify(error="Empty note"), 400
        return jsonify(parse_note(text).to_dict())

    @app.post("/api/transcribe")
    def api_transcribe():
        f = request.files.get("audio")
        if not f:
            return jsonify(error="No audio file"), 400
        suffix = Path(f.filename or "a.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
        f.save(tmp_path)
        try:
            return jsonify(text=asr.transcribe(tmp_path))
        except asr.AsrUnavailable as exc:
            return jsonify(error=str(exc)), 501
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @app.post("/api/commit")
    def api_commit():
        body = request.get_json(silent=True) or {}
        entries = body.get("entries") or []
        if not entries:
            return jsonify(error="Nothing to commit"), 400
        iid = body.get("incident_id") or store.new_id()
        if not valid_id(iid):
            return jsonify(error="Invalid incident id"), 400
        store.create(iid, responder=(body.get("responder") or "unknown")[:60],
                     patient_label=(body.get("patient_label") or "Unknown patient")[:60])
        payloads = [entry_to_payload(e, confirmed=True, edited=bool(e.get("edited"))) for e in entries]
        inc = store.append_entries(iid, payloads)
        ok, bad = chainmod.verify(inc["chain"])
        return jsonify(incident=inc, chain_ok=ok)

    @app.get("/api/incident/<incident_id>")
    def api_incident(incident_id):
        inc = get_incident(incident_id)
        ok, bad = chainmod.verify(inc["chain"])
        return jsonify(incident=inc, chain_ok=ok, first_bad_index=bad)

    @app.get("/api/incident/<incident_id>/fhir")
    def api_fhir(incident_id):
        return Response(json.dumps(to_fhir_bundle(get_incident(incident_id)), indent=2),
                        mimetype="application/fhir+json")

    @app.get("/incident/<incident_id>.pdf")
    def pdf(incident_id):
        return Response(build_pdf(get_incident(incident_id)), mimetype="application/pdf",
                        headers={"Content-Disposition": f"inline; filename={incident_id}.pdf"})

    @app.post("/api/sync/<incident_id>")
    def api_sync(incident_id):
        inc = get_incident(incident_id)
        url = (request.get_json(silent=True) or {}).get("url") or config.SYNC_URL
        if url == "mock":   # demo target: this server's own mock hospital endpoint
            url = request.host_url.rstrip("/") + "/api/mock-ehr"
        ok, msg = sync_incident(inc, url)
        inc["synced"] = ok or inc.get("synced", False)
        inc["sync_log"].append(msg)
        store.save(inc)
        return jsonify(ok=ok, message=msg)

    @app.post("/api/mock-ehr")
    def mock_ehr():
        bundle = request.get_json(silent=True, force=True) or {}
        (mock_dir / f"{bundle.get('id', 'bundle')}.json").write_text(json.dumps(bundle, indent=2))
        return jsonify(status="received", entries=len(bundle.get("entry", [])))

    return app
