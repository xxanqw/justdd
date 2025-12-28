"""
Simple LogManager for JustDD logic layer.

Responsibilities:
- Store recent log entries (in-memory) with timestamps and levels.
- Provide thread-safe append/get/clear operations.
- Allow registering callbacks for append and clear events so UI can update.
- Optional persistence to disk (manual save/load).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

DEFAULT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_MAX_ENTRIES = 10000


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str

    def formatted(self, ts_format: str = DEFAULT_TIMESTAMP_FORMAT) -> str:
        return f"{self.timestamp.strftime(ts_format)} [{self.level}] {self.message}"


class LogManager:
    def __init__(
        self,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        timestamp_format: str = DEFAULT_TIMESTAMP_FORMAT,
        persist_path: Optional[str] = None,
        auto_flush: bool = False,
    ) -> None:
        self._entries: List[LogEntry] = []
        self._lock = threading.Lock()
        self._append_callbacks: set[Callable[[str], None]] = set()
        self._clear_callbacks: set[Callable[[], None]] = set()

        self.max_entries = int(max_entries)
        self.timestamp_format = timestamp_format
        self.persist_path: Optional[Path] = Path(persist_path) if persist_path else None
        self.auto_flush = bool(auto_flush)

        if self.persist_path and self.persist_path.exists():
            try:
                self.load_from_file(self.persist_path)
            except Exception:
                pass

    def register_append_callback(self, callback: Callable[[str], None]) -> None:
        with self._lock:
            self._append_callbacks.add(callback)

    def unregister_append_callback(self, callback: Callable[[str], None]) -> None:
        with self._lock:
            self._append_callbacks.discard(callback)

    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._clear_callbacks.add(callback)

    def unregister_clear_callback(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._clear_callbacks.discard(callback)

    def append(self, message: str, level: str = "INFO", notify: bool = True) -> None:
        entry = LogEntry(
            timestamp=datetime.now(), level=str(level), message=str(message)
        )

        # Insert and trim in a threadsafe way, but call callbacks outside the lock
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.max_entries:
                # Keep only the most recent max_entries
                excess = len(self._entries) - self.max_entries
                if excess > 0:
                    del self._entries[0:excess]
            callbacks = list(self._append_callbacks)
            persist_path = self.persist_path if self.auto_flush else None

        if notify:
            formatted = entry.formatted(self.timestamp_format)
            for cb in callbacks:
                try:
                    cb(formatted)
                except Exception:
                    pass

        if persist_path:
            try:
                self._append_to_file(
                    persist_path, entry.formatted(self.timestamp_format)
                )
            except Exception:
                pass

    # Convenience wrappers
    def info(self, message: str, notify: bool = True) -> None:
        self.append(message, level="INFO", notify=notify)

    def warning(self, message: str, notify: bool = True) -> None:
        self.append(message, level="WARNING", notify=notify)

    def error(self, message: str, notify: bool = True) -> None:
        self.append(message, level="ERROR", notify=notify)

    def debug(self, message: str, notify: bool = True) -> None:
        self.append(message, level="DEBUG", notify=notify)

    def get_lines(self, most_recent: Optional[int] = None) -> List[str]:
        with self._lock:
            entries = list(self._entries)
        if most_recent is not None:
            entries = entries[-most_recent:]
        return [e.formatted(self.timestamp_format) for e in entries]

    def get_text(self, most_recent: Optional[int] = None) -> str:
        return "\n".join(self.get_lines(most_recent))

    def tail(self, n: int = 100) -> List[str]:
        return self.get_lines(most_recent=n)

    def clear(self, notify: bool = True) -> None:
        with self._lock:
            self._entries.clear()
            callbacks = list(self._clear_callbacks)
        if notify:
            for cb in callbacks:
                try:
                    cb()
                except Exception:
                    pass

        if self.persist_path and self.persist_path.exists():
            try:
                self.persist_path.unlink(missing_ok=True)
            except Exception:
                pass

    def _append_to_file(self, path: Path, line: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def save_to_file(self, path: Optional[str | Path] = None) -> None:
        target = Path(path) if path else self.persist_path
        if not target:
            raise ValueError("No persist path specified for saving logs.")
        target.parent.mkdir(parents=True, exist_ok=True)
        text = self.get_text()
        with open(target, "w", encoding="utf-8") as f:
            f.write(text)

    def load_from_file(self, path: Optional[str | Path] = None) -> None:
        target = Path(path) if path else self.persist_path
        if not target or not target.exists():
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                lines = [ln.rstrip("\n") for ln in f if ln.strip()]
            for line in lines:
                ts = datetime.now()
                level = "INFO"
                message = line
                try:
                    if " " in line:
                        possible_ts, rest = line.split(" ", 1)
                        message = line
                except Exception:
                    message = line
                with self._lock:
                    self._entries.append(
                        LogEntry(timestamp=ts, level=level, message=message)
                    )
            with self._lock:
                if len(self._entries) > self.max_entries:
                    self._entries = self._entries[-self.max_entries :]
        except Exception:
            pass

    def export_as_pairs(self) -> List[Tuple[datetime, str]]:
        """Return a list of (timestamp, formatted_line) tuples."""
        with self._lock:
            return [
                (e.timestamp, e.formatted(self.timestamp_format)) for e in self._entries
            ]


global_log_manager = LogManager()

__all__ = ["LogManager", "global_log_manager", "LogEntry"]
