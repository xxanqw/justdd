from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..logic.logs import global_log_manager


class LogsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JustDD - Process Logs")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(800, 600)

        self._append_callback = None
        self._clear_callback = None

        self.setup_ui()

        try:
            for line in global_log_manager.get_lines():
                self._append_to_ui(line)
        except Exception:
            pass

        try:
            global_log_manager.register_append_callback(self._on_append)
            global_log_manager.register_clear_callback(self._on_clear)
            self._append_callback = self._on_append
            self._clear_callback = self._on_clear
        except Exception:
            self._append_callback = None
            self._clear_callback = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        title_label = QLabel("Process Logs")
        title_label.setProperty("class", "title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_button)

        layout.addLayout(header_layout)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        footer_layout.addWidget(close_button)

        layout.addLayout(footer_layout)

    def _append_to_ui(self, line: str):
        try:
            self.logs_text.append(line)
            scrollbar = self.logs_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception:
            pass

    def _clear_ui(self):
        try:
            self.logs_text.clear()
        except Exception:
            pass

    def _on_append(self, line: str):
        try:
            QTimer.singleShot(0, lambda: self._append_to_ui(line))
        except Exception:
            pass

    def _on_clear(self):
        try:
            QTimer.singleShot(0, self._clear_ui)
        except Exception:
            pass

    def append_log(self, message: str):
        try:
            global_log_manager.append(message)
        except Exception:
            try:
                self._append_to_ui(message)
            except Exception:
                pass

    def clear_logs(self):
        try:
            global_log_manager.clear()
        except Exception:
            self._clear_ui()

    def closeEvent(self, event):
        try:
            if self._append_callback:
                global_log_manager.unregister_append_callback(self._append_callback)
                self._append_callback = None
        except Exception:
            pass

        try:
            if self._clear_callback:
                global_log_manager.unregister_clear_callback(self._clear_callback)
                self._clear_callback = None
        except Exception:
            pass

        self.hide()
        event.ignore()
