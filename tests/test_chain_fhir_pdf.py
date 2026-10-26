import copy
from fieldscribe import chain
from fieldscribe.fhir import to_fhir_bundle
from fieldscribe.pdfgen import build_pdf
from fieldscribe.pipeline import record_note
from fieldscribe.store import IncidentStore


def make(tmp_path):
    store = IncidentStore(tmp_path)
    store.create("T-1", responder="Medic 1", patient_label="Patient A", incident_date="2026-10-26")
    return store, record_note(store, "T-1", "Gave epi 1 mg IV at 10:42. Intubated at 10:45", auto_confirm=True)


def test_chain_verifies_and_links(tmp_path):
    _, inc = make(tmp_path)
    assert chain.verify(inc["chain"]) == (True, None)
    assert inc["chain"][0]["prev_hash"] == chain.GENESIS
    assert inc["chain"][1]["prev_hash"] == inc["chain"][0]["hash"]


def test_tampering_is_detected(tmp_path):
    _, inc = make(tmp_path)
    bad = copy.deepcopy(inc["chain"])
    bad[0]["payload"]["dose_value"] = 10.0          # change the recorded dose
    assert chain.verify(bad) == (False, 0)
    bad = copy.deepcopy(inc["chain"])
    del bad[0]                                      # delete an entry
    assert chain.verify(bad)[0] is False


def test_persistence_roundtrip(tmp_path):
    store, inc = make(tmp_path)
    again = store.load("T-1")
    assert again["chain"] == inc["chain"]


def test_invalid_incident_id_rejected(tmp_path):
    store = IncidentStore(tmp_path)
    for bad in ["../x", "a/b", "", "x" * 50]:
        try:
            store.load(bad)
            assert False
        except ValueError:
            pass


def test_fhir_bundle_shape(tmp_path):
    _, inc = make(tmp_path)
    b = to_fhir_bundle(inc)
    assert b["resourceType"] == "Bundle" and len(b["entry"]) == 2
    ma = b["entry"][0]["resource"]
    assert ma["resourceType"] == "MedicationAdministration"
    assert ma["dosage"]["dose"]["value"] == 1.0 and ma["dosage"]["route"]["text"] == "IV"
    assert ma["effectiveDateTime"] == "2026-10-26T10:42:00"
    assert b["entry"][1]["resource"]["resourceType"] == "Procedure"


def test_pdf_is_generated(tmp_path):
    _, inc = make(tmp_path)
    pdf = build_pdf(inc)
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500
