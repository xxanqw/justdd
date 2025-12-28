import os
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PartitionSchemeSelectionPage(QWidget):
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_scheme = None
        self.setup_ui()

    def setup_ui(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(60)

        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch(1)

        try:
            from .icons import make_icon_widget

            icon_widget = make_icon_widget("fa5s.cog", color="#f9e79f", size=64)
            try:
                icon_widget.setFixedSize(64, 64)
            except Exception:
                pass
        except Exception:
            # Fallback to a neutral placeholder (no emoji)
            icon_widget = QLabel()
            icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                icon_widget.setFixedSize(64, 64)
            except Exception:
                pass

        title_label = QLabel("Partition Scheme")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_label)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_widget.setFixedWidth(450)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 40, 0, 40)
        right_layout.setSpacing(25)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scheme_frame = QFrame()
        scheme_frame.setFixedSize(400, 280)
        scheme_layout = QVBoxLayout(scheme_frame)
        scheme_layout.setContentsMargins(20, 15, 20, 15)
        scheme_layout.setSpacing(15)

        title = QLabel("Choose Partition Scheme")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.gpt_button = QPushButton()
        self.gpt_button.setFixedSize(170, 100)
        self.gpt_button.setCheckable(True)
        self.gpt_button.clicked.connect(lambda: self.select_scheme("gpt"))

        gpt_layout = QVBoxLayout()
        gpt_layout.setContentsMargins(10, 15, 10, 10)
        gpt_layout.setSpacing(8)

        gpt_header = QWidget()
        gpt_header_layout = QHBoxLayout(gpt_header)
        gpt_header_layout.setContentsMargins(0, 0, 0, 0)
        gpt_header_layout.setSpacing(8)
        try:
            from .icons import make_icon_widget

            gpt_icon = make_icon_widget("fa5s.wrench", color="#f9e79f", size=18)
        except Exception:
            # Fallback to a neutral placeholder (no emoji)
            gpt_icon = QLabel()
            gpt_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                gpt_icon.setFixedSize(18, 18)
            except Exception:
                pass

        gpt_title = QLabel("GPT (UEFI)")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        gpt_title.setFont(font)
        gpt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gpt_header_layout.addWidget(gpt_icon)
        gpt_header_layout.addWidget(gpt_title)

        gpt_desc = QLabel("For modern computers\n(2010+)\nSupports drives >2TB")
        font = QFont()
        font.setPointSize(8)
        gpt_desc.setFont(font)
        gpt_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gpt_layout.addWidget(gpt_header)
        gpt_layout.addWidget(gpt_desc)
        gpt_layout.addStretch()
        self.gpt_button.setLayout(gpt_layout)

        # MBR (BIOS) Option
        self.mbr_button = QPushButton()
        self.mbr_button.setFixedSize(170, 100)
        self.mbr_button.setCheckable(True)
        self.mbr_button.clicked.connect(lambda: self.select_scheme("mbr"))

        mbr_layout = QVBoxLayout()
        mbr_layout.setContentsMargins(10, 15, 10, 10)
        mbr_layout.setSpacing(8)

        mbr_header = QWidget()
        mbr_header_layout = QHBoxLayout(mbr_header)
        mbr_header_layout.setContentsMargins(0, 0, 0, 0)
        mbr_header_layout.setSpacing(8)
        try:
            from .icons import make_icon_widget

            mbr_icon = make_icon_widget("fa5s.wrench", color="#3498db", size=18)
        except Exception:
            # Fallback to a neutral placeholder (no emoji)
            mbr_icon = QLabel()
            mbr_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                mbr_icon.setFixedSize(18, 18)
            except Exception:
                pass

        mbr_title = QLabel("MBR (BIOS)")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        mbr_title.setFont(font)
        mbr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mbr_header_layout.addWidget(mbr_icon)
        mbr_header_layout.addWidget(mbr_title)

        mbr_desc = QLabel("For older computers\n(pre-2010)\nLimited to 2TB drives")
        font = QFont()
        font.setPointSize(8)
        mbr_desc.setFont(font)
        mbr_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mbr_layout.addWidget(mbr_header)
        mbr_layout.addWidget(mbr_desc)
        mbr_layout.addStretch()
        self.mbr_button.setLayout(mbr_layout)
        # Disable MBR option if 'ms-sys' is not available on the system
        try:
            from shutil import which

            ms_ok = which("ms-sys") is not None
        except Exception:
            ms_ok = False
        try:
            self.mbr_button.setEnabled(bool(ms_ok))
            if not ms_ok:
                self.mbr_button.setToolTip("ms-sys not found; MBR creation disabled")
                if self.mbr_button.isChecked():
                    self.gpt_button.setChecked(True)
            else:
                self.mbr_button.setToolTip("")
        except Exception:
            pass

        buttons_layout.addWidget(self.gpt_button)
        buttons_layout.addWidget(self.mbr_button)

        info_label = QLabel(
            "Choose GPT for most modern computers, or MBR for older systems"
        )
        font = QFont()
        font.setPointSize(9)
        font.setItalic(True)
        info_label.setFont(font)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)

        scheme_layout.addWidget(title)
        scheme_layout.addLayout(buttons_layout)
        scheme_layout.addWidget(info_label)

        right_layout.addWidget(scheme_frame)

        container_layout.addWidget(left_widget)
        container_layout.addWidget(right_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 0, 50, 50)
        main_layout.addStretch(1)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1)

    def select_scheme(self, scheme):
        self.selected_scheme = scheme
        if scheme == "gpt":
            self.gpt_button.setChecked(True)
            self.mbr_button.setChecked(False)
        else:
            self.mbr_button.setChecked(True)
            self.gpt_button.setChecked(False)
        self.selection_changed.emit()

    def get_selected_scheme(self):
        return self.selected_scheme

    def has_valid_selection(self):
        return self.selected_scheme is not None

    def reset_selection(self):
        self.selected_scheme = None
        self.gpt_button.setChecked(False)
        self.mbr_button.setChecked(False)


