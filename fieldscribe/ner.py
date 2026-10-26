"""Rule-based clinical NER: drug / dose / route / procedure / time extraction.

Runs fully on-device with only the standard library. Designed so the rule engine can be
swapped for (or combined with) a fine-tuned ClinicalBERT/DistilBERT token classifier later:
anything that returns a list of `Entry` objects can replace `parse_note`.
"""
from __future__ import annotations
import difflib
import re
from typing import Optional

from .lexicon import (DRUGS, ROUTES, PROCEDURES, UNIT_DIM, UNIT_CANON, NEGATION_WORDS)
from .models import Entry, ParseResult
from .normalize import normalize
from .validator import validate

_CLAUSE_SPLIT = re.compile(r"[.;\n]+(?!\d)")
_DOSE_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(mg|mcg|ug|g|gm|ml|cc|l|units?|iu)\b(?!\s*/)")
_TIME_RES = [
    re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\s*(am|pm)?(?!\s*(?:mg|mcg|g|ml|l|units?|j|joules)\b)"),
    re.compile(r"\b([01]\d|2[0-3])([0-5]\d)\s*(?:hrs|hours|h)\b"),
    re.compile(r"\bat\s+([01]\d|2[0-3])([0-5]\d)\b()"),
]
_ROUTE_RES = {r: re.compile(p) for r, p in ROUTES.items()}


def _compile_mentions():
    items = []
    for canon, d in DRUGS.items():
        for a in d["aliases"]:
            items.append((re.compile(r"(?<![\w'])" + re.escape(a) + r"(?![\w'])"), "medication", canon))
    for canon, pats in PROCEDURES.items():
        for p in pats:
            items.append((re.compile(p), "procedure", canon))
    return items


_MENTIONS = _compile_mentions()
_FUZZY_VOCAB = {a: c for c, d in DRUGS.items() for a in d["aliases"] if " " not in a and len(a) >= 6}


def _find_mentions(c: str):
    """Return non-overlapping mentions [(start, end, kind, canon, name_conf, fuzzy)]."""
    cands = []
    for rx, kind, canon in _MENTIONS:
        for m in rx.finditer(c):
            cands.append((m.start(), m.end(), kind, canon))
    cands.sort(key=lambda x: (-(x[1] - x[0]), x[0]))
    taken, out = [], []
    for s, e, kind, canon in cands:
        if any(s < te and e > ts for ts, te in taken):
            continue
        taken.append((s, e))
        out.append([s, e, kind, canon, 1.0, False])
    # fuzzy drug names (ASR / typo tolerance)
    for m in re.finditer(r"[a-z]{6,}", c):
        s, e = m.span()
        if any(s < te and e > ts for ts, te in taken):
            continue
        close = difflib.get_close_matches(m.group(0), list(_FUZZY_VOCAB), n=1, cutoff=0.84)
        if close:
            ratio = difflib.SequenceMatcher(None, m.group(0), close[0]).ratio()
            taken.append((s, e))
            out.append([s, e, "medication", _FUZZY_VOCAB[close[0]], round(ratio * 0.9, 2), True])
    out.sort(key=lambda x: x[0])
    # one procedure named twice back-to-back ("12-lead ... ECG") is a single event
    dedup = []
    for m in out:
        if dedup and m[2] == "procedure" and dedup[-1][2] == "procedure" and dedup[-1][3] == m[3] \
                and m[0] - dedup[-1][1] <= 12:
            continue
        dedup.append(m)
    return dedup


def _find_time(s: str):
    best = None
    for rx in _TIME_RES:
        m = rx.search(s)
        if m and (best is None or m.start() < best[0]):
            hh, mm = int(m.group(1)), int(m.group(2))
            ap = m.group(3) if m.lastindex and m.lastindex >= 3 else None
            if ap == "pm" and hh < 12:
                hh += 12
            if ap == "am" and hh == 12:
                hh = 0
            best = (m.start(), m.end(), f"{hh:02d}:{mm:02d}")
    return best


def _find_route(s: str, consumed: list, offset: int):
    best = None
    for canon, rx in _ROUTE_RES.items():
        for m in rx.finditer(s):
            a, b = m.start() + offset, m.end() + offset
            if any(a < ce and b > cs for cs, ce in consumed):
                continue
            if best is None or m.start() < best[0]:
                best = (m.start(), m.end(), canon)
            break
    return best


def _procedure_details(canon: str, seg: str) -> dict:
    d = {}
    if canon == "Defibrillation":
        m = re.search(r"(\d+)\s*(?:j\b|joules?)", seg)
        if m:
            d["energy_joules"] = int(m.group(1))
    if canon == "Oxygen administration":
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:l/min|lpm|l per min(?:ute)?|liters? per minute|litres? per minute)", seg)
        if m:
            d["flow_l_per_min"] = float(m.group(1))
        m = re.search(r"non[- ]?rebreather|\bnrb\b|nasal cannula|\bbvm\b|face mask|\bmask\b", seg)
        if m:
            d["device"] = m.group(0)
    return d


