"""Text normalisation for typed notes and ASR output (spoken numbers, unit words)."""
import re

NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
NUM_WORDS.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
                  "ninety": 90})

_UNIT = r"(?:mg|mcg|ug|g|gm|ml|cc|l|units?|iu|milligrams?|micrograms?|grams?|milliliters?|millilitres?|liters?|litres?)"


def normalize(text: str) -> str:
    t = text.strip().lower().replace("µ", "u").replace("’", "'")
    t = re.sub(r"\s+", " ", t)
    words = "|".join(sorted(NUM_WORDS, key=len, reverse=True))
    t = re.sub(rf"\b({words})\b(?=\s*(?:point\b|{_UNIT}\b))", lambda m: str(NUM_WORDS[m.group(1)]), t)
    t = re.sub(r"(\d)\s*point\s*(\d)", r"\1.\2", t)
    t = re.sub(r"(?<![\d.])\bpoint\s*(\d)", r"0.\1", t)          # "point three" -> 0.3
    t = re.sub(r"\bmilligrams?\b", "mg", t)
    t = re.sub(r"\bmicrograms?\b", "mcg", t)
    t = re.sub(r"\bmilli?(?:liters?|litres?)\b", "ml", t)
    t = re.sub(r"(?<=\d)\s*(?:liters?|litres?)\b", " l", t)
    t = re.sub(r"(?<=\d)\s*grams?\b", " g", t)
    return t
