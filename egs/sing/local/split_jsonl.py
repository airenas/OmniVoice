import argparse
import json
import logging
import random
import sys

from tqdm import tqdm


def main(argv):
    parser = argparse.ArgumentParser(
        description="Split an OmniVoice JSONL manifest into train and dev files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Input JSONL manifest")
    parser.add_argument("--train-output", required=True, help="Output train JSONL path")
    parser.add_argument("--dev-output", required=True, help="Output dev JSONL path")
    parser.add_argument(
        "--dev-ratio",
        type=float,
        default=0.01,
        help="Fraction of records assigned to dev",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random split seed")
    args = parser.parse_args(argv)

    if not 0 < args.dev_ratio < 1:
        parser.error("--dev-ratio must be between 0 and 1")

    with open(args.input, encoding="utf-8") as input_file:
        records = []
        for line_number, line in tqdm(enumerate(input_file), desc="reading"):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"line {line_number}: invalid JSON: {error.msg}") from error
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: expected a JSON object")
            records.append(record)

    if len(records) < 2:
        raise ValueError("input must contain at least two records")

    shuffled_indices = list(range(len(records)))
    random.Random(args.seed).shuffle(shuffled_indices)
    dev_count = max(1, round(len(records) * args.dev_ratio))
    dev_indices = set(shuffled_indices[:dev_count])

    with open(args.dev_output, "w", encoding="utf-8") as dev_file:
        for index, record in enumerate(records):
            if index in dev_indices:
                print(json.dumps(record, ensure_ascii=False), file=dev_file)

    with open(args.train_output, "w", encoding="utf-8") as train_file:
        for index, record in enumerate(records):
            if index not in dev_indices:
                print(json.dumps(record, ensure_ascii=False), file=train_file)

    logging.info(
        f"Split {len(records)} records into "
        f"{len(records) - dev_count} train and {dev_count} dev",
    )


if __name__ == "__main__":
    formatter = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    logging.basicConfig(format=formatter, level=logging.INFO)
    logging.info(f"Starting")
    main(sys.argv[1:])
    logging.info(f"Done")