def parse_note(text: str) -> ParseResult:
    norm = normalize(text)
    warnings, entries = [], []
    spans, start = [], 0
    for m in _CLAUSE_SPLIT.finditer(norm):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(norm)))

    for cs, ce in spans:
        c = norm[cs:ce]
        if not c.strip():
            continue
        mentions = _find_mentions(c)
        if not mentions:
            continue
        clause_time = _find_time(c)
        first_start = mentions[0][0]
        lead_time = clause_time if clause_time and clause_time[0] < first_start else None

        segs = []
        for i, mn in enumerate(mentions):
            s = mn[0]
            e = mentions[i + 1][0] if i + 1 < len(mentions) else len(c)
            segs.append((s, e))

        doses_claimed: list = []   # (abs_start, abs_end)
        routes_claimed: list = []
        picked = [None] * len(mentions)
        # pass 1: compatible-dimension dose in own forward segment
        for i, mn in enumerate(mentions):
            if mn[2] != "medication":
                continue
            dim = DRUGS[mn[3]]["dim"]
            s, e = segs[i]
            for m in _DOSE_RE.finditer(c[s:e]):
                ab = (m.start() + s, m.end() + s)
                if ab in doses_claimed:
                    continue
                if UNIT_DIM[m.group(2)] == dim:
                    picked[i] = (float(m.group(1)), m.group(2), ab)
                    doses_claimed.append(ab)
                    break
        # pass 2: dose just before the drug name ("500 ml normal saline"), then any-dimension fallback
        for i, mn in enumerate(mentions):
            if mn[2] != "medication" or picked[i]:
                continue
            dim = DRUGS[mn[3]]["dim"]
            prev_end = mentions[i - 1][1] if i else 0
            back = [m for m in _DOSE_RE.finditer(c[prev_end:mn[0]])
                    if (m.start() + prev_end, m.end() + prev_end) not in doses_claimed
                    and UNIT_DIM[m.group(2)] == dim]
            if back:
                m = back[-1]
                ab = (m.start() + prev_end, m.end() + prev_end)
                picked[i] = (float(m.group(1)), m.group(2), ab)
                doses_claimed.append(ab)
                continue
            s, e = segs[i]
            for m in _DOSE_RE.finditer(c[s:e]):
                ab = (m.start() + s, m.end() + s)
                if ab not in doses_claimed:
                    picked[i] = (float(m.group(1)), m.group(2), ab)
                    doses_claimed.append(ab)
                    break

        for i, mn in enumerate(mentions):
            s, e = segs[i]
            seg = c[s:e]
            kind, canon, name_conf, fuzzy = mn[2], mn[3], mn[4], mn[5]
            flags = []
            # time
            own = _find_time(seg)
            if lead_time and not own:
                t = lead_time[2]
                if re.search(r"\bthen\b", c[lead_time[1]:mn[0]]):   # "at 10:50 gave X, then Y"
                    t_state = "inferred"
                    flags.append("TIME_INFERRED")
                else:
                    t_state = "explicit"
            elif own:
                t, t_state = own[2], "explicit"
            elif clause_time:
                t, t_state = clause_time[2], "inferred"
                flags.append("TIME_INFERRED")
            else:
                t, t_state = None, "missing"
                flags.append("TIME_MISSING")
            if len(list(_TIME_RES[0].finditer(seg))) > 1:   # "epi 1 mg at 10:42 and 10:47": maybe 2 doses
                flags.append("MULTIPLE_TIMES")
            # negation
            window = c[max(0, mn[0] - 25):mn[0]]
            if any(w in window for w in NEGATION_WORDS):
                flags.append("NEGATION_SUSPECTED")
            if fuzzy:
                flags.append("FUZZY_NAME")

            if kind == "medication":
                dose = picked[i]
                route = _find_route(seg, routes_claimed, s)
                if not route:   # route stated just before the drug: "gave IV epinephrine"
                    pre_s = max(mentions[i - 1][1] if i else 0, mn[0] - 20)
                    r = _find_route(c[pre_s:mn[0]], routes_claimed, pre_s)
                    if r:
                        route = (r[0] + pre_s - s, r[1] + pre_s - s, r[2])
                if route:
                    routes_claimed.append((route[0] + s, route[1] + s))
                unit = UNIT_CANON.get(dose[1], dose[1]) if dose else None
                entry = Entry(kind="medication", name=canon, dose_value=dose[0] if dose else None,
                              dose_unit=unit, route=route[2] if route else None, time=t,
                              source_text=c.strip(), flags=flags)
                conf = name_conf * 0.5 + (0.25 if dose else 0) + (0.15 if route else 0) + \
                    (0.10 if t_state == "explicit" else 0.05 if t_state == "inferred" else 0)
            else:
                entry = Entry(kind="procedure", name=canon, time=t, details=_procedure_details(canon, seg),
                              source_text=c.strip(), flags=flags)
                conf = name_conf * 0.8 + (0.2 if t_state == "explicit" else 0.1 if t_state == "inferred" else 0)
            entry.confidence = round(min(conf, 1.0), 2)
            validate(entry)
            entries.append(entry)

    if not entries:
        warnings.append("No medications or procedures were recognised. Check the wording or add them manually.")
    return ParseResult(entries=entries, normalized_text=norm, warnings=warnings)
