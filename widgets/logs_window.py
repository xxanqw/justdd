# widgets/logs_window.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class LogsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JustDD - Process Logs")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Process Logs")
        title_label.setProperty("class", "title")
        title_label.setStyleSheet("color: #f9e79f; font-size: 18pt; font-weight: bold;")
        
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_button)
        
        layout.addLayout(header_layout)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.logs_text)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        footer_layout.addWidget(close_button)
        
        layout.addLayout(footer_layout)
    
    def append_log(self, message):
        self.logs_text.append(message)
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        self.logs_text.clear()
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()