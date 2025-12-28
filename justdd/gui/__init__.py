"""
GUI package for JustDD.

This package provides convenient imports for the UI components that were
extracted into the `gui` package. It attempts package-relative imports
first (recommended) and falls back to absolute imports in case the package
is executed in a different import context during the refactor.

Exports:
- EtcherWizardApp
- PartitionSchemeSelectionPage
- CompactStepIndicator
- ISOSelectionPage
- DriveSelectionPage
- FlashPage
- SuccessPage
"""

__all__ = [
    "EtcherWizardApp",
    "PartitionSchemeSelectionPage",
    "CompactStepIndicator",
    "ISOSelectionPage",
    "DriveSelectionPage",
    "FlashPage",
    "SuccessPage",
]

# Import the main window class (package-relative only)
try:
    from .main_window import EtcherWizardApp  # type: ignore
except Exception:
    EtcherWizardApp = None  # type: ignore

# Import page widgets (package-relative only)
try:
    from .pages import (  # type: ignore
        CompactStepIndicator,
        DriveSelectionPage,
        FlashPage,
        ISOSelectionPage,
        PartitionSchemeSelectionPage,
        SuccessPage,
    )
except Exception:
    PartitionSchemeSelectionPage = None  # type: ignore
    CompactStepIndicator = None  # type: ignore
    ISOSelectionPage = None  # type: ignore
    DriveSelectionPage = None  # type: ignore
    FlashPage = None  # type: ignore
    SuccessPage = None  # type: ignore
