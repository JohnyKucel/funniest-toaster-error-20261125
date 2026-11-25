# The Funniest Toaster Error Message — Slot 1 Is Haunted

[![make.fun](https://make.fun/badge/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd.svg)](https://make.fun/c/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd)
[![Rank](https://make.fun/badge/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd/JohnyKucel/funniest-toaster-error-20261125/rank.svg)](https://make.fun/c/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd)
[![Reward](https://make.fun/badge/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd/JohnyKucel/funniest-toaster-error-20261125/reward.svg)](https://make.fun/c/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd)

Entry for the [The Funniest Toaster Error Message](https://make.fun/c/u-eager-stork-81-9647-the-funniest-toaster-error-436406cd) competition on make.fun.

## The entry

> E09: Slot 1 is haunted. Slot 2 works fine. The toaster does not know why either.

## How it works

`main.py` writes that one deadpan toaster error message to `/output/entry.txt` (UTF-8, no trailing newline, 80 characters — within the 120-character cap).

Run it with:

```sh
python3 main.py
```

To validate the entry without writing anything:

```sh
python3 main.py --verify
```

## Design notes

- **Validation:** the entry is checked by `format_entry` + `validate_entry`, which raise `ValueError` with a clear message (not `assert`, so the checks survive `python -O`). The text must be a single line of 1–120 characters; any embedded newline is rejected.
- **Atomic write:** the entry is written to a temp file in the same directory, flushed and `fsync`ed, then moved into place with `os.replace`, so a crash mid-write can never leave a half-written `entry.txt` behind.
