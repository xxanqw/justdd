from __future__ import annotations

import sys
from typing import Optional

try:
    from .app import main
except (
    Exception
) as exc:
    raise RuntimeError(
        "Failed to import JustDD application. Ensure the package is installed "
        "and runtime dependencies (e.g., PySide6) are available."
    ) from exc


def _run(argv: Optional[list[str]] = None) -> int:
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(_run(sys.argv))
