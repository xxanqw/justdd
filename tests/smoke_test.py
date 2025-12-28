#!/usr/bin/env python3
import sys


def main() -> int:
    try:
        import justdd.constants as c
    except Exception as exc:
        print(
            "smoke-test FAIL: failed to import justdd.constants:", exc, file=sys.stderr
        )
        return 2

    try:
        print("smoke-test OK:", getattr(c, "__name__", repr(c)))
    except Exception as exc:
        print(
            "smoke-test FAIL: unexpected error while validating module:",
            exc,
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
