"""The Funniest Toaster Error Message entry: writes one deadpan toaster
error message to /output/entry.txt.

The entry text is fixed: exactly 80 characters, one line, no trailing
newline. Validation raises ValueError with a clear message instead of
relying on assert, so checks stay active even under python -O.
`--verify` validates only and writes nothing; the normal run writes the
entry atomically (temp file + fsync + os.replace) to /output/entry.txt.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

ENTRY = "E09: Slot 1 is haunted. Slot 2 works fine. The toaster does not know why either."

MIN_ENTRY_CHARS = 1
MAX_ENTRY_CHARS = 120


def format_entry(text):
    """Return the entry as exactly one line with no trailing newline.

    Strips a single trailing newline or carriage return if present, then
    rejects any remaining line break so the output can never gain a
    second line by accident.
    """
    if not isinstance(text, str):
        raise ValueError("entry must be a string")
    cleaned = text.rstrip("\r\n")
    if "\n" in cleaned or "\r" in cleaned:
        raise ValueError("entry must be a single line (no embedded newline)")
    return cleaned


def validate_entry(text):
    """Entry must be a non-empty one-liner within the platform character limit."""
    if not isinstance(text, str):
        raise ValueError("entry must be a string")
    formatted = format_entry(text)
    if not MIN_ENTRY_CHARS <= len(formatted) <= MAX_ENTRY_CHARS:
        raise ValueError(
            f"entry length {len(formatted)} outside "
            f"{MIN_ENTRY_CHARS}..{MAX_ENTRY_CHARS}"
        )
    return formatted


def write_entry_atomic(path, text):
    """Write via a temp file in the same directory, fsync it, then
    os.replace atomically, so a crash cannot leave a half-written entry."""
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write the competition entry.")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="only validate the entry text, do not write any file",
    )
    args = parser.parse_args(argv)
    try:
        entry = validate_entry(ENTRY)
    except ValueError as exc:
        print(f"invalid entry: {exc}", file=sys.stderr)
        return 1
    if args.verify:
        print(f"entry valid: {len(entry)} characters, single line, no trailing newline")
        return 0
    out_dir = Path("/output")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"cannot create output directory {out_dir}: {exc}", file=sys.stderr)
        return 1
    try:
        write_entry_atomic(out_dir / "entry.txt", entry)
    except OSError as exc:
        print(f"cannot write entry: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
