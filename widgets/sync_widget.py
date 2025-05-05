from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
import subprocess

class SyncWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool)
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
    def run(self):
        try:
            res = subprocess.run(["fuser", "-m", self.device], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                pids = res.stdout.strip()
                self.progress.emit(f"Error: Device {self.device} is busy or mounted by PID(s): {pids}")
                self.progress.emit("Please unmount the drive or stop processes using it before syncing.")
                self.finished.emit(False)
                return
            elif res.returncode != 0 and res.stderr:
                self.progress.emit(f"Warning: 'fuser' check failed: {res.stderr.strip()}")
                self.progress.emit("Proceeding with sync despite fuser warning...")
            else:
                self.progress.emit(f"Device {self.device} appears free, proceeding to sync...")
        except subprocess.TimeoutExpired:
            self.progress.emit(f"Error: 'fuser' command timed out checking {self.device}. Cannot safely sync.")
            self.finished.emit(False)
            return
        except FileNotFoundError:
            self.progress.emit("Warning: 'fuser' command not found. Cannot check if device is busy. Proceeding with sync...")
        except Exception as e:
            self.progress.emit(f"Error checking device busy status: {e}")
            self.progress.emit("Proceeding with sync despite error checking busy status...")
        self.progress.emit("Syncing filesystem buffers...")
        try:
            subprocess.run(["sync"], check=True, timeout=60)
            self.progress.emit("Sync command finished.")
            self.finished.emit(True)
        except subprocess.TimeoutExpired:
            self.progress.emit(f"Error: 'sync' command timed out. The drive might be slow or unresponsive.")
            self.finished.emit(False)
        except subprocess.CalledProcessError as e:
            self.progress.emit(f"Sync command failed with error: {e}")
            self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Sync failed with unexpected error: {e}")
            self.finished.emit(False)

class SyncWidget(QWidget):
    syncProgress = Signal(str)
    syncFinished = Signal(bool, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_drive = ""
        self._sync_worker = None
        self.setWindowTitle("Drive Sync Tool")
        flags = Qt.WindowType.Tool | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        description_label = QLabel("Use this tool to manually sync write buffers to the selected Linux drive.")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        self.drive_label = QLabel("Target Drive: <None Selected>")
        layout.addWidget(self.drive_label)
        self.sync_button = QPushButton("Sync Drive Buffers")
        self.sync_button.setToolTip("Flush OS write buffers to the selected drive.")
        self.sync_button.clicked.connect(self._start_sync)
        self.sync_button.setEnabled(False)
        layout.addWidget(self.sync_button)
        layout.addStretch()
        self.setLayout(layout)
    def setTargetDrive(self, drive_path):
        self._target_drive = drive_path
        if self._target_drive:
            self.drive_label.setText(f"Target Drive: {self._target_drive}")
        else:
            self.drive_label.setText("Target Drive: <None Selected>")
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
        self._sync_worker.progress.connect(self.syncProgress)
        self._sync_worker.finished.connect(self._on_sync_finished)
        self._sync_worker.finished.connect(self._sync_worker.deleteLater)
        self._sync_worker.start()
    def _on_sync_finished(self, success):
        final_message = ""
        if success:
            final_message = f"--- Sync completed successfully for {self._target_drive} ---"
            self.syncProgress.emit(final_message)
        else:
            final_message = f"--- Sync encountered errors for {self._target_drive} ---"
            self.syncProgress.emit(final_message)
        self.syncFinished.emit(success, final_message)
        self.sync_button.setEnabled(bool(self._target_drive))
        self._sync_worker = None
    def closeEvent(self, event):
        self.hide()
        event.ignore()