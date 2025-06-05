from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
import sys
import subprocess

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About JustDD")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setFixedSize(350, 380)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
                font-size: 11pt;
            }
            QLabel {
                background-color: transparent;
                border: none;
                color: #ffffff;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(12)
        
        icon_container = QWidget()
        icon_container.setFixedHeight(120)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_path = resource_path("images/icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_container)
        
        name_label = QLabel("JustDD")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #f9e79f; margin: 3px 0;")
        layout.addWidget(name_label)
        
        version_label = QLabel("Version 1.3")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 12pt; color: #cccccc; margin: 3px 0;")
        layout.addWidget(version_label)
        
        author_label = QLabel("by xxanqw")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_label.setStyleSheet("font-size: 10pt; color: #aaaaaa; margin: 3px 0;")
        layout.addWidget(author_label)
        
        layout.addStretch()
        
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        github_button = QPushButton("View on GitHub")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #f9e79f;
                border: 1px solid #f9e79f;
                color: #2c3e50;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 20px;
                min-height: 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #f7dc6f;
                border-color: #f7dc6f;
            }
            QPushButton:pressed {
                background-color: #f4d03f;
            }
        """)
        github_button.clicked.connect(self.open_github)
        github_button.setMinimumHeight(35)
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                border: 1px solid #505050;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                min-height: 16px;
                min-width: 100px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #606060;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
        """)
        close_button.clicked.connect(self.close)
        close_button.setMinimumHeight(35)
        
        buttons_layout.addWidget(github_button)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
    
    def open_github(self):
        try:
            subprocess.run(['xdg-open', 'https://github.com/xxanqw/justdd'], check=False)
        except:
            pass
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()
