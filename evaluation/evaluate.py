"""Entity-level precision/recall/F1 on a small hand-labelled SYNTHETIC set.

IMPORTANT: these cases were written by the project authors against the same lexicon, so the score
is optimistic. It is a regression test for the rule engine, NOT evidence of real-world accuracy.
Measure real accuracy on de-identified n2c2 medication notes / your own recorded dictations.
Run:  python evaluation/evaluate.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fieldscribe.ner import parse_note  # noqa: E402


def key(kind, name, val, unit, route, strict=True):
    return (kind, name, val, unit, route) if strict else (kind, name)


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main():
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    tot = {True: [0, 0, 0], False: [0, 0, 0]}
    misses = []
    for c in cases:
        pred = parse_note(c["t"]).entries
        for strict in (True, False):
            P = [key(e.kind, e.name, e.dose_value, e.dose_unit, e.route, strict) for e in pred]
            G = [key(k, n, (None if v is None else float(v)), u, r, strict) for k, n, v, u, r in c["e"]]
            tp = sum(1 for g in G if g in P)
            tot[strict][0] += tp
            tot[strict][1] += max(len(P) - tp, 0)
            tot[strict][2] += len(G) - tp
            if strict and (sorted(map(str, P)) != sorted(map(str, G))):
                misses.append((c["t"], P, G))
    for strict, label in ((False, "Item recognition (kind+name)"), (True, "Full entity (name+dose+unit+route)")):
        p, r, f = prf(*tot[strict])
        print(f"{label:38s} P={p:.2f} R={r:.2f} F1={f:.2f}   (tp={tot[strict][0]} fp={tot[strict][1]} fn={tot[strict][2]})")
    print(f"\n{len(cases)} cases, {len(misses)} with any mismatch")
    for t, P, G in misses:
        print("  -", t, "\n      got ", P, "\n      want", G)


if __name__ == "__main__":
    main()
