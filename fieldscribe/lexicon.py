"""Clinical lexicon: drugs, routes, procedures.

!! The dose ranges below are ILLUSTRATIVE, adult-oriented values for a student proof of
!! concept. They are NOT clinical guidance and must be replaced by protocol-approved limits
!! from a medical director before any real-world use.
"""

# canonical -> dict(aliases, dim, lo, hi (in base units: mg for mass, ml for volume, units), routes)
DRUGS = {
    "Epinephrine": dict(aliases=["epinephrine", "epinephrin", "adrenaline", "adrenalin", "epi"],
                        dim="mass", lo=0.1, hi=1.0, routes=["IV", "IM", "IO", "SC"]),
    "Aspirin": dict(aliases=["aspirin", "asa"], dim="mass", lo=75, hi=325, routes=["PO"]),
    "Morphine": dict(aliases=["morphine", "morph"], dim="mass", lo=1, hi=15, routes=["IV", "IM", "IO", "SC"]),
    "Fentanyl": dict(aliases=["fentanyl", "fent"], dim="mass", lo=0.025, hi=0.2, routes=["IV", "IM", "IN", "IO"]),
    "Naloxone": dict(aliases=["naloxone", "narcan"], dim="mass", lo=0.4, hi=4, routes=["IV", "IM", "IN", "IO", "SC"]),
    "Atropine": dict(aliases=["atropine"], dim="mass", lo=0.4, hi=3, routes=["IV", "IO", "IM"]),
    "Amiodarone": dict(aliases=["amiodarone", "amio"], dim="mass", lo=150, hi=300, routes=["IV", "IO"]),
    "Ondansetron": dict(aliases=["ondansetron", "zofran"], dim="mass", lo=4, hi=8, routes=["IV", "IM", "PO", "SL"]),
    "Midazolam": dict(aliases=["midazolam", "versed"], dim="mass", lo=1, hi=10, routes=["IV", "IM", "IN", "IO"]),
    "Diazepam": dict(aliases=["diazepam", "valium"], dim="mass", lo=2, hi=10, routes=["IV", "IM", "PR", "IO"]),
    "Salbutamol": dict(aliases=["salbutamol", "albuterol", "ventolin"], dim="mass", lo=2.5, hi=5, routes=["NEB"]),
    "Nitroglycerin": dict(aliases=["nitroglycerin", "nitroglycerine", "ntg", "nitro", "gtn"],
                          dim="mass", lo=0.3, hi=0.8, routes=["SL"]),
    "Dextrose": dict(aliases=["dextrose", "glucose"], dim="mass", lo=5000, hi=25000, routes=["IV", "IO", "PO"]),
    "Paracetamol": dict(aliases=["paracetamol", "acetaminophen", "tylenol"], dim="mass", lo=500, hi=1000,
                        routes=["PO", "IV", "PR"]),
    "Adenosine": dict(aliases=["adenosine"], dim="mass", lo=3, hi=18, routes=["IV", "IO"]),
    "Tranexamic acid": dict(aliases=["tranexamic acid", "txa"], dim="mass", lo=500, hi=2000, routes=["IV", "IO"]),
    "Normal saline": dict(aliases=["normal saline", "saline"], dim="volume", lo=100, hi=2000, routes=["IV", "IO"]),
    "Ringer's lactate": dict(aliases=["ringer's lactate", "ringers lactate", "lactated ringers",
                                      "lactated ringer's"], dim="volume", lo=100, hi=2000, routes=["IV", "IO"]),
}

# route canonical -> regex alternatives (applied to lowercased, normalised text)
ROUTES = {
    "IV": r"\biv\b|intravenous(?:ly)?|through the vein|in the vein|iv push",
    "IM": r"\bim\b|intramuscular(?:ly)?",
    "IO": r"\bio\b|intraosseous(?:ly)?",
    "PO": r"\bpo\b|\boral(?:ly)?\b|by mouth",
    "SL": r"\bsl\b|sublingual(?:ly)?|under the tongue",
    "IN": r"intranasal(?:ly)?|\bnasally\b|through the nose|(?<=g )in(?= at\b|\s*$|,)|(?<=ml )in(?= at\b|\s*$|,)",
    "NEB": r"\bneb\b|nebuli[sz]ed|nebuli[sz]er",
    "SC": r"\bsc\b|\bsubq\b|subcut(?:aneous(?:ly)?)?",
    "PR": r"\bpr\b|rectal(?:ly)?",
}

# procedure canonical -> list of regex patterns
PROCEDURES = {
    "Intubation": [r"intubat(?:ed|ion|e)", r"endotracheal tube", r"\bett\b"],
    "IV access": [r"iv access", r"iv (?:line|cannula|started|established)", r"started (?:an? |the )?iv\b",
                  r"cannulat(?:ed|ion)", r"established iv"],
    "CPR": [r"\bcpr\b", r"chest compressions?", r"\bcompressions\b"],
    "Defibrillation": [r"defibrillat(?:ed|ion)", r"\bshock(?:ed)?\b(?: delivered)?"],
    "Oxygen administration": [r"\boxygen\b", r"\bo2\b"],
    "Bag-valve-mask ventilation": [r"\bbvm\b", r"bag[- ]valve[- ]mask", r"\bbagging\b"],
    "Splinting": [r"\bsplint(?:ed|ing)?\b"],
    "Tourniquet application": [r"\btourniquet\b"],
    "Cervical collar": [r"c[- ]collar", r"cervical collar"],
    "Wound dressing": [r"pressure dressing", r"dressing applied", r"\bbandag(?:ed|ing)\b", r"wound dressed"],
    "12-lead ECG": [r"12[- ]lead", r"\becg\b", r"\bekg\b"],
    "Needle decompression": [r"needle decompression", r"chest decompression"],
    "Suction": [r"\bsuction(?:ed|ing)?\b"],
    "Cardioversion": [r"cardiover(?:ted|sion)"],
    "Pelvic binder": [r"pelvic binder"],
    "Spinal immobilisation": [r"backboard", r"spinal board", r"spinal immobili[sz]ation"],
}

UNIT_DIM = {"mg": "mass", "mcg": "mass", "ug": "mass", "g": "mass", "gm": "mass",
            "ml": "volume", "cc": "volume", "l": "volume",
            "unit": "units", "units": "units", "iu": "units"}
# multiplier to base unit (mg / ml / units)
UNIT_FACTOR = {"mg": 1, "mcg": 0.001, "ug": 0.001, "g": 1000, "gm": 1000,
               "ml": 1, "cc": 1, "l": 1000, "unit": 1, "units": 1, "iu": 1}
UNIT_CANON = {"ug": "mcg", "gm": "g", "cc": "ml", "unit": "units", "iu": "units"}

NEGATION_WORDS = ["no ", "not ", "refused", "declined", "allergic", "held ", "withheld", "didn't", "did not",
                  "without", "contraindicated"]
