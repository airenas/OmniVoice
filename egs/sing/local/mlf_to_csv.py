import argparse
import logging
import sys
from typing import List

import mlf
from egs.sing.local.accents import Accent, get_accent_index


def change_phone(p) -> str:
    if p == ".":  ## do not drop dot
        return p
    return p.replace("'", "").replace(".", "")


class Word:
    def __init__(self, word: str, punctuation: str):
        self.word = word
        self.punctuation = punctuation
        self.phones = []
        self.is_sil = False

    def phones_str(self) -> str:
        if not self.phones:
            return ""

        phones = self.phones[:]
        if mlf.is_sil(phones[-1]) and self.punctuation != "":
            phones.insert(-1, get_punct(self.punctuation))
        elif self.punctuation != "":
            phones.append(get_punct(self.punctuation))
        return " ".join(phones)

    def word_phones_str(self) -> str:
        if not self.phones:
            return ""

        phones = self.phones[:]
        if mlf.is_sil(phones[-1]) and self.punctuation != "":
            phones.insert(-1, get_punct(self.punctuation))
        elif self.punctuation != "":
            phones.append(get_punct(self.punctuation))
        if mlf.is_sil(phones[-1]):
            phones[-1] = " " + phones[-1]

        res = []
        for p in phones:
            pn = change_phone(p)
            if pn:
                res.append(pn)

        return "".join(res).strip()

    def word_accent_str(self):
        if self.is_sil:
            return ""
        try:
            acc, pos = get_accent_index(self.word, self.phones)
            if acc != Accent.Unset:
                return acc.add_to_word(pos, self.word) + get_punct(self.punctuation)
        except Exception as ex:
            logging.warning(f"Problem: {ex}")
        return self.word + get_punct(self.punctuation)


def get_words(words: List[Word]) -> str:
    res, prev = "", ""
    for w in words:
        if w.is_sil:
            continue
        # print(f"({res}), ({w.word}), ({prev})", file=sys.stderr)
        res += prev + w.word + get_punct(w.punctuation)
        prev = " "
    return res


def get_phones(words: List[Word]) -> str:
    res = []
    for w in words:
        phones_str = w.phones_str()
        res.append(phones_str)
    return " ".join(res)


def get_word_phones(words: List[Word]) -> str:
    res = []
    for w in words:
        phones_str = w.word_phones_str()
        if phones_str:
            res.append(phones_str)
    return " ".join(res)


def get_word_accents(words: List[Word]) -> str:
    res = []
    for w in words:
        w_str = w.word_accent_str()
        if w_str:
            res.append(w_str)
    return " ".join(res)


class Line:
    def __init__(self, name: str):
        self.name = name
        self.words: List[Word] = []

    def last_word(self) -> Word:
        if len(self.words) == 0:
            raise ValueError("no words")
        return self.words[-1]

    def to_str(self):
        word_str = get_words(self.words)
        phones = get_phones(self.words)
        word_phones = get_word_phones(self.words).strip()
        word_accent = get_word_accents(self.words)
        return f"{self.name}|{word_str}|{word_str.lower()}|{phones}|{word_phones}|{word_accent}"


def get_punct(s):
    if s == "-":
        return " -"
    return s


def write_line(name, words, phones, file):
    if name != "":
        s = " ".join(words)
        ph = ""
        if len(phones) > 0:
            ph = "|" + " ".join(phones)
        print("%s|%s|%s%s" % (name, s, s.lower(), ph), file=file)


def main(argv):
    parser = argparse.ArgumentParser(description="Convert mlf to specific csv",
                                     epilog="E.g. cat input.mlf | " + sys.argv[0] + " > result.mlf",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", dest="input_file", type=argparse.FileType("r"), default=sys.stdin,
                        help="Input MLF file; read stdin when omitted")
    parser.add_argument("--outputPhones", default=False, action='store_true', help="Do output phones")
    parser.add_argument("--skipSP", default=False, action='store_true', help="Skip 'sp' after punctuation")
    args = parser.parse_args(args=argv)

    print("Starting", file=sys.stderr)

    lc = 0
    wc = 0
    ln: Line | None = None
    for line in args.input_file:
        lc += 1
        s_line = line.strip()
        try:
            if s_line == "#!MLF!#":
                continue
            if s_line.startswith("\""):
                if ln:
                    print(ln.to_str(), file=sys.stdout)
                ln = Line(name=s_line.strip('""').replace(".lab", ""))
            elif s_line == ".":
                continue
            else:
                if not ln:
                    raise ValueError("no item header")
                m_line = mlf.from_str(line.rstrip())
                if m_line.is_word():
                    wc += 1
                    ln.words.append(Word(word=m_line.word, punctuation=m_line.punct))
                if len(ln.words) == 0 and m_line.ph == "sil":
                    w = Word(word="", punctuation="")
                    w.is_sil = True
                    ln.words.append(w)

                ln.last_word().phones.append(m_line.ph)
        except BaseException as ex:
            raise ValueError(f"{ex}. Txt: {s_line}")
    if ln:
        print(ln.to_str(), file=sys.stdout)

    print("Read %d lines, %d words" % (lc, wc), file=sys.stderr)
    print("Done", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
