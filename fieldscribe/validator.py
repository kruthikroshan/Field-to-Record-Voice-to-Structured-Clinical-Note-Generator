"""Safety checks on extracted entries (illustrative ranges, see lexicon.py)."""
from .config import LOW_CONFIDENCE
from .lexicon import DRUGS, UNIT_DIM, UNIT_FACTOR
from .models import Entry


def _add(entry: Entry, flag: str):
    if flag not in entry.flags:
        entry.flags.append(flag)


def validate(entry: Entry) -> Entry:
    if entry.kind == "medication":
        spec = DRUGS.get(entry.name)
        if entry.dose_value is None:
            _add(entry, "DOSE_MISSING")
        elif spec:
            unit = entry.dose_unit
            if UNIT_DIM.get(unit) != spec["dim"]:
                _add(entry, "UNIT_MISMATCH")
                entry.confidence = round(entry.confidence * 0.8, 2)
            else:
                base = entry.dose_value * UNIT_FACTOR[unit]
                if not (spec["lo"] <= base <= spec["hi"]):
                    _add(entry, "DOSE_OUT_OF_RANGE")
                    entry.confidence = round(entry.confidence * 0.8, 2)
        if entry.route is None:
            _add(entry, "ROUTE_MISSING")
        elif spec and entry.route not in spec["routes"]:
            _add(entry, "ROUTE_UNUSUAL")
            entry.confidence = round(entry.confidence * 0.85, 2)
    if "NEGATION_SUSPECTED" in entry.flags:
        entry.confidence = round(entry.confidence * 0.6, 2)
    if entry.confidence < LOW_CONFIDENCE:
        _add(entry, "LOW_CONFIDENCE")
    return entry
