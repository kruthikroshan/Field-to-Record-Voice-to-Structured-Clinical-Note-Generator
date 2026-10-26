from fieldscribe.ner import parse_note
from fieldscribe.normalize import normalize


def ents(text):
    return parse_note(text).entries


def test_basic_med_extraction():
    e = ents("Gave epi 1 mg IV at 10:42")[0]
    assert (e.name, e.dose_value, e.dose_unit, e.route, e.time) == ("Epinephrine", 1.0, "mg", "IV", "10:42")
    assert e.flags == [] and e.confidence >= 0.9


def test_multiple_meds_one_sentence():
    es = ents("Gave epi 1 mg IV at 10:42 and aspirin 324 mg PO at 10:44")
    assert [x.name for x in es] == ["Epinephrine", "Aspirin"]
    assert es[1].time == "10:44" and es[1].route == "PO"


def test_dose_before_drug_name():
    e = ents("At 10:50 gave 500 ml normal saline IV")[0]
    assert (e.name, e.dose_value, e.dose_unit) == ("Normal saline", 500.0, "ml")


def test_spoken_numbers_and_units():
    assert "1.5 mg" in normalize("one point five milligrams")
    e = ents("gave one point five milligrams of epinephrine intravenously at 1105 hrs")[0]
    assert e.dose_value == 1.5 and e.route == "IV" and e.time == "11:05"
    assert "DOSE_OUT_OF_RANGE" in e.flags


def test_typo_tolerance_is_flagged():
    e = ents("gave morphin 5 mg IV at 10:00")[0]
    assert e.name == "Morphine" and "FUZZY_NAME" in e.flags


def test_procedures_and_details():
    es = ents("Defibrillated at 200 J 10:46. Oxygen 15 L/min via NRB at 10:47")
    assert es[0].name == "Defibrillation" and es[0].details["energy_joules"] == 200
    assert es[1].details["flow_l_per_min"] == 15.0


def test_missing_fields_are_flagged_not_guessed():
    e = ents("gave morphine")[0]
    assert {"DOSE_MISSING", "ROUTE_MISSING", "TIME_MISSING"} <= set(e.flags)
    assert e.dose_value is None and e.route is None and e.time is None


def test_negation_is_flagged():
    e = ents("Patient refused aspirin")[0]
    assert "NEGATION_SUSPECTED" in e.flags and "LOW_CONFIDENCE" in e.flags


def test_unit_mismatch_and_unusual_route():
    assert "UNIT_MISMATCH" in ents("gave epi 5 ml IV at 10:00")[0].flags
    assert "ROUTE_UNUSUAL" in ents("gave aspirin 324 mg IV at 10:00")[0].flags


def test_decimal_dose_not_mistaken_for_time():
    e = ents("gave 10.5 mg morphine IV at 10:50")[0]
    assert e.dose_value == 10.5 and e.time == "10:50"


def test_empty_result_warns():
    r = parse_note("patient is conscious and talking")
    assert r.entries == [] and r.warnings


def test_point_without_leading_zero():
    e = ents("gave epi point three mg IM at 10:15")[0]
    assert e.dose_value == 0.3 and not e.flags


def test_second_time_in_one_segment_is_flagged_not_dropped():
    assert "MULTIPLE_TIMES" in ents("two doses of epi 1 mg IV at 10:42 and 10:47")[0].flags


def test_started_iv_variants():
    assert ents("started IV 18g left AC at 10:40")[0].name == "IV access"
