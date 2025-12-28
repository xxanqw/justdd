from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..logic.utils import send_notification
from .about_widget import AboutWidget
from .logs_window import LogsWindow
from .pages import (
    FlashPage,
    SelectionPage,
    SuccessPage,
)


class JustDDApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JustDD - USB Image Writer")

        self.iso_path = ""
        self.drive_path = ""
        self.drive_display = ""
        self.partition_scheme = "gpt"
        self.iso_page = None
        self.drive_page = None
        self.partition_scheme_page = None
        self.flash_worker = None
        self.current_page = 0
        self._shutdown_in_progress = False

        self.logs_window: Optional[LogsWindow] = LogsWindow()
        self.about_widget = AboutWidget(self)
        self.setup_ui()
        self.update_navigation_buttons()

    def closeEvent(self, event):
        if self._shutdown_in_progress:
            event.accept()
            return

        self._shutdown_in_progress = True

        if self.flash_worker and self.flash_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Flash in Progress",
                "A flash operation is currently in progress. Are you sure you want to exit?\n\n"
                "This will cancel the operation and may leave your drive in an unusable state.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                self._shutdown_in_progress = False
                event.ignore()
                return

            self._force_cleanup_worker()

        if self.logs_window:
            try:
                self.logs_window.close()
                self.logs_window = None
            except Exception:
                pass

        self._cleanup_all_resources()

        event.accept()

    def _force_cleanup_worker(self):
        if self.flash_worker:
            try:
                self.flash_worker.progress.disconnect()
                self.flash_worker.status_update.disconnect()
                self.flash_worker.log_message.disconnect()
                self.flash_worker.finished.disconnect()
                self.flash_worker.requestInterruption()
                if not self.flash_worker.wait(2000):
                    self.flash_worker.terminate()
                    if not self.flash_worker.wait(1000):
                        pass
                self.flash_worker = None
            except Exception:
                pass
                self.flash_worker = None

    def _cleanup_all_resources(self):
        try:
            if self.flash_worker:
                self._force_cleanup_worker()

            if self.update_checker:
                try:
                    self.update_checker.cleanup_thread()
                    self.update_checker = None
                except Exception:
                    pass

            QApplication.processEvents()

        except Exception:
            pass

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.resize(900, 500)
        self.setMinimumSize(900, 500)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        self.selection_page = SelectionPage()
        self.flash_page = FlashPage(self)
        self.success_page = SuccessPage()
        try:
            self.selection_page.flash_requested.connect(self.start_flash)
        except Exception:
            pass

        self.selection_page.selection_changed.connect(self.update_navigation_buttons)

        self.success_page.flash_another_requested.connect(self.reset_to_start)

        self.stacked_widget.addWidget(self.selection_page)
        self.stacked_widget.addWidget(self.flash_page)
        self.stacked_widget.addWidget(self.success_page)

        footer_frame = QFrame()
        footer_frame.setFixedHeight(60)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(30, 10, 30, 10)
        footer_layout.setSpacing(15)

        left_buttons_layout = QHBoxLayout()

        logs_button = QPushButton("Show Logs")
        logs_button.setFixedSize(100, 35)
        logs_button.clicked.connect(self.show_logs)

        about_button = QPushButton("About")
        about_button.setFixedSize(80, 35)
        about_button.clicked.connect(self.show_about)

        left_buttons_layout.addWidget(logs_button)
        left_buttons_layout.addWidget(about_button)
        left_buttons_layout.addStretch()

        footer_layout.addLayout(left_buttons_layout)
        footer_layout.addStretch()

        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(15)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._back_to_selection)
        self.back_button.setMinimumHeight(35)
        self.back_button.setFixedWidth(80)

        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.go_forward)
        self.continue_button.setMinimumHeight(35)
        self.continue_button.setFixedWidth(100)

        self.flash_button = QPushButton("Flash!")
        self.flash_button.clicked.connect(self.start_flash)
        self.flash_button.setMinimumHeight(35)
        self.flash_button.setFixedWidth(100)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_flash)
        self.cancel_button.setMinimumHeight(35)
        self.cancel_button.setFixedWidth(80)

        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.cancel_button)
        nav_layout.addWidget(self.continue_button)
        nav_layout.addWidget(self.flash_button)

        footer_layout.addWidget(nav_container)

        layout.addWidget(self.stacked_widget, 1)
        layout.addWidget(footer_frame)

    def update_navigation_buttons(self):
        page = self.current_page
        is_flashing = self.flash_page.is_flashing()
        error_occurred = getattr(self.flash_page, "error_occurred", False)

        self.back_button.hide()
        self.continue_button.hide()
        self.flash_button.hide()
        self.cancel_button.hide()

        if page == 1 and error_occurred:
            self.back_button.show()
            return

        if is_flashing:
            self.cancel_button.show()
            return

        if page == 0:
            self.flash_button.hide()
            return

        if page == 1:
            self.back_button.show()
            return

        if page == 2:
            self.back_button.show()
            return

    def go_back(self):
        if self.current_page > 0:
            self.current_page = 0
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_navigation_buttons()

    def go_forward(self):
        if self.current_page == 0:
            if (
                getattr(self, "selection_page", None)
                and self.selection_page.has_valid_selection()
            ):
                self._prepare_flash_page()
                self.current_page = 1
                self.stacked_widget.setCurrentIndex(self.current_page)
                self.update_navigation_buttons()

    def _back_to_selection(self):
        self.current_page = 0
        self.stacked_widget.setCurrentIndex(self.current_page)
        self.update_navigation_buttons()

    def _prepare_flash_page(self):
        try:
            iso_path = self.selection_page.get_selected_iso()
            drive_path, drive_display = self.selection_page.get_selected_drive()
            iso_type = self.selection_page.get_iso_type()
            iso_details = self.selection_page.get_iso_details()
        except Exception:
            iso_path = self.iso_path
            drive_path = self.drive_path
            drive_display = self.drive_display
            iso_type = "unknown"
            iso_details = {}

        self.iso_path = iso_path or ""
        self.drive_path = drive_path or ""
        self.drive_display = drive_display or ""
        self.partition_scheme = (
            self.selection_page.get_selected_scheme()
            if getattr(self, "selection_page", None)
            else self.partition_scheme
        )

        self.flash_page.set_flash_info(
            self.iso_path,
            self.drive_path,
            self.drive_display,
            iso_type,
            iso_details,
        )

    def start_flash(self):
        self._prepare_flash_page()
        reply = QMessageBox.warning(
            self,
            "Confirm Flash Operation",
            f"Are you absolutely sure you want to flash the image to {self.drive_path}?\n\n"
            f"This will DESTROY ALL DATA on the drive!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.stacked_widget.setCurrentWidget(self.flash_page)
            self.flash_page.start_flash()
            self.update_navigation_buttons()

            iso_type = (
                self.selection_page.get_iso_type()
                if getattr(self, "selection_page", None)
                else "unknown"
            )
            mode = "windows" if iso_type == "windows" else "linux"

            from ..logic.flash_worker import FlashWorker

            self.flash_worker = FlashWorker(
                self.iso_path, self.drive_path, mode, self.partition_scheme
            )
            self.flash_worker.progress.connect(self.flash_page.update_progress)
            self.flash_worker.status_update.connect(self.flash_page.update_status)
            self.flash_worker.log_message.connect(self.log_message_safe)
            self.flash_worker.finished.connect(self.on_flash_finished)
            self.flash_worker.start()

    def cancel_flash(self):
        if self.flash_worker:
            reply = QMessageBox.warning(
                self,
                "Cancel Flash Operation",
                "Are you sure you want to cancel the flash operation?\n\n"
                "Cancelling during the flash process may leave your USB drive in a corrupted "
                "or unusable state. You may need to reformat the drive to use it again.\n\n"
                "Do you want to continue with cancellation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return

            self.log_message_safe(
                "User confirmed cancellation - stopping flash operation..."
            )

            try:
                self.flash_worker.finished.disconnect()
                self.flash_worker.requestInterruption()
                if not self.flash_worker.wait(5000):
                    self.log_message_safe("Force terminating flash thread...")
                    self.flash_worker.terminate()
                    self.flash_worker.wait(2000)
                self.flash_worker = None
            except Exception as e:
                self.log_message_safe(f"Error during cancellation: {e}")
                self.flash_worker = None

        self.flash_page.flashing = False
        self.update_navigation_buttons()
        self.flash_page.set_flash_info(
            self.iso_path, self.drive_path, self.drive_display
        )
        self.flash_page.status_label.setText("Flash operation cancelled.")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.flash_page.status_label.setFont(font)

    def log_message_safe(self, message):
        try:
            if self.logs_window and not self._shutdown_in_progress:
                self.logs_window.append_log(message)
        except Exception:
            pass

    def on_flash_finished(self, success, message):
        if self._shutdown_in_progress:
            return

        try:
            self.flash_page.flash_completed(success, message)

            if self.flash_worker:
                try:
                    self.flash_worker.progress.disconnect()
                    self.flash_worker.status_update.disconnect()
                    self.flash_worker.log_message.disconnect()
                    self.flash_worker.finished.disconnect()
                except Exception:
                    pass

                self.flash_worker.deleteLater()
                self.flash_worker = None

            if success:
                self.current_page = 2
                self.stacked_widget.setCurrentWidget(self.success_page)

                send_notification(
                    title="Flash Complete",
                    message="USB drive has been successfully created!",
                )
                self.cancel_button.setVisible(False)
                self.back_button.setVisible(True)
            else:
                send_notification(
                    title="Flash Failed", message=f"Flash operation failed: {message}"
                )

                QMessageBox.critical(
                    self, "Flash Failed", f"Flash operation failed: {message}"
                )
                self.back_button.setVisible(True)
                self.cancel_button.setVisible(False)

            self.flash_page.flashing = False

        except Exception as e:
            if not self._shutdown_in_progress:
                self.log_message_safe(f"Error in flash finish handler: {e}")

    def reset_to_start(self):
        self.current_page = 0
        self.iso_path = ""
        self.drive_path = ""
        self.drive_display = ""
        self.partition_scheme = "gpt"

        try:
            self.selection_page.reset_selection()
            try:
                self.selection_page.drive_list.clearSelection()
            except Exception:
                pass
        except Exception:
            try:
                if getattr(self, "selection_page", None) is not None:
                    self.selection_page.reset_selection()
                else:
                    iso_pg = getattr(self, "iso_page", None)
                    if iso_pg is not None:
                        try:
                            setattr(iso_pg, "iso_path", None)
                        except Exception:
                            pass
                        try:
                            setattr(iso_pg, "iso_type", "unknown")
                        except Exception:
                            pass
                        try:
                            setattr(iso_pg, "iso_details", {})
                        except Exception:
                            pass
                        lbl = getattr(iso_pg, "file_path_label", None)
                        if lbl is not None:
                            try:
                                lbl.setText("Please select an ISO")
                                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            except Exception:
                                pass
            except Exception:
                pass
        font = QFont()
        font.setPointSize(12)
        try:
            sp = getattr(self, "selection_page", None)
            if sp is not None and getattr(sp, "file_label", None) is not None:
                sp.file_label.setFont(font)
            else:
                iso_pg = getattr(self, "iso_page", None)
                lbl = (
                    getattr(iso_pg, "file_path_label", None)
                    if iso_pg is not None
                    else None
                )
                if lbl is not None:
                    lbl.setFont(font)
        except Exception:
            pass

        try:
            name_lbl = getattr(self.selection_page, "iso_name_label", None)
            if name_lbl is None:
                name_lbl = getattr(self.iso_page, "iso_name_label", None)
            if name_lbl is not None:
                try:
                    name_lbl.setText("")
                    name_lbl.hide()
                except Exception:
                    pass

            meta_lbl = getattr(self.selection_page, "iso_meta_label", None)
            if meta_lbl is None:
                meta_lbl = getattr(self.iso_page, "iso_meta_label", None)
            if meta_lbl is not None:
                try:
                    meta_lbl.setText("")
                    meta_lbl.hide()
                except Exception:
                    pass

            try:
                from .icons import set_label_icon

                thumb = getattr(self.selection_page, "iso_thumb", None)
                if thumb is None:
                    thumb = getattr(self.iso_page, "iso_thumb", None)
                if thumb is not None:
                    try:
                        # Avoid emoji fallback; prefer neutral empty label instead
                        set_label_icon(thumb, "fa5s.file", 48, "#f9e79f", "")
                    except Exception:
                        try:
                            thumb.setText("")
                        except Exception:
                            pass
            except Exception:
                pass

        except Exception:
            pass

        legacy = getattr(self.selection_page, "iso_type_label", None)
        if legacy is None:
            legacy = getattr(self.iso_page, "iso_type_label", None)
        if legacy is not None:
            try:
                legacy.hide()
            except Exception:
                pass

        try:
            sp = getattr(self, "selection_page", None)
            if sp is not None:
                try:
                    dl = getattr(sp, "drive_list", None)
                    if dl is not None:
                        dl.clearSelection()
                except Exception:
                    pass
                try:
                    sp.reset_selection()
                except Exception:
                    pass
            else:
                dp = getattr(self, "drive_page", None)
                if dp is not None:
                    try:
                        dl = getattr(dp, "drive_list", None)
                        if dl is not None:
                            dl.clearSelection()
                    except Exception:
                        pass
                psp = getattr(self, "partition_scheme_page", None)
                if psp is not None:
                    try:
                        psp.reset_selection()
                    except Exception:
                        pass
        except Exception:
            pass

        self.flash_page.set_flash_info("", "", "")
        self.flash_page.progress_bar.setValue(0)

        try:
            self.stacked_widget.setCurrentWidget(self.selection_page)
        except Exception:
            try:
                iso_pg = getattr(self, "iso_page", None)
                if iso_pg is not None:
                    self.stacked_widget.setCurrentWidget(iso_pg)
            except Exception:
                pass
        self.update_navigation_buttons()

    def show_logs(self):
        # Ensure LogsWindow exists (it may have been closed and set to None)
        if self.logs_window is None:
            self.logs_window = LogsWindow()
        self.logs_window.show()
        self.logs_window.raise_()
        self.logs_window.activateWindow()

    def show_about(self):
        self.about_widget.exec()


__all__ = ["JustDDApp"]
