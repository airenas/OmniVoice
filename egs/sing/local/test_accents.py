from typing import List

import pytest

from egs.sing.local.accents import Accent, get_accent_index


@pytest.mark.parametrize(
    "accent, pos, word, expected",
    [
        (Accent.D, 1, "kalnas", "ka\u0301lnas"),
        (Accent.K, 1, "kalnas", "ka\u0300lnas"),
        (Accent.R, 1, "kalnas", "ka\u0303lnas"),
        (Accent.Unset, -1, "kalnas", "kalnas"),
        (Accent.K, 0, "alna", "a\u0300lna"),
        (Accent.K, 3, "alna", "alna\u0300"),
    ],
)
def test_add_to_word(accent, pos, word, expected):
    assert accent.add_to_word(pos, word) == expected


@pytest.mark.parametrize(
    "accent, pos, word",
    [
        (Accent.D, -1, "kalnas"),
        (Accent.D, len("kalnas"), "kalnas"),
    ],
)
def test_add_to_word_invalid_positions(accent, pos, word):
    with pytest.raises(ValueError):
        accent.add_to_word(pos, word)


@pytest.mark.parametrize(
    "word, phones, wanted_accent, wanted_pos",
    [
        ("siaubinga", ["s'", 'eu', "b'", '"i', 'N.', 'g', 'a'], Accent.K, 5),
        ("Tačiau", ["t'", "a", "tS'", "^eu"], Accent.R, 5),
        ("Dzeusas", ["dz'", "\"e", "u", "s", "a", "s"], Accent.K, 2),
        ("Nėra", ["n'", "E", "r", "a"], Accent.Unset, -1),
        ("gyvybės", ["g'", 'i:', "v'", '"i:', "b'", 'E:'], Accent.D, 3),
        ("ietį", ['j', '"ie', "t'", 'i:', 'sp'], Accent.D, 0),
    ],
)
def test_get_accent_index(word: str, phones: List[str], wanted_accent: Accent, wanted_pos: int):
    assert get_accent_index(word, phones) == (wanted_accent, wanted_pos)
