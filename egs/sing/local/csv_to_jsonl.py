import argparse
import json
import logging
import os
import sys

from tqdm import tqdm


def main(argv):
    parser = argparse.ArgumentParser(
        description="Convert pipe-delimited metadata to an OmniVoice JSONL manifest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        default="-",
        help="Input CSV path, or '-' to read from stdin",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSONL path, or '-' to write to stdout",
    )
    parser.add_argument(
        "--audio-dir",
        default=".",
        help="Directory containing WAV files named <id>.wav",
    )
    parser.add_argument(
        "--language-id",
        default="lt",
        type=str,
        help="Language ID to add to every record, for example 'lt'",
    )
    parser.add_argument(
        "--type",
        default="gr",
        type=str,
        help="Type ph (phonemes) | gr (graphemes) | wa - accented words",
    )
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as fr:
        with open(args.output, "w", encoding="utf-8") as fw:
            count = 0
            for ln, line in enumerate(tqdm(fr, desc="reading file")):
                line = line.strip()
                if not line:
                    continue
                row = line.split("|")
                rc = 6
                if len(row) < rc:
                    raise ValueError(
                        f"line {ln}: expected at least {rc} pipe-delimited fields, got {len(row)}"
                    )

                sample_id, original_text, lc_text, phonemes, phonemes1, wa = row[:rc]
                sample_id = sample_id.strip()
                if not sample_id:
                    raise ValueError(f"line {ln}: sample ID is empty")

                record = {
                    "id": sample_id,
                    "audio_path": os.path.join(args.audio_dir, sample_id + ".wav"),
                }
                if args.type == "ph":
                    record["text"] = phonemes
                elif args.type == "ph1":
                    record["text"] = phonemes1    
                elif args.type == "gr":
                    record["text"] = original_text
                elif args.type == "wa":
                    record["text"] = wa
                else:
                    raise ValueError(f"unknown type {args.type}")        

                if args.language_id is not None:
                    record["language_id"] = args.language_id

                print(json.dumps(record, ensure_ascii=False), file=fw)
                count += 1

    logging.info(f"Converted {count} records")


if __name__ == "__main__":
    formatter = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    logging.basicConfig(format=formatter, level=logging.INFO)
    logging.info(f"Starting")
    main(sys.argv[1:])
    logging.info(f"Done")



    Идеология нацистского государства включала крайний национализм, расизм, антисемитизм, антикоммунизм, культ личности, представление о «жизненном пространстве» и построении расово определённого «народного сообщества» (нем. Volksgemeinschaft). После прихода к власти НСДАП были ликвидированы основные институты Веймарской республики, запрещены политические партии и независимые профсоюзы, установлена система политического контроля, цензуры и репрессий. Во внешней политике нацистская Германия последовательно пересматривала ограничения Версальского договора, проводила перевооружение, расширяла вооружённые силы и добивалась территориальной экспансии. В 1938 году был осуществлён аншлюс Австрии, затем последовали расчленение и оккупация Чехословакии. 1 сентября 1939 года нападение Германии на Польшу стало началом Второй мировой войны.
