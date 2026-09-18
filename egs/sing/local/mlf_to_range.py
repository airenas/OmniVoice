import argparse
import fileinput
import sys

import mlf
import range


def is_split(m):
    return (m.ph == "sil" or m.ph == "sp") and m.sent == "sil"

def write_ranges(ranges, file):
    for r in ranges:
        print("%d %d" % (r.from_, r.to), file=file)

def main(argv):
    parser = argparse.ArgumentParser(description="Makes range file for mlf. Splits by sentence",
                                     epilog="E.g. cat input.mlf | " + sys.argv[0] + " > result.range",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--max-sil", default=200, type=int, help="Max sil in ms")
    parser.add_argument("--max-duration", default=15000, type=int, help="Max duration in ms")

    parser.add_argument("files", nargs="*", help="Input MLF file(s), reads stdin when omitted")
    args = parser.parse_args(args=argv)

    # print("Starting", file=sys.stderr)
    # print("Using max sil %d ms" % args.maxSil, file=sys.stderr)
    max_sil = args.max_sil * 10000
    mlfs = []
    lc = 0
    files = args.files if args.files else ("-",)
    for line in fileinput.input(files=files):
        lc += 1
        s_line = line.strip()
        if s_line == "#!MLF!#":
            continue
        elif s_line == ".":
            continue
        else:
            m_line = mlf.from_str(line.rstrip())
            mlfs.append(m_line)

    res = []
    r = None
    for i, m_line in enumerate(mlfs):
        from_ = int(m_line.from_)
        to = int(m_line.to)

        is_sp = is_split(m_line)
        if i == 0:
            r = range.Range(from_, to)
            if is_sp:
                r.from_ = trim_4(max(from_, to - max_sil))
            res.append(r)
        elif i == len(mlfs) - 1:
            r.to = to
            if is_sp:
                r.to = trim_4(min(to, from_ + max_sil))
        elif is_sp:
            at = from_ + (to - from_) / 2
            at = trim_4(at)
            r.to = trim_4(min(at, from_ + max_sil))
            r = range.Range(trim_4(max(at, to - max_sil)), to)
            res.append(r)

    # res = join_ranges(res, max_duration=args.max_duration * 10000)
    write_ranges(res, sys.stdout)

    print("Read %d lines, %d splits" % (lc, len(res)), file=sys.stderr)
    # print("Done", file=sys.stderr)


def trim_4(n):
    return int(n / 10000) * 10000


if __name__ == "__main__":
    main(sys.argv[1:])
