from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..logic.steps import StepState


class StepCard(QWidget):
    clicked = Signal()

    def __init__(self, step_number: int, title: str, description: str, parent=None):
        super().__init__(parent)
        self.step_number = step_number
        self.title = title
        self.description = description
        self.state = StepState.WAITING

        self.setProperty("class", "StepCard")
        self.setup_ui()
        self.update_appearance()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()

        self.number_label = QLabel(str(self.step_number))
        self.number_label.setFixedSize(30, 30)
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        self.title_label = QLabel(self.title)
        self.title_label.setProperty("class", "step-title")

        self.desc_label = QLabel(self.description)
        self.desc_label.setProperty("class", "step-description")
        self.desc_label.setWordWrap(True)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)

        header_layout.addWidget(self.number_label)
        header_layout.addLayout(text_layout, 1)

        layout.addLayout(header_layout)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_widget)

    def set_state(self, state: StepState):
        self.state = state
        self.update_appearance()

    def update_appearance(self):
        if self.state == StepState.WAITING:
            self.setProperty("active", "false")
            self.setProperty("completed", "false")
            self.number_label.setText(str(self.step_number))
        elif self.state == StepState.ACTIVE:
            self.setProperty("active", "true")
            self.setProperty("completed", "false")
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            self.number_label.setFont(font)
            self.number_label.setText(str(self.step_number))
        elif self.state == StepState.COMPLETED:
            self.setProperty("active", "false")
            self.setProperty("completed", "true")
            self.number_label.setText("✓")
        elif self.state == StepState.ERROR:
            self.setProperty("active", "false")
            self.setProperty("completed", "false")
            self.number_label.setText("✗")
        try:
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass

    def add_content_widget(self, widget):
        self.content_layout.addWidget(widget)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
