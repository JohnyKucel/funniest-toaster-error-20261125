"""The Funniest Toaster Error Message entry: writes one deadpan toaster
error message to /output/entry.txt.

The entry text is fixed: exactly 80 characters, one line, no trailing
newline. Validation raises ValueError with a clear message instead of
relying on assert, so checks stay active even under python -O.
`--verify` validates only and writes nothing; the normal run writes the
entry atomically (temp file + fsync + os.replace + directory fsync) to
/output/entry.txt.
Output location is fixed by OUTPUT_DIR / ENTRY_FILENAME below so the
path is defined in exactly one place.
Entry point flow is deliberately split so each step is testable alone:
_parse_args() owns the CLI surface, _ensure_output_dir() owns the
filesystem precondition, and main() only orchestrates the steps in
order — parse, validate, verify-or-write — and maps every failure to
its exit code. No step hides inside another step.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

ENTRY = "E09: Slot 1 is haunted. Slot 2 works fine. The toaster does not know why either."

MIN_ENTRY_CHARS = 1
MAX_ENTRY_CHARS = 120
OUTPUT_DIR = Path("/output")
ENTRY_FILENAME = "entry.txt"


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
    """Entry must be a non-empty one-liner within the platform character limit.

    Returns the formatted single line; raises ValueError on any violation
    so a bad entry fails loudly instead of writing a wrong file.
    """
    if not isinstance(text, str):
        raise ValueError("entry must be a string")
    formatted = format_entry(text)
    if not MIN_ENTRY_CHARS <= len(formatted) <= MAX_ENTRY_CHARS:
        raise ValueError(
            f"entry length {len(formatted)} outside "
            f"{MIN_ENTRY_CHARS}..{MAX_ENTRY_CHARS}"
        )
    return formatted


def _fsync_dir(directory):
    """Best-effort fsync of a directory so a rename survives a crash.

    Directory fsync is not supported on every filesystem, so an OSError
    here is tolerated — the file itself was already fsynced before the
    rename, which is the part that must not fail silently.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


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
        _fsync_dir(path.parent)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _parse_args(argv):
    """Parse the command line and return the parsed arguments.

    The CLI has exactly one flag: --verify, which validates the entry
    text and writes nothing. Keeping the parser in its own helper means
    main() never touches argparse directly, and the flag set can be
    inspected or tested without running the whole program. ``argv`` is
    passed straight through to parse_args so tests can inject it; when
    it is None, argparse reads sys.argv as usual.
    """
    parser = argparse.ArgumentParser(
        description="Write the competition entry.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="only validate the entry text, do not write any file",
    )
    return parser.parse_args(argv)


def _ensure_output_dir(directory):
    """Create the output directory if needed and return it.

    Creates missing parents as well, and succeeds silently when the
    directory already exists, so repeated runs are idempotent. Any
    OSError (for example a permission problem, or a file sitting where
    the directory should be) is left to the caller: main() turns it
    into a one-line diagnostic on stderr plus exit code 1, instead of
    letting a traceback leak to the user.
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def main(argv=None):
    """Orchestrate one run: parse, validate, verify-or-write.

    Steps, in order: parse the arguments; validate the fixed entry
    text; in --verify mode report the entry as valid and stop; otherwise
    ensure the output directory exists and write the entry atomically.
    Returns 0 on success and 1 on any validation, directory, or write
    failure, with the reason printed to stderr. main() does no work
    itself beyond calling the helpers and mapping failures to codes.
    """
    args = _parse_args(argv)
    try:
        entry = validate_entry(ENTRY)
    except ValueError as exc:
        print(f"invalid entry: {exc}", file=sys.stderr)
        return 1
    if args.verify:
        print(f"entry valid: {len(entry)} characters, single line, no trailing newline")
        return 0
    try:
        out_dir = _ensure_output_dir(OUTPUT_DIR)
    except OSError as exc:
        print(f"cannot create output directory {OUTPUT_DIR}: {exc}", file=sys.stderr)
        return 1
    try:
        write_entry_atomic(out_dir / ENTRY_FILENAME, entry)
    except OSError as exc:
        print(f"cannot write entry: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    # Propagate main()'s exit code so a failed write/validation is
    # visible to the caller instead of silently exiting 0.
    sys.exit(main())
