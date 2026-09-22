from enum import Enum
from typing import List, Tuple, Dict


class Accent(Enum):
    Unset = ""
    K = "K"
    D = "D"
    R = "R"

    def accent(self) -> str:
        if self == Accent.K:
            return "\u0300"
        if self == Accent.D:
            return "\u0301"
        if self == Accent.R:
            return "\u0303"
        return ""

    def add_to_word(self, pos: int, word: str) -> str:
        if self == Accent.Unset:
            return word
        if pos < 0 or pos >= len(word):
            raise ValueError(f"wrong pos {pos} for {word}")
        return word[: pos + 1] + self.accent() + word[pos + 1:]


_ACCENTS = {
    "\"e": (Accent.K, {}),
    "\"o": (Accent.K, {}),
    "\"i": (Accent.K, {}),
    "\"a": (Accent.K, {}),
    "\"u": (Accent.K, {}),
    "\"ui": (Accent.K, {}),
    "\"iu": (Accent.K, {"iu": 1}),

    "\"ie": (Accent.D, {}),
    "\"ai": (Accent.D, {}),
    "\"uo": (Accent.D, {}),
    "\"au": (Accent.D, {}),

    "^eu": (Accent.R, {"iau": 2, "eu": 1}),
    "^au": (Accent.R, {"au": 1}),
    "^ai": (Accent.R, {"ai": 1}),
    "^ie": (Accent.R, {"ie": 1}),
    "^ui": (Accent.R, {"ui": 1}),
    "^ei": (Accent.R, {"ei": 1}),
    "\"ei": (Accent.D, {"ei": 0, "iai": 1}),
    "^uo": (Accent.R, {"uo": 1}),

    "^io:": (Accent.R, {"io": 1}),
    "^iuo": (Accent.R, {"uo": 1, "iuo": 2}),

    "^a:": (Accent.R, {}),
    "^e:": (Accent.R, {}),
    "^r": (Accent.R, {}),
    "^n": (Accent.R, {}),
    "^N": (Accent.R, {}),
    "^m": (Accent.R, {}),
    "^o:": (Accent.R, {}),
    "^u:": (Accent.R, {}),
    "^i:": (Accent.R, {}),
    "^E:": (Accent.R, {}),
    "^l": (Accent.R, {}),

    "\"o:": (Accent.D, {}),
    "\"eu": (Accent.D, {"eu": 0, "iau": 1}),
    "\"e:": (Accent.D, {}),
    "\"a:": (Accent.D, {}),
    "\"E:": (Accent.D, {}),
    "\"u:": (Accent.D, {}),
    "\"i:": (Accent.D, {}),
    "\"iu:": (Accent.D, {"iū": 1, "ių": 1}),
    "\"io:": (Accent.D, {"io": 1}),
    "\"io": (Accent.K, {"io": 1, "o": 0}),
    "^iu:": (Accent.R, {"iū": 1, "ių": 1}),
    "^iui": (Accent.R, {"iui": 2}),
    "\"iuo": (Accent.D, {"iuo": 1, "uo": 0}),

}

_PHONEME_TO_GRAPHEME = {
    "tS": {"č", "c"},
    "io": {"io", "o"},
    "iuo": {"iuo", "uo"},
    "io:": {"io", "o"},
    "E": {"ė"},
    "N": {"n"},
    "E:": {"ė"},
    "e:": {"e", "ia", "a", "ę"},
    "e": {"e", "ia", "a"},
    "ei": {"ei", "iai"},
    "eu:": {"eu", "iau", "au"},
    "eu": {"eu", "iau", "au"},
    "S": ["šš", "š", "ž", "s"],
    "ts": {"c", "č", "ts"},
    "Z": ["žž", "šž", "ž", "š", "z"],
    "G": {"h"},
    "dZ": ["dž", "č", "tdž"],
    "dz": ["dz", "c"],
    "r": ["rr", "r"],
    "x": {"ch"},
    "i:": {"y", "į"},
    "i": {"y", "i"},
    "z": {"s", "z"},
    "u:": {"ū", "ų"},
    "iu:": {"iū", "ių", "ū", "ų"},
    "iu": {"iu", "u"},
    "a:": {"a", "ą"},
    "f:": {"f", "v"},
    "o:": {"o"},
    "s": {"s", "šs", "žs", "z"},
    "t": {"t", "d"},
    "k": ["gk", "k", "g"],
    "d": {"t", "d"},
    "g": {"k", "g"},
    "b": {"b", "p"},
    "p": {"b", "p"},
    "j": ["j", ""],
    "sil": [""],
    "sp": [""],
    "f": ["f", "v"],
    "m": ["n", "m"]
}


def clean_phone(ph):
    return ph.replace("\"", "").replace("'", "").replace(".", "").replace("^", "")


def clean(ph: str) -> Tuple[Tuple[Accent, Dict[str, int]], str]:
    acc = _ACCENTS.get(ph.replace("'", "").replace(".", ""), (Accent.Unset, {}))
    return acc, clean_phone(ph)


def get_accent_index(word: str, phones: List[str]) -> Tuple[Accent, int]:
    word = word.lower()
    wi = 0
    for ph in phones:
        (acc, fixes), cleaned = clean(ph)
        if acc != Accent.Unset:
            for f in fixes:
                if word[wi:wi + len(f)] == f:
                    return acc, wi + fixes[f]
            return acc, wi
        possible = _PHONEME_TO_GRAPHEME.get(cleaned, {cleaned})
        was = False
        for l in possible:
            if word[wi:wi + len(l)] == l:
                wi += len(l)
                was = True
                break
        if not was:
            raise ValueError(f"phonemes mismatch {ph} for {word}[{wi}], ph: {phones}")
    for ph in phones:
        if "\"" in ph or "^" in ph:
            raise ValueError(f"accent not detected {ph} for {word}")
    return Accent.Unset, -1
