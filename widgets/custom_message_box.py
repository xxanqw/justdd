from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor


class CustomMessageBox(QDialog):
    # Message box types
    Information = 0
    Warning = 1
    Critical = 2
    Question = 3
    
    # Standard buttons
    Ok = 0x00000400
    Cancel = 0x00400000
    Yes = 0x00004000
    No = 0x00010000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_value = None
        self.setup_ui()
        self.setModal(True)
        
    def setup_ui(self):
        self.setFixedSize(450, 200)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("messageBoxContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 25, 30, 20)
        content_layout.setSpacing(15)
        
        # Header layout (icon + title)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel()
        self.title_label.setObjectName("messageBoxTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label, 1)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setObjectName("messageBoxText")
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        font = QFont()
        font.setPointSize(11)
        self.message_label.setFont(font)
        
        content_layout.addLayout(header_layout)
        content_layout.addWidget(self.message_label)
        content_layout.addStretch()
        
        # Button frame
        button_frame = QFrame()
        button_frame.setObjectName("messageBoxButtons")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(10)
        
        self.button_layout = button_layout
        
        main_layout.addWidget(content_frame, 1)
        main_layout.addWidget(button_frame)
        
    def set_icon(self, icon_type):
        """Set the icon based on message type"""
        icons = {
            self.Information: "ℹ️",
            self.Warning: "⚠️", 
            self.Critical: "❌",
            self.Question: "❓"
        }
        
        colors = {
            self.Information: "#3498db",
            self.Warning: "#f39c12",
            self.Critical: "#e74c3c", 
            self.Question: "#f9e79f"
        }
        
        icon_text = icons.get(icon_type, "ℹ️")
        color = colors.get(icon_type, "#3498db")
        
        self.icon_label.setText(icon_text)
        self.icon_label.setStyleSheet(f"font-size: 20pt; color: {color};")
        
    def set_text(self, title, message):
        """Set the title and message text"""
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.setWindowTitle(title)
        
    def add_button(self, text, button_type, is_default=False):
        """Add a button to the message box"""
        button = QPushButton(text)
        button.setMinimumSize(80, 32)
        
        if button_type in [self.Ok, self.Yes]:
            button.setObjectName("primaryButton")
        elif button_type in [self.Cancel, self.No]:
            button.setObjectName("secondaryButton")
            
        if is_default:
            button.setDefault(True)
            button.setFocus()
            
        button.clicked.connect(lambda: self.button_clicked(button_type))
        
        # Add stretch before first button to push all buttons to the right
        if self.button_layout.count() == 0:
            self.button_layout.addStretch()
            
        self.button_layout.addWidget(button)
        
        return button
        
    def button_clicked(self, button_type):
        """Handle button clicks"""
        self.result_value = button_type
        self.accept()
        
    def exec(self):
        """Execute the dialog and return the result"""
        super().exec()
        return self.result_value
        
    @staticmethod
    def information(parent, title, message):
        """Show an information message box"""
        msg_box = CustomMessageBox(parent)
        msg_box.set_icon(CustomMessageBox.Information)
        msg_box.set_text(title, message)
        msg_box.add_button("OK", CustomMessageBox.Ok, True)
        return msg_box.exec()
        
    @staticmethod
    def warning(parent, title, message, buttons=None):
        """Show a warning message box"""
        if buttons is None:
            buttons = CustomMessageBox.Ok
            
        msg_box = CustomMessageBox(parent)
        msg_box.set_icon(CustomMessageBox.Warning)
        msg_box.set_text(title, message)
        
        if buttons == CustomMessageBox.Ok:
            msg_box.add_button("OK", CustomMessageBox.Ok, True)
        elif buttons == (CustomMessageBox.Yes | CustomMessageBox.No):
            msg_box.add_button("No", CustomMessageBox.No)
            msg_box.add_button("Yes", CustomMessageBox.Yes, True)
            
        return msg_box.exec()
        
    @staticmethod
    def critical(parent, title, message):
        """Show a critical error message box"""
        msg_box = CustomMessageBox(parent)
        msg_box.set_icon(CustomMessageBox.Critical)
        msg_box.set_text(title, message)
        msg_box.add_button("OK", CustomMessageBox.Ok, True)
        return msg_box.exec()
        
    @staticmethod
    def question(parent, title, message, buttons=None):
        """Show a question message box"""
        if buttons is None:
            buttons = CustomMessageBox.Yes | CustomMessageBox.No
            
        msg_box = CustomMessageBox(parent)
        msg_box.set_icon(CustomMessageBox.Question)
        msg_box.set_text(title, message)
        
        if buttons == (CustomMessageBox.Yes | CustomMessageBox.No):
            msg_box.add_button("No", CustomMessageBox.No)
            msg_box.add_button("Yes", CustomMessageBox.Yes, True)
            
        return msg_box.exec()
