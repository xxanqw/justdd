from __future__ import annotations

import logging
import os
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from .gui.main_window import JustDDApp

logger = logging.getLogger(__name__)


def _set_qt_attributes() -> None:
    val = getattr(Qt, "AA_EnableHighDpiScaling", None)
    if val is not None:
        try:
            QApplication.setAttribute(val, True)
        except Exception:
            logger.debug("Failed to set Qt.AA_EnableHighDpiScaling", exc_info=True)

    val = getattr(Qt, "AA_UseHighDpiPixmaps", None)
    if val is not None:
        try:
            QApplication.setAttribute(val, True)
        except Exception:
            logger.debug("Failed to set Qt.AA_UseHighDpiPixmaps", exc_info=True)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    _set_qt_attributes()

    if argv is None:
        argv = sys.argv

    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.wayland.textinput=false")
    os.environ.setdefault(
        "XDG_CURRENT_DESKTOP", os.environ.get("XDG_CURRENT_DESKTOP", "")
    )

    try:
        app = QApplication(list(argv))
    except Exception as exc:
        logger.error("Failed to initialize QApplication: %s", exc, exc_info=True)
        return 1

    try:
        try:
            app.setStyle("Fusion")
        except Exception:
            logger.debug("Failed to apply Qt 'Fusion' style.", exc_info=True)

        window = JustDDApp()
        window.show()

        return app.exec()
    except Exception as exc:
        logger.exception("Unhandled exception in application main loop: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
