import webbrowser

import requests
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ..constants import __APP_NAME__, __AUTHOR__, __GITHUB_URL__, __VERSION__


class AboutWidget(QDialog):
    def __init__(self, parent=None, image_url=None):
        super().__init__(parent)
        self.setWindowTitle("About JustDD")
        self.setModal(True)
        self.setFixedSize(350, 280)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.Dialog)
        self.image_url = "https://cdn.xserv.pp.ua/files/justdd/icon.png"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 18, 30, 18)
        layout.setSpacing(10)

        if self.image_url:
            image_label = QLabel()
            pixmap = self._load_pixmap_from_url(self.image_url)
            if pixmap:
                image_label.setPixmap(
                    pixmap.scaledToWidth(96, Qt.TransformationMode.SmoothTransformation)
                )
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(image_label)

        name_label = QLabel(__APP_NAME__)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        version_label = QLabel(f"Version {__VERSION__}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        author_label = QLabel(f"by {__AUTHOR__}")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        github_btn = QPushButton("View on GitHub")
        github_btn.clicked.connect(lambda: webbrowser.open(__GITHUB_URL__))
        btn_layout.addWidget(github_btn)

        about_qt_btn = QPushButton("About Qt")
        about_qt_btn.clicked.connect(lambda: QMessageBox.aboutQt(self))
        btn_layout.addWidget(about_qt_btn)

        layout.addLayout(btn_layout)

    def _load_pixmap_from_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        except Exception:
            return None

    def closeEvent(self, event):
        event.accept()