class SelectionPage(QWidget):
    selection_changed = Signal()
    flash_requested = Signal()

    def _update_mbr_availability(self):
        try:
            from shutil import which

            ok = which("ms-sys") is not None
        except Exception:
            ok = False

        try:
            self.mbr_radio.setEnabled(bool(ok))
            if not ok:
                self.mbr_radio.setToolTip("ms-sys not found; MBR creation disabled")
                if self.mbr_radio.isChecked():
                    # Fall back to the safe default
                    self.gpt_radio.setChecked(True)
            else:
                self.mbr_radio.setToolTip("")
        except Exception:
            pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.iso_path = None
        self.iso_type = "unknown"
        self.iso_details = {}
        self.selected_drive = None
        self.partition_scheme = "gpt"
        self._screen_handle = None
        self._window_event_filter_installed = False
        self.setup_ui()
        try:
            self.refresh_drives()
        except Exception:
            pass

    def setup_ui(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        def _make_icon(
            icon_name: str, fallback: str = "", size: int = 36, fixed: int = 48
        ):
            try:
                from .icons import make_icon_widget

                icon_widget = make_icon_widget(icon_name, color="#ffffff", size=size)
                try:
                    icon_widget.setFixedSize(fixed, fixed)
                except Exception:
                    pass
                return icon_widget
            except Exception:
                # Fallback to a neutral placeholder (no emoji)
                lbl = QLabel("")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                font = QFont()
                font.setPointSize(size - 4 if size > 20 else 20)
                lbl.setFont(font)
                try:
                    lbl.setFixedSize(fixed, fixed)
                except Exception:
                    pass
                return lbl

        img_icon = _make_icon("fa5s.save", "", size=36, fixed=48)
        drive_icon = _make_icon("fa5s.hdd", "", size=36, fixed=48)
        flash_icon = _make_icon("fa5s.bolt", "", size=36, fixed=48)

        self.select_image_button = QPushButton("Select Image")
        self.select_image_button.setMinimumWidth(220)
        self.select_image_button.setMaximumWidth(260)
        self.select_image_button.setMinimumHeight(48)
        self.select_image_button.clicked.connect(self.browse_file)

        self.file_label = QLabel("Please select an ISO")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setMinimumWidth(220)
        self.file_label.setMaximumWidth(260)

        self.iso_thumb = QLabel()
        self.iso_thumb.setFixedSize(48, 48)
        self.iso_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iso_thumb.hide()

        self.iso_name_label = QLabel("")
        self.iso_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iso_name_label.setMinimumWidth(220)
        self.iso_name_label.setMaximumWidth(260)
        self.iso_name_label.hide()

        self.iso_meta_label = QLabel("")
        self.iso_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iso_meta_label.setMinimumWidth(220)
        self.iso_meta_label.setMaximumWidth(260)
        self.iso_meta_label.hide()

        self.select_target_button = QPushButton("Select target")
        self.select_target_button.setMinimumWidth(220)
        self.select_target_button.setMaximumWidth(260)
        self.select_target_button.setMinimumHeight(48)
        self.select_target_button.clicked.connect(self.open_drive_selector_dialog)

        self.selected_drive_label = QLabel("No drive selected")
        self.selected_drive_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_drive_label.setMinimumWidth(220)
        self.selected_drive_label.setMaximumWidth(260)

        self.flash_button = QPushButton("Flash!")
        self.flash_button.setMinimumWidth(220)
        self.flash_button.setMaximumWidth(260)
        self.flash_button.setMinimumHeight(48)
        self.flash_button.setEnabled(False)
        self.flash_button.clicked.connect(self._on_flash_clicked)

        step_container = QWidget()
        step_layout = QHBoxLayout(step_container)
        step_layout.setContentsMargins(8, 20, 20, 20)
        step_layout.setSpacing(36)
        step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        col_left = QWidget()
        col_left.setMinimumWidth(260)
        col_left.setMaximumWidth(280)
        col_left_layout = QVBoxLayout(col_left)
        col_left_layout.setContentsMargins(0, 0, 0, 0)
        col_left_layout.setSpacing(12)
        col_left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col_left_layout.addWidget(img_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        col_left_layout.addWidget(
            self.select_image_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_left_layout.addWidget(
            self.file_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_left_layout.addWidget(
            self.iso_name_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_left_layout.addWidget(
            self.iso_meta_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_left_layout.addStretch(1)

        col_center = QWidget()
        col_center.setMinimumWidth(260)
        col_center.setMaximumWidth(280)
        col_center_layout = QVBoxLayout(col_center)
        col_center_layout.setContentsMargins(0, 0, 0, 0)
        col_center_layout.setSpacing(12)
        col_center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col_center_layout.addWidget(drive_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        col_center_layout.addWidget(
            self.select_target_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_center_layout.addWidget(
            self.selected_drive_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_center_layout.addStretch(1)

        col_right = QWidget()
        col_right.setMinimumWidth(260)
        col_right.setMaximumWidth(280)
        col_right_layout = QVBoxLayout(col_right)
        col_right_layout.setContentsMargins(0, 0, 0, 0)
        col_right_layout.setSpacing(12)
        col_right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col_right_layout.addWidget(flash_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        col_right_layout.addWidget(
            self.flash_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        col_right_layout.addStretch(1)

        # Add columns with equal stretch so their centers are anchored at thirds.
        step_layout.addWidget(col_left)
        step_layout.addWidget(col_center)
        step_layout.addWidget(col_right)

        container_layout.addWidget(
            step_container, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Keep an internal (hidden) drive list used by the refresh/selection logic
        self.drive_list = QListWidget()
        self.drive_list.setFixedHeight(260)
        self.drive_list.itemSelectionChanged.connect(self._on_drive_selection_changed)
        self.drive_list.hide()

        right_widget = QFrame(self)
        right_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_widget.setObjectName("partitionOverlay")
        right_widget.setStyleSheet(
            "QFrame#partitionOverlay { background-color: rgba(43,43,43,220); border-radius: 6px; border: 1px solid rgba(80,80,80,200); }"
            "QFrame#partitionOverlay QLabel { color: #ffffff; }"
        )
        right_widget.setMinimumWidth(140)
        right_widget.setMaximumWidth(260)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ptitle = QLabel("Partition Scheme")
        ptitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gpt_radio = QRadioButton("GPT (UEFI)")
        self.mbr_radio = QRadioButton("MBR (BIOS)")
        self.gpt_radio.setChecked(True)

        # Reflection of changes to interested parties
        self.gpt_radio.toggled.connect(lambda: self.selection_changed.emit())
        self.mbr_radio.toggled.connect(lambda: self.selection_changed.emit())

        right_layout.addWidget(ptitle, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addWidget(self.gpt_radio, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addWidget(self.mbr_radio, alignment=Qt.AlignmentFlag.AlignHCenter)
        # Keep some spacing, but do not add this popup to the main layout.
        right_layout.addStretch(1)
        right_widget.hide()
        self._partition_widget = right_widget
        try:
            self._update_mbr_availability()
        except Exception:
            pass

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.addWidget(container, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.selection_changed.connect(self.update_button_states)
        self.update_button_states()

    def open_drive_selector_dialog(self):
        try:
            self.refresh_drives()
        except Exception:
            pass

        dlg = QDialog(self)
        dlg.setWindowTitle("Select Target Drive")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)
        list_widget = QListWidget()

        for i in range(self.drive_list.count()):
            orig = self.drive_list.item(i)
            new_item = QListWidgetItem(orig.text())
            new_item.setData(
                Qt.ItemDataRole.UserRole, orig.data(Qt.ItemDataRole.UserRole)
            )
            list_widget.addItem(new_item)

        if list_widget.count() == 0:
            layout.addWidget(QLabel("No removable USB drives found"))
        else:
            list_widget.setCurrentRow(0)
            layout.addWidget(list_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            sel = list_widget.currentItem()
            if sel:
                drive_data = sel.data(Qt.ItemDataRole.UserRole)
                if drive_data:
                    self.selected_drive = drive_data
                    try:
                        name = drive_data.get("name", "Selected Drive")
                    except Exception:
                        name = (
                            str(drive_data)
                            if drive_data is not None
                            else "Selected Drive"
                        )
                    self.selected_drive_label.setText(name)
                    self.selection_changed.emit()

        try:
            dlg.deleteLater()
        except Exception:
            pass

    def update_button_states(self):
        # Enable the "Select target" control once an image is chosen
        self.select_target_button.setEnabled(bool(self.iso_path))

        # Show the selected drive's friendly name on the target button if present
        sd = getattr(self, "selected_drive", None)
        if sd and isinstance(sd, dict):
            try:
                name = sd.get("name", "Select target")
            except Exception:
                name = "Select target"
            self.select_target_button.setText(name)
        else:
            self.select_target_button.setText("Select target")

        # Enable the Flash button only when both an ISO and a drive are selected
        flash_enabled = self.has_valid_selection()
        self.flash_button.setEnabled(flash_enabled)
        try:
            self.select_image_button.setStyleSheet("")
            self.select_target_button.setStyleSheet("")
            self.flash_button.setStyleSheet("")
        except Exception:
            pass

        # Show partition options only for Windows ISOs (as a floating popup).
        if getattr(self, "iso_type", "unknown") == "windows":
            try:
                self._update_mbr_availability()
            except Exception:
                pass
            try:
                self._show_partition_popover()
            except Exception:
                pass
        else:
            try:
                self._hide_partition_popover()
            except Exception:
                pass

        # Update the small selected drive label under the target control
        sd = getattr(self, "selected_drive", None)
        if sd and isinstance(sd, dict):
            self.selected_drive_label.setText(sd.get("name", "Selected Drive"))
        elif sd is not None:
            try:
                self.selected_drive_label.setText(str(sd))
            except Exception:
                self.selected_drive_label.setText("Selected Drive")
        else:
            self.selected_drive_label.setText("No drive selected")

    def _show_partition_popover(self):
        if not hasattr(self, "_partition_widget") or self._partition_widget is None:
            return
        try:
            try:
                if (
                    getattr(self, "iso_meta_label", None)
                    and self.iso_meta_label.isVisible()
                ):
                    anchor = self.iso_meta_label
                elif (
                    getattr(self, "iso_name_label", None)
                    and self.iso_name_label.isVisible()
                ):
                    anchor = self.iso_name_label
                else:
                    anchor = self.select_image_button
            except Exception:
                anchor = self.select_image_button

            center_local = anchor.mapTo(self, anchor.rect().center())
            bottom_local = anchor.mapTo(self, anchor.rect().bottomLeft())

            try:
                self._partition_widget.adjustSize()
            except Exception:
                pass
            pop_hint = self._partition_widget.sizeHint()
            pop_width = (
                pop_hint.width()
                if pop_hint.isValid()
                else self._partition_widget.width()
            )

            try:
                left_local = self.select_image_button.mapTo(
                    self, self.select_image_button.rect().bottomLeft()
                )
                x = left_local.x()
            except Exception:
                x = max(8, center_local.x() - (pop_width // 2))
            y = bottom_local.y() + 8  # small gap

            try:
                pop_height = (
                    pop_hint.height()
                    if pop_hint.isValid()
                    else self._partition_widget.height()
                )
                page_h = self.height()
                if y + pop_height > page_h - 8:
                    alt_y = bottom_local.y() - pop_height - 8
                    if alt_y >= 8:
                        y = alt_y
                    else:
                        y = max(8, page_h - pop_height - 8)
            except Exception:
                pass

            try:
                btn_w = self.select_image_button.width()
                # match the button width exactly to ensure visual consistency
                self._partition_widget.setFixedWidth(btn_w)
                pop_width = self._partition_widget.width()
            except Exception:
                pass

            try:
                page_w = self.width()
                page_h = self.height()
                pop_height = (
                    pop_hint.height()
                    if pop_hint.isValid()
                    else self._partition_widget.height()
                )
                if x < 8:
                    x = 8
                if x + pop_width > page_w - 8:
                    x = page_w - pop_width - 8
                if y + pop_height > page_h - 8:
                    alt_y = bottom_local.y() - pop_height - 8
                    if alt_y >= 8:
                        y = alt_y
                    else:
                        y = max(8, page_h - pop_height - 8)
                if y < 8:
                    y = 8
            except Exception:
                pass

            self._partition_widget.move(x, y)
            self._partition_widget.raise_()
            self._partition_widget.show()
            try:
                self._position_partition_overlay()
            except Exception:
                pass

            try:
                self._attach_screen_change_handler()
            except Exception:
                pass
            try:
                self._attach_window_event_filter()
            except Exception:
                pass
        except Exception:
            try:
                self._partition_widget.show()
            except Exception:
                pass

    def _hide_partition_popover(self):
        try:
            pop = getattr(self, "_partition_widget", None)
            if pop and pop.isVisible():
                pop.hide()
        except Exception:
            pass
        try:
            self._detach_screen_change_handler()
        except Exception:
            pass
        try:
            self._detach_window_event_filter()
        except Exception:
            pass

    def _attach_screen_change_handler(self):
        try:
            win = self.window()
            if win is None:
                return
            wh = win.windowHandle()
            if wh is None:
                return
            if getattr(self, "_screen_handle", None) is wh:
                return
            try:
                wh.screenChanged.connect(self._on_screen_changed)
                self._screen_handle = wh
            except Exception:
                pass
        except Exception:
            pass

    def _detach_screen_change_handler(self):
        try:
            wh = getattr(self, "_screen_handle", None)
            if wh is not None:
                try:
                    wh.screenChanged.disconnect(self._on_screen_changed)
                except Exception:
                    pass
            self._screen_handle = None
        except Exception:
            pass

    def _on_screen_changed(self, screen):
        try:
            self._hide_partition_popover()
        except Exception:
            pass

    def _attach_window_event_filter(self):
        try:
            win = self.window()
            if not win or getattr(self, "_window_event_filter_installed", False):
                return
            try:
                win.installEventFilter(self)
                self._window_event_filter_installed = True
            except Exception:
                pass
        except Exception:
            pass

    def _detach_window_event_filter(self):
        try:
            win = self.window()
            if not win or not getattr(self, "_window_event_filter_installed", False):
                return
            try:
                win.removeEventFilter(self)
            except Exception:
                pass
            self._window_event_filter_installed = False
        except Exception:
            pass

    def _position_partition_overlay(self):
        try:
            pop = getattr(self, "_partition_widget", None)
            if not pop or not pop.isVisible():
                return
            try:
                if (
                    getattr(self, "iso_meta_label", None)
                    and self.iso_meta_label.isVisible()
                ):
                    anchor = self.iso_meta_label
                elif (
                    getattr(self, "iso_name_label", None)
                    and self.iso_name_label.isVisible()
                ):
                    anchor = self.iso_name_label
                else:
                    anchor = self.file_label
            except Exception:
                anchor = self.file_label
            center_local = anchor.mapTo(self, anchor.rect().center())
            bottom_local = anchor.mapTo(self, anchor.rect().bottomLeft())
            try:
                pop.adjustSize()
            except Exception:
                pass
            pop_hint = pop.sizeHint()
            pop_width = pop_hint.width() if pop_hint.isValid() else pop.width()
            pop_height = pop_hint.height() if pop_hint.isValid() else pop.height()
            try:
                left_local = self.select_image_button.mapTo(
                    self, self.select_image_button.rect().bottomLeft()
                )
                x = left_local.x()
            except Exception:
                x = max(8, center_local.x() - (pop_width // 2))
            y = bottom_local.y() + 8
            try:
                page_w = self.width()
                page_h = self.height()
                if x < 8:
                    x = 8
                if x + pop_width > page_w - 8:
                    x = page_w - pop_width - 8
                if y + pop_height > page_h - 8:
                    alt_y = bottom_local.y() - pop_height - 8
                    if alt_y >= 8:
                        y = alt_y
                    else:
                        y = max(8, page_h - pop_height - 8)
                if y < 8:
                    y = 8
            except Exception:
                pass
            pop.move(x, y)
            pop.raise_()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            from PySide6.QtCore import QEvent

            move_ev = getattr(QEvent, "Move", None)
            resize_ev = getattr(QEvent, "Resize", None)
            if obj is self.window() and (
                (move_ev is not None and event.type() == move_ev)
                or (resize_ev is not None and event.type() == resize_ev)
            ):
                try:
                    if (
                        getattr(self, "_partition_widget", None)
                        and self._partition_widget.isVisible()
                    ):
                        self._position_partition_overlay()
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def _accent_color(self):
        """Return the widget palette's highlight color as a hex string, falling back to an Etcher-like cyan.

        Access QPalette roles defensively so static analyzers (and unusual Qt stubs)
        can't flag the code. If the Highlight role is missing for any reason, we
        fall back to a reasonable hard-coded accent.
        """
        try:
            from PySide6.QtGui import QPalette

            # Some static analyzers / type stubs don't expose enum members on
            # QPalette; use getattr and check for None to be defensive.
            role = getattr(QPalette, "Highlight", None)
            if role is not None:
                try:
                    c = self.palette().color(role)
                    return c.name()
                except Exception:
                    # Best-effort: ignore color retrieval failures silently
                    pass
        except Exception:
            # If importing or attribute lookup fails, continue to fallback
            pass

        # Final fallback if palette lookup wasn't possible or failed.
        return "#00b5ff"

    def _on_flash_clicked(self):
        """Emit a signal that indicates the user pressed the Flash button in the UI."""
        if self.has_valid_selection():
            self.flash_requested.emit()

    def browse_file(self):
        dialog = QFileDialog(self, "Select ISO File")
        _dont = getattr(QFileDialog, "DontUseNativeDialog", None)
        if _dont is not None:
            try:
                dialog.setOption(_dont, True)
            except Exception:
                pass
        _existing = getattr(QFileDialog, "ExistingFile", None)
        if _existing is not None:
            try:
                dialog.setFileMode(_existing)
            except Exception:
                pass

        dialog.setNameFilter(
            "Disk Images (*.iso *.img *.bin *.raw *.dd *.vmdk *.vhd *.dmg *.zip *.gz *.xz *.bz2 *.zst);;All Files (*)"
        )

        if dialog.exec():
            files = dialog.selectedFiles()
            file_path = files[0] if files else ""
            if file_path:
                self.iso_path = file_path
                try:
                    from ..logic.iso_detector import ISODetector

                    self.iso_type, self.iso_details = ISODetector.detect_iso_type(
                        file_path
                    )
                except Exception:
                    self.iso_type = "unknown"
                    self.iso_details = {}
                if self.iso_type == "windows":
                    try:
                        from shutil import which

                        from PySide6.QtWidgets import QMessageBox

                        if which("ntfs-3g") is None:
                            QMessageBox.warning(
                                self,
                                "ntfs-3g required",
                                "The 'ntfs-3g' utility is required to work with Windows ISOs.\nPlease install 'ntfs-3g' and try again.",
                            )
                            try:
                                self.reset_selection()
                            except Exception:
                                pass
                            return
                    except Exception:
                        pass
                # Update UI: show elided filename on the Select button and metadata below
                filename = os.path.basename(file_path)
                metrics = self.select_image_button.fontMetrics()
                elided_filename = metrics.elidedText(
                    filename, Qt.TextElideMode.ElideMiddle, 220
                )
                # Put the elided filename on the main Select Image button and keep the
                # full path as a tooltip so users can see the exact selection.
                try:
                    self.select_image_button.setText(elided_filename)
                    self.select_image_button.setToolTip(filename)
                except Exception:
                    pass
                # Show detected metadata (name and size) in the file label under the button
                name = self.iso_details.get("name", "")
                size = self.iso_details.get("size", "")
                if name or size:
                    meta = name if name else ""
                    if size:
                        meta = f"{meta} • {size}" if meta else size
                    self.file_label.setText(meta)
                    try:
                        self.file_label.show()
                    except Exception:
                        pass
                else:
                    # Fall back to showing the elided filename as metadata
                    self.file_label.setText(elided_filename)
                # Try to set icon
                try:
                    if self.iso_type == "linux":
                        pass  # Do not show Linux icon
                    elif self.iso_type == "windows":
                        pass  # Do not show Windows icon
                    else:
                        pass  # Do not show generic file icon
                except Exception:
                    pass  # Do not show any icon on error
                # Show partition options only for Windows ISOs
                if self.iso_type == "windows":
                    try:
                        self._show_partition_popover()
                    except Exception:
                        pass
                else:
                    try:
                        self._hide_partition_popover()
                    except Exception:
                        pass
                self.selection_changed.emit()

    def refresh_drives(self):
        self.drive_list.clear()
        try:
            result = subprocess.run(
                ["lsblk", "-dno", "NAME,RM,TYPE,SIZE,MOUNTPOINT,LABEL,MODEL"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )

            drives_found = []

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 4:
                    name = parts[0]
                    rm = parts[1]
                    dtype = parts[2]
                    size = parts[3]
                    mountpoint = (
                        parts[4] if len(parts) > 4 and parts[4] != "" else "Not mounted"
                    )
                    label = parts[5] if len(parts) > 5 and parts[5] != "" else ""
                    model = " ".join(parts[6:]) if len(parts) > 6 else "Unknown Drive"

                    if rm == "1" and dtype == "disk":
                        device_path = f"/dev/{name}"

                        drive_name = (
                            model if model != "Unknown Drive" else f"USB Drive ({name})"
                        )
                        if label:
                            drive_name = f"{drive_name} - {label}"

                        drives_found.append(
                            {
                                "device_path": device_path,
                                "name": drive_name,
                                "size": size,
                                "mountpoint": mountpoint,
                                "full_info": f"{device_path} ({size}) - {mountpoint}",
                            }
                        )

            if drives_found:
                for drive in drives_found:
                    item = QListWidgetItem()

                    primary_text = drive["name"]
                    secondary_text = f"{drive['device_path']} • {drive['size']} • {drive['mountpoint']}"

                    display_text = f"{primary_text}\n{secondary_text}"
                    item.setText(display_text)

                    item.setData(Qt.ItemDataRole.UserRole, drive)

                    item.setForeground(QColor("#ffffff"))

                    self.drive_list.addItem(item)
            else:
                item = QListWidgetItem("No removable USB drives found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor("#888888"))
                self.drive_list.addItem(item)

        except Exception as e:
            item = QListWidgetItem(f"Error scanning drives: {str(e)}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#e74c3c"))
            self.drive_list.addItem(item)

    def _on_drive_selection_changed(self):
        current_item = self.drive_list.currentItem()
        if current_item:
            drive_data = current_item.data(Qt.ItemDataRole.UserRole)
            if drive_data:
                self.selected_drive = drive_data
        else:
            self.selected_drive = None
        self.selection_changed.emit()

    def get_selected_iso(self):
        return self.iso_path

    def get_selected_drive(self):
        if self.selected_drive:
            return self.selected_drive["device_path"], self.selected_drive["full_info"]
        return None, None

    def get_iso_type(self):
        return self.iso_type

    def get_iso_details(self):
        return self.iso_details

    def get_selected_scheme(self):
        try:
            if (
                getattr(self, "mbr_radio", None)
                and self.mbr_radio.isEnabled()
                and self.mbr_radio.isChecked()
            ):
                return "mbr"
        except Exception:
            pass
        return "gpt"

    def has_valid_selection(self):
        drive, _ = self.get_selected_drive()
        return bool(self.iso_path) and bool(drive)

    def reset_selection(self):
        self.iso_path = None
        self.iso_type = "unknown"
        self.iso_details = {}
        self.selected_drive = None

        self.file_label.setText("Please select an ISO")
        try:
            self.file_label.setFont(self.font())
        except Exception:
            try:
                self.file_label.setFont(QFont())
            except Exception:
                pass
        # Reset the primary Select Image button text, tooltip and any applied styling
        try:
            self.select_image_button.setText("Select Image")
            self.select_image_button.setToolTip("")
            # Clear any inline styling so Fusion defaults (palette) are used again
            self.select_image_button.setStyleSheet("")
        except Exception:
            pass

        self.iso_name_label.setText("")
        try:
            self.iso_name_label.hide()
        except Exception:
            pass

        self.iso_meta_label.setText("")
        try:
            self.iso_meta_label.hide()
        except Exception:
            pass

        # Hide the thumbnail (if shown)
        try:
            self.iso_thumb.hide()
        except Exception:
            pass

        # Reset target and flash controls (use Fusion defaults)
        try:
            self.select_target_button.setText("Select target")
            self.select_target_button.setEnabled(False)
            self.select_target_button.setStyleSheet("")
        except Exception:
            pass

        try:
            self.flash_button.setEnabled(False)
            self.flash_button.setStyleSheet("")
        except Exception:
            pass

        self.drive_list.clear()
        try:
            self.refresh_drives()
        except Exception:
            pass

        self._hide_partition_popover()
        self.gpt_radio.setChecked(True)
        self.selection_changed.emit()


class CompactStepIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 1
        self.total_steps = 3
        self.is_windows_mode = False
        self.setFixedHeight(25)
        self.setFixedWidth(160)  # Increased width for 4 steps

    def set_windows_mode(self, enabled):
        self.is_windows_mode = enabled
        self.total_steps = 4 if enabled else 3
        self.setFixedWidth(160 if enabled else 120)
        self.update()

    def set_step(self, step):
        self.current_step = step
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        active_color = QColor("#f9e79f")
        inactive_color = QColor("#505050")
        completed_color = QColor("#f9e79f")

        width = self.width()
        height = self.height()

        step_width = width // self.total_steps
        circle_radius = 8
        y_center = height // 2

        for i in range(1, self.total_steps + 1):
            x_center = (i - 1) * step_width + step_width // 2

            if i < self.current_step:
                color = completed_color
            elif i == self.current_step:
                color = active_color
            else:
                color = inactive_color

            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                x_center - circle_radius,
                y_center - circle_radius,
                circle_radius * 2,
                circle_radius * 2,
            )

            if i < self.total_steps:
                line_color = (
                    completed_color if i < self.current_step else inactive_color
                )
                painter.setPen(line_color)
                painter.drawLine(
                    x_center + circle_radius,
                    y_center,
                    x_center + step_width - circle_radius,
                    y_center,
                )

            painter.setPen(
                QColor("#000000") if color != inactive_color else QColor("#ffffff")
            )
            font = painter.font()
            font.setPointSize(7)
            painter.setFont(font)
            if i < self.current_step:
                painter.drawText(x_center - 4, y_center + 3, "✓")
            else:
                painter.drawText(x_center - 3, y_center + 3, str(i))


class ISOSelectionPage(QWidget):
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.iso_path = None
        self.iso_type = "unknown"
        self.iso_details = {}
        self.setup_ui()

    def setup_ui(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(60)

        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch(1)

        # Icon (file) using qtawesome when available; fallback to emoji if not.
        try:
            from .icons import make_icon_widget

            # Larger file icon and centered for better visual balance
            icon_widget = make_icon_widget("fa5s.file", color="#f9e79f", size=64)
        except Exception:
            # Fallback to neutral placeholder (no emoji)
            icon_widget = QLabel()
            icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                icon_widget.setFixedSize(64, 64)
            except Exception:
                pass

        title_label = QLabel("Select ISO File")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure the icon itself is centered in the left column
        left_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_label)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_widget.setFixedWidth(450)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 40, 0, 40)
        right_layout.setSpacing(25)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        file_frame = QFrame()
        file_frame.setFixedSize(400, 280)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(0)

        # Compact ISO summary card (filename + detector info)
        self.iso_info_card = QFrame()
        self.iso_info_card.setObjectName("isoInfoCard")
        # ISO selection card (filename at top, centered logo + info below, action at bottom)
        # Keep the card background consistent with other dark frames and allow it to expand
        # Make the info card expand vertically while preserving rounded corners.
        self.iso_info_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        iso_card_layout = QVBoxLayout(self.iso_info_card)
        iso_card_layout.setContentsMargins(12, 12, 12, 12)
        iso_card_layout.setSpacing(8)

        # Filename row (elided when too long)
        # Initial prompt instructing the user to select an ISO (centered)
        self.iso_file_label = QLabel("Please select an ISO")
        self.iso_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iso_file_label.setWordWrap(False)
        self.iso_file_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Backwards compatibility: some code expects `file_path_label`
        self.file_path_label = self.iso_file_label

        # Centered logo + stacked info under it (logo centered, info centered below)
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(6)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.iso_thumb = QLabel()
        self.iso_thumb.setFixedSize(48, 48)
        self.iso_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Hide logo until an ISO is selected
        self.iso_thumb.hide()

        self.iso_name_label = QLabel("")
        self.iso_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.iso_meta_label = QLabel("")
        self.iso_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_layout.addWidget(self.iso_thumb, alignment=Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(
            self.iso_name_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        logo_layout.addWidget(
            self.iso_meta_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        iso_card_layout.addWidget(self.iso_file_label)
        iso_card_layout.addWidget(logo_container, stretch=1)

        # Put the Browse button inside the card so the card expands with it
        browse_button = QPushButton("Browse for Image")
        browse_button.setProperty("class", "primary")
        browse_button.clicked.connect(self.browse_file)
        browse_button.setMinimumHeight(40)
        browse_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Hide the detail rows until an ISO is chosen; the card itself remains visible
        self.iso_name_label.hide()
        self.iso_meta_label.hide()

        # Add the selection card and anchor the Browse button at the bottom of the frame.
        # Give the info card stretch so it expands to the bottom while the Browse button
        # remains anchored.
        file_layout.addWidget(self.iso_info_card, 1)
        # Add small spacing so the card doesn't touch the button directly and rounded
        # corners are visible.
        file_layout.addSpacing(12)
        file_layout.addWidget(browse_button)

        right_layout.addWidget(file_frame)

        container_layout.addWidget(left_widget)
        container_layout.addWidget(right_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 0, 50, 50)
        main_layout.addStretch(1)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1)

    def browse_file(self):
        # Use a QFileDialog instance and set DontUseNativeDialog via a guarded
        # call to `setOption`. Using an instance avoids passing an `options`
        # argument whose typing can confuse static analyzers.
        dialog = QFileDialog(self, "Select ISO File")

        # Guarded attempt to ask Qt to use the non-native (Qt) dialog so our
        # stylesheet is applied consistently.
        _dont = getattr(QFileDialog, "DontUseNativeDialog", None)
        if _dont is not None:
            try:
                dialog.setOption(_dont, True)
            except Exception:
                # If the API stub/platform doesn't accept the option, ignore it.
                pass

        # Prefer an existing-file selection mode when present.
        _existing = getattr(QFileDialog, "ExistingFile", None)
        if _existing is not None:
            try:
                dialog.setFileMode(_existing)
            except Exception:
                pass

        dialog.setNameFilter(
            "Disk Images (*.iso *.img *.bin *.raw *.dd *.vmdk *.vhd *.dmg *.zip *.gz *.xz *.bz2 *.zst);;All Files (*)"
        )

        # Exec the dialog and read the selected file if the user accepted.
        file_path = ""
        if dialog.exec():
            selected = dialog.selectedFiles()
            file_path = selected[0] if selected else ""
        if file_path:
            self.iso_path = file_path
            filename = os.path.basename(file_path)

            # Lazy import to avoid circular imports if the application imports
            # pages from this module while app module imports pages later.
            from ..logic.iso_detector import ISODetector  # local import

            self.iso_type, self.iso_details = ISODetector.detect_iso_type(file_path)

            # Use elided text so very long filenames don't break the layout
            metrics = self.iso_file_label.fontMetrics()
            elided_filename = metrics.elidedText(
                filename, Qt.TextElideMode.ElideMiddle, 360
            )
            self.iso_file_label.setText(elided_filename)
            font = QFont()
            font.setPointSize(11)
            font.setBold(True)
            self.iso_file_label.setFont(font)

            # Update detector details (icon + name + size) and reveal them
            self._update_iso_type_display()
            self.iso_thumb.show()
            self.iso_name_label.show()
            self.iso_meta_label.show()
            # align filename left when a real ISO is selected
            self.iso_file_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            # Update detector details (icon + name + size)
            self._update_iso_type_display()

            self.selection_changed.emit()

    def _update_iso_type_display(self):
        # Update the ISO type display and populate the compact info card.
        if self.iso_type == "unknown":
            name = "Unknown ISO type"
            color = "#f39c12"
            icon_name = "fa5s.exclamation-triangle"
            fallback = ""
        elif self.iso_type == "linux":
            name = self.iso_details.get("name", "Linux")
            color = "#f9e79f"
            icon_name = "fa5b.linux"
            fallback = ""
        else:
            name = self.iso_details.get("name", "Windows")
            color = "#3498db"
            icon_name = "fa5b.windows"
            fallback = ""

        # Set name and metadata (size)
        size = self.iso_details.get("size", "")
        metrics = self.iso_name_label.fontMetrics()
        elided = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 260)
        self.iso_name_label.setText(elided)
        self.iso_meta_label.setText(size)

        # Try to render a centered, larger icon safely
        try:
            from .icons import set_label_icon

            # Avoid using emoji fallbacks; prefer neutral empty label instead
            set_label_icon(self.iso_thumb, icon_name, 48, color, "")
        except Exception:
            try:
                self.iso_thumb.setText("")
            except Exception:
                pass

        # Reveal the stacked info under the logo
        try:
            self.iso_name_label.show()
            self.iso_meta_label.show()
            self.iso_info_card.show()
        except Exception:
            try:
                self.iso_thumb.show()
                self.iso_name_label.show()
                self.iso_meta_label.show()
            except Exception:
                pass

    def get_selected_iso(self):
        return self.iso_path

    def get_iso_type(self):
        return self.iso_type

    def get_iso_details(self):
        return self.iso_details

    def has_valid_selection(self):
        return self.iso_path is not None


class DriveSelectionPage(QWidget):
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_drives()

    def setup_ui(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(60)

        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch(1)

        try:
            from .icons import make_icon_widget

            icon_label = make_icon_widget("fa5s.hdd", color="#f9e79f", size=48)
        except Exception:
            # Fallback to neutral placeholder (no emoji)
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                icon_label.setFixedSize(48, 48)
            except Exception:
                pass

        title_label = QLabel("Select ISO File")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_label)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_widget.setFixedWidth(450)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 40, 0, 40)
        right_layout.setSpacing(20)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        drive_frame = QFrame()
        drive_frame.setFixedSize(400, 280)
        drive_layout = QVBoxLayout(drive_frame)
        drive_layout.setContentsMargins(15, 15, 15, 15)
        drive_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_label = QLabel("Available USB Drives:")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header_label.setFont(font)

        refresh_button = QPushButton("Refresh")
        try:
            from .icons import set_button_icon

            set_button_icon(refresh_button, "fa5s.sync", size=18, text="Refresh")
        except Exception:
            refresh_button.setText("Refresh")
        refresh_button.setFixedHeight(32)
        refresh_button.clicked.connect(self.refresh_drives)
        refresh_button.setToolTip("Refresh drive list")

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)

        self.drive_list = QListWidget()
        self.drive_list.setFixedHeight(200)
        self.drive_list.itemSelectionChanged.connect(self.on_drive_selection_changed)

        drive_layout.addLayout(header_layout)
        drive_layout.addWidget(self.drive_list)

        right_layout.addWidget(drive_frame)

        container_layout.addWidget(left_widget)
        container_layout.addWidget(right_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 0, 50, 50)
        main_layout.addStretch(1)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1)

    def refresh_drives(self):
        self.drive_list.clear()

        try:
            result = subprocess.run(
                ["lsblk", "-dno", "NAME,RM,TYPE,SIZE,MOUNTPOINT,LABEL,MODEL"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )

            drives_found = []

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 4:
                    name = parts[0]
                    rm = parts[1]
                    dtype = parts[2]
                    size = parts[3]
                    mountpoint = (
                        parts[4] if len(parts) > 4 and parts[4] != "" else "Not mounted"
                    )
                    label = parts[5] if len(parts) > 5 and parts[5] != "" else ""
                    model = " ".join(parts[6:]) if len(parts) > 6 else "Unknown Drive"

                    if rm == "1" and dtype == "disk":
                        device_path = f"/dev/{name}"

                        drive_name = (
                            model if model != "Unknown Drive" else f"USB Drive ({name})"
                        )
                        if label:
                            drive_name = f"{drive_name} - {label}"

                        drives_found.append(
                            {
                                "device_path": device_path,
                                "name": drive_name,
                                "size": size,
                                "mountpoint": mountpoint,
                                "full_info": f"{device_path} ({size}) - {mountpoint}",
                            }
                        )

            if drives_found:
                for drive in drives_found:
                    item = QListWidgetItem()

                    primary_text = drive["name"]
                    secondary_text = f"{drive['device_path']} • {drive['size']} • {drive['mountpoint']}"

                    display_text = f"{primary_text}\n{secondary_text}"
                    item.setText(display_text)

                    item.setData(Qt.ItemDataRole.UserRole, drive)

                    item.setForeground(QColor("#ffffff"))

                    self.drive_list.addItem(item)
            else:
                item = QListWidgetItem("No removable USB drives found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor("#888888"))
                self.drive_list.addItem(item)

        except Exception as e:
            item = QListWidgetItem(f"Error scanning drives: {str(e)}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#e74c3c"))
            self.drive_list.addItem(item)

        self.selection_changed.emit()

    def on_drive_selection_changed(self):
        # Handle drive selection changes
        self.selection_changed.emit()

    def get_selected_drive(self):
        # Get the currently selected drive info
        current_item = self.drive_list.currentItem()
        if current_item:
            drive_data = current_item.data(Qt.ItemDataRole.UserRole)
            if drive_data:
                return drive_data["device_path"], drive_data["full_info"]
        return None, None

    def has_valid_selection(self):
        # Check if a valid drive is selected
        current_item = self.drive_list.currentItem()
        if current_item:
            drive_data = current_item.data(Qt.ItemDataRole.UserRole)
            return drive_data is not None
        return False


class FlashPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.iso_path = ""
        self.drive_path = ""
        self.drive_display = ""
        self.iso_type = "unknown"
        self.iso_details = {}
        self.flashing = False
        self.error_occurred = False
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 0, 50, 50)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a wide container for centering content
        container = QWidget()
        container.setMinimumWidth(600)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            from PySide6.QtGui import QPalette

            from .icons import make_icon_widget

            # Use system accent color for the icon
            accent_color = None
            try:
                accent_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            except Exception:
                accent_color = "#00b5ff"  # fallback to blue

            # Create an icon widget using the accent color (ensure variable is always defined)
            icon_widget = make_icon_widget("fa5s.bolt", color=accent_color, size=48)
            try:
                icon_widget.setFixedSize(48, 48)
            except Exception:
                pass

        except Exception:
            # Fallback to neutral placeholder (no emoji)
            icon_widget = QLabel()
            icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                icon_widget.setFixedSize(48, 48)
            except Exception:
                pass

        flashing_label = QLabel("Flashing...")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        flashing_label.setFont(font)
        flashing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Preparing to flash...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(400)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(400)
        self.progress_bar.setMinimumHeight(30)

        container_layout.addStretch(1)
        container_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(
            flashing_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        container_layout.addWidget(
            self.status_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        container_layout.addWidget(
            self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter
        )
        container_layout.addStretch(1)

        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_flash_info(
        self, iso_path, drive_path, drive_display, iso_type="unknown", iso_details=None
    ):
        self.iso_path = iso_path
        self.drive_path = drive_path
        self.drive_display = drive_display
        self.iso_type = iso_type
        self.iso_details = iso_details or {}

        # If no ISO is provided, reset the flash summary UI to sensible defaults
        # and avoid performing file detection or icon operations.
        if not iso_path:
            self.flashing = False
            self.progress_bar.setValue(0)
            self.status_label.setText("Ready to flash...")
            f = QFont()
            f.setPointSize(12)
            f.setBold(True)
            self.status_label.setFont(f)
            return

        self.flashing = False
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to flash...")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)

        filename = os.path.basename(iso_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."

    def start_flash(self):
        self.flashing = True

        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing to flash...")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        self.status_label.setFont(f)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def flash_completed(self, success, message):
        self.flashing = False

        # No title_label to reset

        if success:
            self.status_label.setText("Flash completed successfully!")
            f = QFont()
            f.setPointSize(12)
            f.setBold(True)
            self.status_label.setFont(f)
            self.error_occurred = False
        else:
            self.status_label.setText(f"Flash failed: {message}")
            f = QFont()
            f.setPointSize(12)
            f.setBold(True)
            self.status_label.setFont(f)
            self.error_occurred = True
            # Use default message box for error
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Flash failed: {message}")
            # Do NOT set any button visibility here; handled by main window

    def is_flashing(self):
        return self.flashing


class SuccessPage(QWidget):
    flash_another_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(30)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            from PySide6.QtGui import QPalette

            from .icons import make_icon_widget

            # Use system accent color for the icon
            accent_color = None
            try:
                accent_color = self.palette().color(QPalette.ColorRole.Highlight).name()
            except Exception:
                accent_color = "#00b5ff"  # fallback to blue

            icon_widget = make_icon_widget(
                "fa5s.check-circle", color=accent_color, size=48
            )
            try:
                icon_widget.setFixedSize(48, 48)
            except Exception:
                pass
        except Exception:
            icon_widget = QLabel()
            icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                icon_widget.setFixedSize(48, 48)
            except Exception:
                pass
        # Ensure the icon appearance is clean for both real widgets and fallbacks
        try:
            font = QFont()
            font.setPointSize(48)
            icon_widget.setFont(font)
        except Exception:
            pass

        title_label = QLabel("Flash Completed Successfully!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title_label.setFont(font)

        message_label = QLabel("Your image has been successfully written to the drive.")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        message_label.setFont(font)

        container_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)
        container_layout.addWidget(message_label)
        container_layout.addSpacing(20)

        main_layout.addWidget(container)


__all__ = [
    "PartitionSchemeSelectionPage",
    "CompactStepIndicator",
    "ISOSelectionPage",
    "DriveSelectionPage",
    "FlashPage",
    "SuccessPage",
]
