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

    QPushButton.danger:pressed {
        background-color: #a93226;
    }

    QPushButton.danger:disabled {
        background-color: #2d2d2d;
        color: #666666;
        border-color: #3d3d3d;
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
        border: none;
        background-color: transparent;
        padding: 0px;
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

    /* Combo Box - Enhanced Styling */
    QComboBox {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 200px;
        min-height: 20px;
        color: #ffffff;
        font-size: 11pt;
    }

    QComboBox:hover {
        border-color: #f9e79f;
        background-color: #505050;
    }

    QComboBox:focus {
        border-color: #f9e79f;
        background-color: #505050;
    }

    QComboBox:disabled {
        background-color: #2d2d2d;
        color: #666666;
        border-color: #3d3d3d;
    }

    QComboBox::drop-down {
        border: none;
        width: 25px;
        background-color: transparent;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }

    QComboBox::down-arrow {
        image: none;
        border: 2px solid #888888;
        border-top: none;
        border-left: none;
        width: 6px;
        height: 6px;
        margin-right: 8px;
    }

    QComboBox::down-arrow:hover {
        border-color: #f9e79f;
    }

    QComboBox::down-arrow:disabled {
        border-color: #555555;
    }

    /* Combo Box Dropdown - Modern Design */
    QComboBox QAbstractItemView {
        background-color: #353535;
        border: 2px solid #f9e79f;
        border-radius: 8px;
        selection-background-color: #f9e79f;
        selection-color: #2c3e50;
        outline: none;
        color: #ffffff;
        padding: 8px;
        font-size: 11pt;
        show-decoration-selected: 1;
        alternate-background-color: #404040;
    }

    QComboBox QAbstractItemView::item {
        background-color: transparent;
        border: none;
        padding: 12px 16px;
        margin: 2px 4px;
        border-radius: 6px;
        min-height: 20px;
        color: #ffffff;
    }

    QComboBox QAbstractItemView::item:hover {
        background-color: #505050;
        color: #ffffff;
        border: 1px solid #606060;
    }

    QComboBox QAbstractItemView::item:selected {
        background-color: #f9e79f;
        color: #2c3e50;
        font-weight: bold;
        border: 1px solid #f4d03f;
    }

    QComboBox QAbstractItemView::item:disabled {
        color: #f9e79f;
        background-color: #2d2d2d;
        font-style: normal;
        font-weight: bold;
        text-align: center;
        border-top: 1px solid #505050;
        border-bottom: 1px solid #505050;
        margin: 6px 2px;
        padding: 8px 16px;
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

    /* Custom Message Box Styles */
    QFrame#messageBoxContent {
        background-color: #2d2d2d;
        border-radius: 0px;
        border-top: 1px solid #404040;
        border-left: 1px solid #404040;
        border-right: 1px solid #404040;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
    }

    QLabel#messageBoxTitle {
        color: #f9e79f;
        font-weight: bold;
        font-size: 14pt;
    }

    QLabel#messageBoxText {
        color: #ffffff;
        font-size: 11pt;
        line-height: 1.4;
    }

    QFrame#messageBoxButtons {
        background-color: #1e1e1e;
        border-radius: 0px;
        border-top: 1px solid #404040;
        border-bottom: 1px solid #404040;
        border-left: 1px solid #404040;
        border-right: 1px solid #404040;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }

    QPushButton#primaryButton {
        background-color: #f9e79f;
        border-color: #f9e79f;
        color: #2c3e50;
        font-weight: bold;
        min-width: 80px;
        padding: 8px 16px;
    }

    QPushButton#primaryButton:hover {
        background-color: #f7dc6f;
        border-color: #f7dc6f;
    }

    QPushButton#primaryButton:pressed {
        background-color: #f4d03f;
    }

    QPushButton#secondaryButton {
        background-color: #404040;
        border-color: #505050;
        color: #ffffff;
        font-weight: bold;
        min-width: 80px;
        padding: 8px 16px;
    }

    QPushButton#secondaryButton:hover {
        background-color: #505050;
        border-color: #606060;
    }

    QPushButton#secondaryButton:pressed {
        background-color: #353535;
    }

    /* Frame Styling for ISO Downloader */
    QFrame#selectionFrame {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 8px;
        margin: 2px;
    }

    QFrame#progressFrame {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 8px;
        margin: 2px;
    }

    /* Partition Scheme Selection Styling */
    QPushButton[checkable="true"] {
        background-color: #404040;
        border: 2px solid #505050;
        border-radius: 8px;
        padding: 0px;
        text-align: center;
        font-weight: normal;
        min-height: 100px;
    }

    QPushButton[checkable="true"]:hover {
        background-color: #505050;
        border-color: #f9e79f;
    }

    QPushButton[checkable="true"]:checked {
        background-color: #3d3d2a;
        border-color: #f9e79f;
        border-width: 3px;
    }

    /* Ensure labels inside checkable buttons have no borders and proper spacing */
    QPushButton[checkable="true"] QLabel {
        background-color: transparent;
        border: none;
        margin: 0;
        padding: 2px;
        line-height: 1.4;
    }
    """
