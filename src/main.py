
# src/main.py
import argparse
import sys
from typing import TextIO


from processor import process_stream


def _run(input_stream: TextIO) -> int:
    """Run the aggregation against the given input stream."""
    try:
        process_stream(input_stream, sys.stdout)
    except ValueError as exc:
        # Fail fast but give a readable error for CLI
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate trade statistics from a CSV price update stream"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help=(
            "Path to input CSV file. If omitted or '-', "
            "read from standard input."
        ),
    )
    args = parser.parse_args()

    if args.file and args.file != "-":
        with open(args.file, "r", newline="") as f:
            return _run(f)

    return _run(sys.stdin)


if __name__ == "__main__":
    raise SystemExit(main())
