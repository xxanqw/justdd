from __future__ import annotations

__all__ = ["__version__", "constants"]

try:
    from . import constants
    from .constants import __VERSION__ as __version__
except Exception:
    try:
        import importlib.metadata as _metadata
    except Exception:
        _metadata = None

    if _metadata is not None:
        try:
            __version__ = _metadata.version("justdd")
        except Exception:
            __version__ = "0.0.0"
    else:
        __version__ = "0.0.0"
