import json
from fieldscribe.web.app import create_app


def client(tmp_path):
    return create_app(tmp_path).test_client()


def test_parse_commit_verify_export(tmp_path):
    c = client(tmp_path)
    r = c.post("/api/parse", json={"text": "Gave epi 1 mg IV at 10:42"})
    entries = r.get_json()["entries"]
    assert entries[0]["name"] == "Epinephrine"
    r = c.post("/api/commit", json={"incident_id": "WEB-1", "responder": "M1", "patient_label": "P", "entries": entries})
    assert r.get_json()["chain_ok"] is True
    assert c.get("/api/incident/WEB-1").get_json()["chain_ok"] is True
    assert c.get("/incident/WEB-1.pdf").data.startswith(b"%PDF")
    assert c.get("/api/incident/WEB-1/fhir").get_json()["resourceType"] == "Bundle"


def test_bad_inputs(tmp_path):
    c = client(tmp_path)
    assert c.post("/api/parse", json={"text": "  "}).status_code == 400
    assert c.get("/api/incident/nope").status_code == 404
    assert c.get("/api/incident/..%2Fx").status_code in (400, 404)
    assert c.post("/api/commit", json={"entries": []}).status_code == 400


def test_sync_offline_keeps_record_queued(tmp_path):
    c = client(tmp_path)
    entries = c.post("/api/parse", json={"text": "gave aspirin 324 mg PO at 10:00"}).get_json()["entries"]
    c.post("/api/commit", json={"incident_id": "S-1", "entries": entries})
    r = c.post("/api/sync/S-1", json={"url": "http://127.0.0.1:9/unreachable"}).get_json()
    assert r["ok"] is False and "Offline" in r["message"]
    assert c.get("/api/incident/S-1").get_json()["incident"]["synced"] is False


def test_transcribe_without_backend_is_graceful(tmp_path):
    import io
    from fieldscribe import asr
    if asr.available_backends():
        return
    r = client(tmp_path).post("/api/transcribe", data={"audio": (io.BytesIO(b"x"), "a.wav")},
                              content_type="multipart/form-data")
    assert r.status_code == 501
