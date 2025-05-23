import sys
import os
import subprocess


def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QFormLayout,
    QTabWidget,
    QCheckBox,
    QFrame,
)
from PySide6.QtCore import Qt, QProcess, QThread, Signal
from PySide6.QtGui import QIcon, QTextCursor, QPixmap
from widgets.sync_widget import SyncWidget, SyncWorker
from PySide6.QtGui import QIcon
import tempfile
from widgets.iso_downloader_widget import IsoDownloaderWidget


# --- SyncWorker Class (Keep as is for now) ---
class SyncWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool)

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device

    def run(self):
        import tempfile
        import os

        # Check for busy processes on the device
        try:
            res = subprocess.run(
                ["fuser", "-m", self.device], capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                pids = res.stdout.strip()
                self.progress.emit(
                    f"Error: Device {self.device} is busy or mounted by PID(s): {pids}"
                )
                self.progress.emit(
                    "Please unmount the drive or stop processes using it before syncing."
                )
                self.finished.emit(False)
                return
            elif res.returncode != 0 and res.stderr:
                self.progress.emit(
                    f"Warning: 'fuser' check failed: {res.stderr.strip()}"
                )
                self.progress.emit("Proceeding with sync despite fuser warning...")
            else:
                self.progress.emit(
                    f"Device {self.device} appears free, proceeding to sync..."
                )
        except subprocess.TimeoutExpired:
            self.progress.emit(
                f"Error: 'fuser' command timed out checking {self.device}. Cannot safely sync."
            )
            self.finished.emit(False)
            return
        except FileNotFoundError:
            self.progress.emit(
                "Warning: 'fuser' command not found. Cannot check if device is busy. Proceeding with sync..."
            )
        except Exception as e:
            self.progress.emit(f"Error checking device busy status: {e}")
            self.progress.emit(
                "Proceeding with sync despite error checking busy status..."
            )

        # Perform sync using a shell script for all commands
        # Add pkexec root check at the top of the script
        script_lines = [
            'if [ "$(id -u)" -ne 0 ]; then exec pkexec bash "$0" "$@"; fi',
            "set -e",
        ]
        script_lines.append(f'echo "Syncing filesystem buffers..."')
        script_lines.append("sync")
        script_content = "\n".join(script_lines)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as tf:
            tf.write(script_content)
            script_path = tf.name
        try:
            os.chmod(script_path, 0o700)
            proc = subprocess.Popen(
                ["bash", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                self.progress.emit(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self.progress.emit("Sync command finished.")
                self.finished.emit(True)
            else:
                self.progress.emit(f"Sync script exited with code {proc.returncode}")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Sync failed with unexpected error: {e}")
            self.finished.emit(False)
        finally:
            os.unlink(script_path)


# --- SyncWidget Class ---
class SyncWidget(QWidget):
    # Signals to communicate with the main app
    syncProgress = Signal(str)
    syncFinished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_drive = ""
        self._sync_worker = None

        # Set window properties
        self.setWindowTitle("Drive Sync Tool")
        flags = Qt.WindowType.Tool | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Description Label (Optional but helpful)
        description_label = QLabel(
            "Use this tool to manually sync write buffers to the selected Linux drive."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Drive Info Label
        self.drive_label = QLabel("Target Drive: <None Selected>")
        layout.addWidget(self.drive_label)

        # Sync Button
        self.sync_button = QPushButton("Sync Drive Buffers")
        self.sync_button.setToolTip("Flush OS write buffers to the selected drive.")
        self.sync_button.clicked.connect(self._start_sync)
        self.sync_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.sync_button)

        layout.addStretch()

        self.setLayout(layout)

    def setTargetDrive(self, drive_path):
        self._target_drive = drive_path
        if self._target_drive:
            self.drive_label.setText(f"Target Drive: {self._target_drive}")
        else:
            self.drive_label.setText("Target Drive: <None Selected>")

        # Enable button only if a drive is set and no sync is running
        is_running = self._sync_worker is not None and self._sync_worker.isRunning()
        self.sync_button.setEnabled(bool(self._target_drive) and not is_running)

    def _start_sync(self):
        if not self._target_drive:
            self.syncProgress.emit("Sync Error: No drive selected.")
            QMessageBox.warning(self, "Sync Error", "No drive selected.")
            return

        if self._sync_worker and self._sync_worker.isRunning():
            self.syncProgress.emit("Sync Info: Sync already in progress.")
            return

        self.sync_button.setEnabled(False)
        self.syncProgress.emit(f"Starting sync via Sync Tool for: {self._target_drive}")
        self.syncProgress.emit(f"Checking device busy status: {self._target_drive}")

        self._sync_worker = SyncWorker(self._target_drive)
        self._sync_worker.progress.connect(self.syncProgress)  # Relay progress
        self._sync_worker.finished.connect(self._on_sync_finished)
        # Clean up worker thread when finished
        self._sync_worker.finished.connect(self._sync_worker.deleteLater)
        self._sync_worker.start()

    def _on_sync_finished(self, success):
        final_message = ""
        if success:
            final_message = (
                f"--- Sync completed successfully for {self._target_drive} ---"
            )
            self.syncProgress.emit(final_message)
        else:
            final_message = f"--- Sync encountered errors for {self._target_drive} ---"
            self.syncProgress.emit(final_message)

        self.syncFinished.emit(success, final_message)

        # Re-enable button if a drive is still selected
        self.sync_button.setEnabled(bool(self._target_drive))
        self._sync_worker = None  # Clear worker reference

    def closeEvent(self, event):
        # We just hide it instead of closing, so it can be reopened easily
        self.hide()
        event.ignore()  # Ignore the close event, effectively hiding the window


class WindowsWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool)

    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps

    def run(self):
        script_lines = [
            "set -e",
            # Unmount and clean up any previous mounts or folders
            "for mnt in /mnt/justdd_iso /mnt/justdd_vfat /mnt/justdd_ntfs; do",
            '  if mountpoint -q "$mnt"; then',
            '    umount "$mnt" || true',
            "  fi",
            '  rm -rf "$mnt"',
            "done",
            # Check if ISO is already mounted at /mnt/justdd_iso
            'if mount | grep -q "/mnt/justdd_iso"; then',
            "  umount /mnt/justdd_iso || true",
            "fi",
        ]
        for idx, (desc, cmd) in enumerate(self.steps, 1):
            script_lines.append(f'echo "Step {idx}/{len(self.steps)}: {desc}"')
            script_lines.append(f'echo "Running: {" ".join(cmd)}"')
            script_lines.append(
                " ".join(f'"{c}"' if " " in c or c.startswith("-") else c for c in cmd)
            )
        script_content = "\n".join(script_lines)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as tf:
            tf.write(script_content)
            script_path = tf.name
        try:
            os.chmod(script_path, 0o700)
            proc = subprocess.Popen(
                ["pkexec", "bash", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                self.progress.emit(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self.finished.emit(True)
            else:
                self.progress.emit(f"Script exited with code {proc.returncode}")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Exception: {e}")
            self.finished.emit(False)
        finally:
            os.unlink(script_path)


class DDApp(QWidget):
    def __init__(self):
        super().__init__()
        # Enable floating behavior in tiling window managers by making this a dialog that stays on top
        flags = self.windowFlags()
        flags |= (
            Qt.WindowType.Dialog
            | Qt.WindowStaysOnTopHint
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setWindowFlags(flags)
        # Initialize attributes before any method calls
        self.iso_path = ""
        self.target_drive = ""
        self.drive_info = {}
        self.iso_path_win = ""
        self.target_drive_win = ""
        self.drive_info_win = {}
        self.setWindowTitle("JustDD - USB Image Writer (1.2)")

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # --- Linux ISO Tab ---
        linux_tab = QWidget()
        linux_layout = QVBoxLayout(linux_tab)
        # ISO selection
        linux_iso_form = QFormLayout()
        self.iso_edit = QLineEdit()
        self.iso_edit.setReadOnly(True)
        self.iso_edit.setPlaceholderText("Select an ISO file...")
        self.iso_browse_button = QPushButton("Browse...")
        self.iso_browse_button.setToolTip("Click to select the ISO image file.")
        self.iso_browse_button.clicked.connect(self.browse_iso)
        iso_browse_layout = QHBoxLayout()
        iso_browse_layout.addWidget(self.iso_edit)
        iso_browse_layout.addWidget(self.iso_browse_button)
        linux_iso_form.addRow("ISO File:", iso_browse_layout)
        linux_layout.addLayout(linux_iso_form)
        # Drive selection
        linux_drive_form = QFormLayout()
        self.drive_combo = QComboBox()
        self.drive_combo.setToolTip("Select the target USB drive.")
        self.refresh_drives_button = QPushButton("Refresh")
        self.refresh_drives_button.setToolTip("Rescan for available drives.")
        self.refresh_drives_button.clicked.connect(self.refresh_drives)
        self.open_sync_button = QPushButton("Sync Tool")
        self.open_sync_button.setToolTip(
            "Open a separate tool to manually sync drive buffers."
        )
        self.open_sync_button.clicked.connect(self.open_sync_widget)
        self.open_sync_button.setEnabled(False)  # Disabled until a drive is selected
        drive_select_layout = QHBoxLayout()
        drive_select_layout.addWidget(self.drive_combo, 1)
        drive_select_layout.addWidget(self.refresh_drives_button)
        drive_select_layout.addWidget(self.open_sync_button)
        linux_drive_form.addRow("Target Drive:", drive_select_layout)
        linux_layout.addLayout(linux_drive_form)
        # Write button
        self.write_button = QPushButton("Write to Drive")
        self.write_button.setToolTip(
            "Start writing the selected ISO to the selected drive (requires confirmation)."
        )
        self.write_button.clicked.connect(self.confirm_write)
        self.write_button.setEnabled(False)
        linux_layout.addWidget(self.write_button)
        # Status Area
        self.status_label = QLabel("Status / Output:")
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        linux_layout.addWidget(self.status_label)
        linux_layout.addWidget(self.status_output, 1)

        tabs.addTab(linux_tab, "Linux ISO")

        # --- Windows ISO Tab ---
        windows_tab = QWidget()
        windows_layout = QVBoxLayout(windows_tab)
        # ISO selection for Windows
        win_iso_form = QFormLayout()
        self.iso_edit_win = QLineEdit()
        self.iso_edit_win.setReadOnly(True)
        self.iso_edit_win.setPlaceholderText("Select a Windows ISO...")
        self.iso_browse_button_win = QPushButton("Browse...")
        self.iso_browse_button_win.setToolTip("Select Windows ISO file.")
        self.iso_browse_button_win.clicked.connect(self.browse_iso_win)
        win_iso_layout = QHBoxLayout()
        win_iso_layout.addWidget(self.iso_edit_win)
        win_iso_layout.addWidget(self.iso_browse_button_win)
        win_iso_form.addRow("Windows ISO:", win_iso_layout)
        windows_layout.addLayout(win_iso_form)
        # Drive selection for Windows
        win_drive_form = QFormLayout()
        self.drive_combo_win = QComboBox()
        self.drive_combo_win.setToolTip(
            "Select target USB drive for Windows installation."
        )
        self.refresh_drives_button_win = QPushButton("Refresh")
        self.refresh_drives_button_win.setToolTip("Rescan for drives.")
        self.refresh_drives_button_win.clicked.connect(self.refresh_drives_win)
        win_drive_layout = QHBoxLayout()
        win_drive_layout.addWidget(self.drive_combo_win, 1)
        win_drive_layout.addWidget(self.refresh_drives_button_win)
        win_drive_form.addRow("Target Drive:", win_drive_layout)
        windows_layout.addLayout(win_drive_form)
        # Write button and status for Windows
        self.write_button_win = QPushButton("Prepare USB")
        self.write_button_win.setToolTip(
            "Format and copy Windows files to make bootable USB."
        )
        self.write_button_win.clicked.connect(self.confirm_write_windows)
        self.write_button_win.setEnabled(False)
        windows_layout.addWidget(self.write_button_win)
        self.status_label_win = QLabel("Status / Output:")
        self.status_output_win = QTextEdit()
        self.status_output_win.setReadOnly(True)
        self.status_output_win.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        windows_layout.addWidget(self.status_label_win)
        windows_layout.addWidget(self.status_output_win, 1)
        tabs.addTab(windows_tab, "Windows ISO")

        # --- About Tab ---
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        icon_label = QLabel()
        icon_path = resource_path("images/icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                print(f"Failed to load pixmap from: {icon_path}")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            about_layout.addWidget(icon_label)
        else:
            print(f"Icon not found at: {icon_path}")

        about_label = QLabel(
            "<b>JustDD - USB Image Writer</b><br>"
            "Version 1.2<br><br>"
            "A simple, open-source tool to write Linux and Windows ISO images to USB drives.\n"
            "Supports manual sync, drive selection, and Windows USB preparation.<br><br>"
            "Author: xxanqw<br>"
            "License: GPLv3<br>"
            "<br>For more information, visit the GitHub page."
        )
        about_label.setWordWrap(True)
        about_label.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(about_label)
        github_button = QPushButton("Visit GitHub")
        github_button.clicked.connect(
            lambda: os.system('xdg-open "https://github.com/xxanqw/justdd"')
        )
        about_layout.addWidget(github_button)
        about_layout.addStretch()
        tabs.addTab(about_tab, "About")

        # --- Create Sync Widget instance (AFTER status_output is defined) ---
        self.sync_widget = SyncWidget()
        # Connect its progress signal to the main status output (now safe)
        self.sync_widget.syncProgress.connect(self.status_output.append)

        # --- Create ISO Downloader Widget (floating, like SyncWidget) ---
        self.iso_downloader_widget = IsoDownloaderWidget()

        # --- Add button at the bottom to open ISO Downloader ---
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addStretch()
        self.open_iso_downloader_button = QPushButton("ISO Downloader")
        self.open_iso_downloader_button.setToolTip("Open a tool to download Linux ISOs.")
        self.open_iso_downloader_button.clicked.connect(self.open_iso_downloader_widget)
        bottom_button_layout.addWidget(self.open_iso_downloader_button)
        main_layout.addLayout(bottom_button_layout)

        # Initial drive scans and connections
        self.refresh_drives()  # linux drives
        self.drive_combo.currentIndexChanged.connect(
            self.update_write_button_state
        )  # Connect drive change
        self.refresh_drives_win()  # windows drives
        self.drive_combo_win.currentIndexChanged.connect(
            self.update_write_button_state_win
        )

    def browse_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ISO File", "", "ISO Files (*.iso);;All Files (*)"
        )
        if file_path:
            self.iso_path = file_path
            self.iso_edit.setText(file_path)
            self.update_write_button_state()
            self.status_output.append(f"Selected ISO: {self.iso_path}")

    def browse_iso_win(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Windows ISO File", "", "ISO Files (*.iso);;All Files (*)"
        )
        if file_path:
            self.iso_path_win = file_path
            self.iso_edit_win.setText(file_path)
            self.update_write_button_state_win()
            self.status_output_win.append(f"Selected Windows ISO: {self.iso_path_win}")

    def refresh_drives(self):
        current_selection = self.drive_combo.currentText()
        self.status_output.append("Refreshing drive list...")
        self.drive_combo.clear()
        # --- Drive Listing Logic (Linux tab) ---
        try:
            # Using lsblk to find removable block devices (like USB drives)
            # -d: list devices without partitions
            # -n: no header
            # -o NAME,RM,TYPE,SIZE,MOUNTPOINT: output relevant info
            # We filter for RM=1 (removable) and TYPE=disk
            result = subprocess.run(
                ["lsblk", "-dno", "NAME,RM,TYPE,SIZE,MOUNTPOINT"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            drives = []
            drive_info = {}
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                name = parts[0]
                rm = parts[1]
                type = parts[2]
                size = parts[3]
                mountpoint = parts[4] if len(parts) > 4 else "[Not mounted]"

                if rm == "1" and type == "disk":
                    device_path = f"/dev/{name}"
                    display_text = f"{device_path} ({size}) - {mountpoint}"
                    drives.append(display_text)
                    drive_info[display_text] = device_path  # Store mapping

            if drives:
                self.drive_combo.addItems(drives)
                self.drive_info = drive_info  # Store the info map
                # Try to restore previous selection if still present
                if current_selection in drive_info:
                    self.drive_combo.setCurrentText(current_selection)
                self.status_output.append(
                    f"Found drives: {', '.join(drive_info.values())}"
                )
            else:
                self.status_output.append("No suitable removable drives found.")
                self.drive_info = {}
        except FileNotFoundError:
            self.status_output.append(
                "Error: 'lsblk' command not found. Cannot list drives."
            )
            self.drive_info = {}
        except subprocess.TimeoutExpired:
            self.status_output.append("Error: 'lsblk' command timed out.")
            self.drive_info = {}
        except subprocess.CalledProcessError as e:
            self.status_output.append(f"Error listing drives: {e}\n{e.stderr}")
            self.drive_info = {}
        except Exception as e:
            self.status_output.append(
                f"An unexpected error occurred while listing drives: {e}"
            )
            self.drive_info = {}

        self.update_write_button_state()
        # --- End Drive Listing Logic (Linux) ---

    def refresh_drives_win(self):
        current_selection = self.drive_combo_win.currentText()
        self.status_output_win.append("Refreshing drive list...")
        self.drive_combo_win.clear()
        # --- Drive Listing Logic (Windows tab (same but why not)) ---
        try:
            result = subprocess.run(
                ["lsblk", "-dno", "NAME,RM,TYPE,SIZE,MOUNTPOINT"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            drives = []
            drive_info = {}
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                name = parts[0]
                rm = parts[1]
                type = parts[2]
                size = parts[3]
                mountpoint = parts[4] if len(parts) > 4 else "[Not mounted]"

                if rm == "1" and type == "disk":
                    device_path = f"/dev/{name}"
                    display_text = f"{device_path} ({size}) - {mountpoint}"
                    drives.append(display_text)
                    drive_info[display_text] = device_path

            if drives:
                self.drive_combo_win.addItems(drives)
                self.drive_info_win = drive_info
                if current_selection in drive_info:
                    self.drive_combo_win.setCurrentText(current_selection)
                self.status_output_win.append(
                    f"Found drives: {', '.join(drive_info.values())}"
                )
            else:
                self.status_output_win.append("No suitable removable drives found.")
                self.drive_info_win = {}
        except FileNotFoundError:
            self.status_output_win.append(
                "Error: 'lsblk' command not found. Cannot list drives."
            )
            self.drive_info_win = {}
        except subprocess.TimeoutExpired:
            self.status_output_win.append("Error: 'lsblk' command timed out.")
            self.drive_info_win = {}
        except subprocess.CalledProcessError as e:
            self.status_output_win.append(f"Error listing drives: {e}\n{e.stderr}")
            self.drive_info_win = {}
        except Exception as e:
            self.status_output_win.append(
                f"An unexpected error occurred while listing drives: {e}"
            )
            self.drive_info_win = {}

        self.update_write_button_state_win()
        # --- End Drive Listing Logic (Windows) ---

    def update_write_button_state(self):
        selected_drive_display = self.drive_combo.currentText()
        # Get the actual device path from the display text
        self.target_drive = self.drive_info.get(selected_drive_display, "")

        # Enable/disable Write button
        can_write = bool(self.iso_path and self.target_drive)
        self.write_button.setEnabled(can_write)

        # Enable/disable Sync Tool button
        can_sync = bool(self.target_drive)
        self.open_sync_button.setEnabled(can_sync)

        # Update the SyncWidget with the selected drive (even if hidden)
        self.sync_widget.setTargetDrive(self.target_drive)

    def update_write_button_state_win(self):
        selected_drive_display = self.drive_combo_win.currentText()
        # Get the actual device path from the display text
        self.target_drive_win = self.drive_info_win.get(selected_drive_display, "")

        if self.iso_path_win and self.target_drive_win:
            self.write_button_win.setEnabled(True)
        else:
            self.write_button_win.setEnabled(False)

    def confirm_write(self):
        # Ensure target_drive is updated based on current selection
        selected_drive_display = self.drive_combo.currentText()
        self.target_drive = self.drive_info.get(selected_drive_display, "")

        if not self.iso_path or not self.target_drive:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please select both an ISO file and a target drive.",
            )
            return

        # Double-check the drive path looks reasonable (basic check)
        if not self.target_drive.startswith("/dev/"):
            QMessageBox.critical(
                self, "Error", f"Invalid target drive path derived: {self.target_drive}"
            )
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Write Operation",
            f"<font color='red'><b>WARNING:</b></font> This will <b>DESTROY ALL DATA</b> on <font color='blue'>{self.target_drive}</font> ({selected_drive_display.split('(')[-1].split(')')[0]}).<br><br>"
            f"Are you absolutely sure you want to write<br>'{os.path.basename(self.iso_path)}'<br>"
            f"to<br>'{self.target_drive}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.write_image()

    def confirm_write_windows(self):
        # Ensure target_drive_win is updated based on current selection
        selected_drive_display = self.drive_combo_win.currentText()
        self.target_drive_win = self.drive_info_win.get(selected_drive_display, "")

        if not self.iso_path_win or not self.target_drive_win:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please select both a Windows ISO file and a target drive.",
            )
            return

        # Double-check the drive path looks reasonable (basic check)
        if not self.target_drive_win.startswith("/dev/"):
            QMessageBox.critical(
                self,
                "Error",
                f"Invalid target drive path derived: {self.target_drive_win}",
            )
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Write Operation",
            f"<font color='red'><b>WARNING:</b></font> This will <b>DESTROY ALL DATA</b> on <font color='blue'>{self.target_drive_win}</font> ({selected_drive_display.split('(')[-1].split(')')[0]}).<br><br>"
            f"Are you absolutely sure you want to write<br>'{os.path.basename(self.iso_path_win)}'<br>"
            f"to<br>'{self.target_drive_win}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.write_image_windows()

    def write_image(self):
        self.status_output.clear()
        self.status_output.append(f"Starting write process...")
        self.status_output.append(f"ISO: {self.iso_path}")
        self.status_output.append(f"Drive: {self.target_drive}")
        self.status_output.append("--- DD Command Output ---")

        self.write_button.setEnabled(False)
        self.refresh_drives_button.setEnabled(False)
        self.iso_browse_button.setEnabled(False)
        self.drive_combo.setEnabled(False)
        self.open_sync_button.setEnabled(False)
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.tabBar().setEnabled(False)

        # --- DD Execution Logic ---
        # Using pkexec.
        # Using QProcess for better integration (non-blocking).

        # Create QProcess instance and connect signals
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        # Use pkexec to run dd as root
        command = "pkexec"
        args = [
            "dd",
            f"if={self.iso_path}",
            f"of={self.target_drive}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
        ]
        self.status_output.append(f"Executing: pkexec {' '.join(args)}")
        self.process.start(command, args)

    # Windows-specific function to handle the write process
    def write_image_windows(self):
        self.status_output_win.clear()
        self._set_windows_ui_enabled(False)
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.tabBar().setEnabled(False)
        self.findChild(QTabWidget).setEnabled(False)
        # Disable all tabs while writing
        drive = self.target_drive_win
        p1, p2 = f"{drive}1", f"{drive}2"
        iso_mount, vfat_mount, ntfs_mount = (
            "/mnt/justdd_iso",
            "/mnt/justdd_vfat",
            "/mnt/justdd_ntfs",
        )
        steps = [
            ("Wipefs", ["wipefs", "-a", drive]),
            ("Parted mklabel", ["parted", "--script", drive, "mklabel", "gpt"]),
            (
                "Parted mkpart BOOT",
                ["parted", "--script", drive, "mkpart", "BOOT", "fat32", "0%", "1GiB"],
            ),
            (
                "Parted mkpart INSTALL",
                [
                    "parted",
                    "--script",
                    drive,
                    "mkpart",
                    "INSTALL",
                    "ntfs",
                    "1GiB",
                    "100%",
                ],
            ),
            ("mkfs.vfat", ["mkfs.vfat", "-n", "BOOT", p1]),
            ("mkfs.ntfs", ["mkfs.ntfs", "--quick", "-L", "INSTALL", p2]),
            ("mkdir ISO mount", ["mkdir", "-p", iso_mount]),
            ("mount ISO", ["mount", "-o", "loop", self.iso_path_win, iso_mount]),
            ("mkdir VFAT", ["mkdir", "-p", vfat_mount]),
            ("mount BOOT", ["mount", p1, vfat_mount]),
            (
                "rsync to BOOT",
                [
                    "rsync",
                    "-r",
                    "--info=progress2",
                    "--no-perms",
                    "--no-owner",
                    "--no-group",
                    "--exclude",
                    "sources",
                    f"{iso_mount}/",
                    f"{vfat_mount}/",
                ],
            ),
            ("mkdir sources", ["mkdir", "-p", f"{vfat_mount}/sources"]),
            (
                "copy boot.wim",
                ["cp", f"{iso_mount}/sources/boot.wim", f"{vfat_mount}/sources/"],
            ),
            ("mkdir NTFS", ["mkdir", "-p", ntfs_mount]),
            ("mount INSTALL", ["mount", p2, ntfs_mount]),
            (
                "rsync to INSTALL (this is a VERY LONG process, output can be broken)",
                [
                    "rsync",
                    "-r",
                    "--info=progress2",
                    "--no-perms",
                    "--no-owner",
                    "--no-group",
                    f"{iso_mount}/",
                    f"{ntfs_mount}/",
                ],
            ),
            (
                "umount INSTALL (this step is even longer than previous, just give it time)",
                ["umount", ntfs_mount],
            ),
            ("umount BOOT", ["umount", vfat_mount]),
            ("umount ISO", ["umount", iso_mount]),
            ("sync buffers", ["sync"]),
            (
                "remove dirs (if it fails, do it yourself)",
                ["rmdir", iso_mount, vfat_mount, ntfs_mount],
            ),
        ]
        self.windows_worker = WindowsWorker(steps)
        self.windows_worker.progress.connect(self.status_output_win.append)
        self.windows_worker.finished.connect(self._on_windows_done)
        self.windows_worker.start()

    def _on_windows_done(self, success):
        if success:
            self.status_output_win.append("--- Windows USB preparation complete ---")
            QMessageBox.information(
                self, "Success", "Windows USB drive prepared successfully."
            )
        else:
            self.status_output_win.append("--- Windows USB preparation failed ---")
        # Re-enable UI
        self._set_windows_ui_enabled(True)
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.tabBar().setEnabled(True)
        self.findChild(QTabWidget).setEnabled(True)

    def _set_windows_ui_enabled(self, enabled: bool):
        """Enable or disable Windows ISO tab controls."""
        self.write_button_win.setEnabled(enabled)
        self.refresh_drives_button_win.setEnabled(enabled)
        self.iso_browse_button_win.setEnabled(enabled)
        self.drive_combo_win.setEnabled(enabled)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.handle_stdout_data(data)

    def handle_stdout_data(self, data):
        # Append stdout data, ensuring it ends with a newline for clarity
        text = data.strip()
        if text:
            self.status_output.append(text)
            self.status_output.verticalScrollBar().setValue(
                self.status_output.verticalScrollBar().maximum()
            )  # Scroll to bottom

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.handle_stderr_data(data)

    def handle_stderr_data(self, data):
        # dd often prints progress to stderr, handle it specially
        # Try to update the last line if it looks like progress
        lines = data.strip().split("\r")  # dd progress uses carriage return
        last_line = lines[-1]
        current_text = self.status_output.toPlainText()
        lines_in_widget = current_text.split("\n")

        # Check if the last line in the widget might be previous progress output
        if lines_in_widget and (
            "copied" in lines_in_widget[-1] or "records in" in lines_in_widget[-1]
        ):
            # Overwrite the last line with new progress
            cursor = self.status_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            # Check if the block is the last line before removing
            cursor.movePosition(
                QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor
            )
            if cursor.blockNumber() == self.status_output.document().blockCount() - 1:
                cursor.removeSelectedText()
                cursor.insertBlock()  # Ensure we are on a new line if needed
            self.status_output.append(last_line)
        elif last_line:  # Otherwise, just append
            self.status_output.append(last_line)

        self.status_output.verticalScrollBar().setValue(
            self.status_output.verticalScrollBar().maximum()
        )  # Scroll to bottom

    def handle_stdout_win(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.handle_stdout_data_win(data)

    def handle_stdout_data_win(self, data):
        # Append stdout data, ensuring it ends with a newline for clarity
        text = data.strip()
        if text:
            self.status_output_win.append(text)
            self.status_output_win.verticalScrollBar().setValue(
                self.status_output_win.verticalScrollBar().maximum()
            )  # Scroll to bottom

    def handle_stderr_win(self):
        data = self.process.readAllStandardError().data().decode()
        self.handle_stderr_data_win(data)

    def handle_stderr_data_win(self, data):
        lines = data.strip().split("\r")
        last_line = lines[-1]
        current_text = self.status_output_win.toPlainText()
        lines_in_widget = current_text.split("\n")

        if lines_in_widget and (
            "copied" in lines_in_widget[-1] or "records in" in lines_in_widget[-1]
        ):
            cursor = self.status_output_win.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.movePosition(
                QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor
            )
            if (
                cursor.blockNumber()
                == self.status_output_win.document().blockCount() - 1
            ):
                cursor.removeSelectedText()
                cursor.insertBlock()
            self.status_output_win.append(last_line)
        elif last_line:
            self.status_output_win.append(last_line)

        self.status_output_win.verticalScrollBar().setValue(
            self.status_output_win.verticalScrollBar().maximum()
        )

    def process_finished(self, exit_code=None, exit_status=None):
        # If called by QProcess signal, get exit code from the process
        if exit_code is None and self.process:
            exit_code = self.process.exitCode()
            exit_status = self.process.exitStatus()

        # --- Placeholder message ---
        if "Simulating" in self.status_output.toPlainText() and exit_code == 0:
            self.status_output.append("--- Simulation Complete ---")
            QMessageBox.information(self, "Simulation", "Simulated write completed.")
        # --- End Placeholder ---
        elif exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            self.status_output.append("--- Write Completed Successfully ---")
            QMessageBox.information(self, "Success", "ISO image written successfully.")
        elif exit_status == QProcess.ExitStatus.CrashExit:
            self.status_output.append(f"--- Write Failed (Process Crashed) ---")
            QMessageBox.critical(
                self, "Error", f"Write process crashed. Check status output."
            )
        else:
            self.status_output.append(f"--- Write Failed (Exit Code: {exit_code}) ---")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to write ISO image. Check status output for details. Exit code: {exit_code}",
            )

        if self.process:  # Check if process exists before clearing
            self.process.finished.disconnect()  # Disconnect signals to prevent issues if called multiple times
            self.process.readyReadStandardOutput.disconnect()
            self.process.readyReadStandardError.disconnect()
            self.process = None  # Clear the process object

        # Re-enable UI elements
        self.write_button.setEnabled(True)
        self.refresh_drives_button.setEnabled(True)
        self.iso_browse_button.setEnabled(True)
        self.drive_combo.setEnabled(True)
        self.open_sync_button.setEnabled(True)
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.tabBar().setEnabled(True)
        self.update_write_button_state()

    def process_finished_win(self, exit_code=None, exit_status=None):
        # If called by QProcess signal, get exit code from the process
        if exit_code is None and self.process:
            exit_code = self.process.exitCode()
            exit_status = self.process.exitStatus()  # QProcess.ExitStatus

        # --- Placeholder message ---
        if "Simulating" in self.status_output_win.toPlainText() and exit_code == 0:
            self.status_output_win.append("--- Simulation Complete ---")
            QMessageBox.information(self, "Simulation", "Simulated write completed.")
        # --- End Placeholder ---
        elif exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            self.status_output_win.append("--- Write Completed Successfully ---")
            QMessageBox.information(self, "Success", "ISO image written successfully.")
        elif exit_status == QProcess.ExitStatus.CrashExit:
            self.status_output_win.append(f"--- Write Failed (Process Crashed) ---")
            QMessageBox.critical(
                self, "Error", f"Write process crashed. Check status output."
            )
        else:
            self.status_output_win.append(
                f"--- Write Failed (Exit Code: {exit_code}) ---"
            )
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to write ISO image. Check status output for details. Exit code: {exit_code}",
            )

        if self.process:  # Check if process exists before clearing
            self.process.finished.disconnect()  # Disconnect signals to prevent issues if called multiple times
            self.process.readyReadStandardOutput.disconnect()
            self.process.readyReadStandardError.disconnect()
            self.process = None  # Clear the process object

        # Re-enable Windows UI elements
        self.write_button_win.setEnabled(True)
        self.refresh_drives_button_win.setEnabled(True)
        self.iso_browse_button_win.setEnabled(True)
        self.drive_combo.setEnabled(True)
        self.update_write_button_state_win()  # Re-evaluate button state

    # --- Method to open the Sync Widget ---
    def open_sync_widget(self):
        # Ensure the target drive is up-to-date before showing
        self.sync_widget.setTargetDrive(self.target_drive)
        self.sync_widget.show()
        self.sync_widget.raise_()
        self.sync_widget.activateWindow()

    # --- Method to open the ISO Downloader Widget ---
    def open_iso_downloader_widget(self):
        self.iso_downloader_widget.show()
        self.iso_downloader_widget.raise_()
        self.iso_downloader_widget.activateWindow()


if __name__ == "__main__":
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland.textinput=false"
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Set window icon for both X11 and Wayland
    icon_path = resource_path("images/icon.png")
    app.setWindowIcon(QIcon(icon_path))
    os.environ["XDG_CURRENT_DESKTOP"] = os.environ.get(
        "XDG_CURRENT_DESKTOP", ""
    )  # Ensure env is set for Wayland
    window = DDApp()
    window.resize(650, 450)
    window.show()
    sys.exit(app.exec())
