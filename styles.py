# Updated styles.py
def get_etcher_style():
    return """
    QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
        font-size: 11pt;
    }

    QMainWindow {
        background-color: #1e1e1e;
    }

    /* Buttons */
    QPushButton {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        min-height: 16px;
        min-width: 80px;
    }

    QPushButton:hover {
        background-color: #505050;
        border-color: #606060;
    }

    QPushButton:pressed {
        background-color: #353535;
    }

    QPushButton:disabled {
        background-color: #2d2d2d;
        color: #666666;
        border-color: #3d3d3d;
    }

    QPushButton.primary {
        background-color: #f9e79f;
        border-color: #f9e79f;
        color: #2c3e50;
        font-weight: bold;
    }

    QPushButton.primary:hover {
        background-color: #f7dc6f;
        border-color: #f7dc6f;
    }

    QPushButton.primary:pressed {
        background-color: #f4d03f;
    }

    QPushButton.danger {
        background-color: #e74c3c;
        border-color: #e74c3c;
        color: #ffffff;
    }

    QPushButton.danger:hover {
        background-color: #c0392b;
        border-color: #c0392b;
    }

    /* Progress Bar */
    QProgressBar {
        border: 2px solid #404040;
        border-radius: 8px;
        text-align: center;
        background-color: #2d2d2d;
        color: #ffffff;
        font-weight: bold;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: #f9e79f;
        border-radius: 6px;
        color: #2c3e50;
    }

    /* Labels */
    QLabel {
        color: #ffffff;
        border: none; /* Ensure QLabels have no border by default */
        background-color: transparent; /* Ensure no background color by default */
        padding: 0px; /* Ensure no padding by default */
    }

    .title {
        font-size: 18pt;
        font-weight: bold;
        color: #f9e79f;
    }

    .subtitle {
        font-size: 12pt;
        color: #cccccc;
    }

    .step-title {
        font-size: 14pt;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .step-description {
        font-size: 10pt;
        color: #aaaaaa;
        margin-bottom: 12px;
    }

    /* Line Edits */
    QLineEdit {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 6px;
        padding: 8px;
        color: #ffffff;
        min-height: 20px;
    }

    QLineEdit:focus {
        border-color: #f9e79f;
    }

    QLineEdit:read-only {
        background-color: #353535;
        color: #cccccc;
    }

    /* Combo Box */
    QComboBox {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 6px;
        padding: 8px;
        min-width: 200px;
        min-height: 20px;
    }

    QComboBox:hover {
        border-color: #606060;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }

    QComboBox QAbstractItemView {
        background-color: #404040;
        border: 1px solid #505050;
        selection-background-color: #f9e79f;
        selection-color: #2c3e50;
    }

    /* Text Edit (for logs) */
    QTextEdit {
        background-color: #1a1a1a;
        border: 1px solid #404040;
        border-radius: 6px;
        color: #ffffff;
        font-family: "Consolas", "Monaco", "Courier New", monospace;
        font-size: 9pt;
    }

    /* Frame styles */
    QFrame {
        border: none;
    }

    /* About Widget specific styles */
    QFrame[class="info-frame"] {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 8px;
        padding: 20px;
    }

    QFrame[class="credits-frame"] {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 8px;
        padding: 15px;
    }
    """