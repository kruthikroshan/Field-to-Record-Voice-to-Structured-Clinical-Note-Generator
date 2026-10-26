"""FHIR-lite export: MedicationAdministration + Procedure resources in a collection Bundle.

'Lite' = the handful of fields needed for a field record, not a full conformance profile.
The patient is referenced by a pseudonymous label only (no PHI).
"""
from __future__ import annotations

_UCUM = {"mg": "mg", "mcg": "ug", "g": "g", "ml": "mL", "l": "L", "units": "[IU]"}


def _dt(date: str, hhmm: str | None):
    return f"{date}T{hhmm}:00" if hhmm else None


def _ext(payload: dict, link: dict) -> list:
    return [
        {"url": "urn:fieldscribe:confidence", "valueDecimal": payload.get("confidence")},
        {"url": "urn:fieldscribe:flags", "valueString": ",".join(payload.get("flags", []))},
        {"url": "urn:fieldscribe:confirmed-by-responder", "valueBoolean": payload.get("confirmed", False)},
        {"url": "urn:fieldscribe:chain-hash", "valueString": link["hash"]},
        {"url": "urn:fieldscribe:chain-index", "valueInteger": link["index"]},
    ]


def to_fhir_bundle(incident: dict) -> dict:
    date = incident["incident_date"]
    subject = {"display": incident["patient_label"]}
    performer = [{"actor": {"display": incident["responder"]}}]
    entries = []
    for link in incident["chain"]:
        p = link["payload"]
        when = _dt(date, p.get("time"))
        if p["kind"] == "medication":
            res = {"resourceType": "MedicationAdministration", "id": f"ma-{link['index']}",
                   "status": "completed", "subject": subject, "performer": performer,
                   "medicationCodeableConcept": {"text": p["name"]},
                   "effectiveDateTime": when,
                   "dosage": {}, "extension": _ext(p, link)}
            if p.get("route"):
                res["dosage"]["route"] = {"text": p["route"]}
            if p.get("dose_value") is not None:
                unit = p.get("dose_unit") or ""
                res["dosage"]["dose"] = {"value": p["dose_value"], "unit": unit,
                                         "system": "http://unitsofmeasure.org", "code": _UCUM.get(unit, unit)}
            res["dosage"]["text"] = " ".join(str(x) for x in
                                             [p.get("dose_value"), p.get("dose_unit"), p.get("route")] if x)
        else:
            res = {"resourceType": "Procedure", "id": f"pr-{link['index']}", "status": "completed",
                   "subject": subject, "performer": performer, "code": {"text": p["name"]},
                   "performedDateTime": when, "extension": _ext(p, link)}
            if p.get("details"):
                res["note"] = [{"text": "; ".join(f"{k}={v}" for k, v in p["details"].items())}]
        res = {k: v for k, v in res.items() if v is not None}
        entries.append({"fullUrl": f"urn:fieldscribe:{incident['incident_id']}:{link['index']}", "resource": res})
    return {"resourceType": "Bundle", "type": "collection", "id": incident["incident_id"],
            "meta": {"tag": [{"system": "urn:fieldscribe", "code": "fhir-lite"}]}, "entry": entries}
