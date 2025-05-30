from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QComboBox, 
)
from PySide6.QtCore import Qt, QStandardPaths, QModelIndex, QThread, Signal, QObject
from PySide6.QtGui import QStandardItemModel, QStandardItem
import os
import time
from urllib.parse import urljoin

from .download_worker import IsoDownloadWorker
from .distro_config import DISTRO_CONFIG
from .utils import format_time_display, clean_filename

from .fetchers.ubuntu_fetcher import fetch_ubuntu_versions, fetch_ubuntu_isos
from .fetchers.fedora_fetcher import fetch_fedora_versions, fetch_fedora_isos
from .fetchers.debian_fetcher import fetch_debian_versions, fetch_debian_isos
from .fetchers.mint_fetcher import fetch_mint_versions, fetch_mint_isos
from .fetchers.arch_fetcher import fetch_arch_isos
from .fetchers.opensuse_fetcher import fetch_opensuse_versions, fetch_opensuse_isos
from .fetchers.endeavouros_fetcher import fetch_endeavouros_isos


class VersionFetcherWorker(QObject):
    finished = Signal(object, str)
    error = Signal(str, str)

    def __init__(self, fetch_function, config):
        super().__init__()
        self.fetch_function = fetch_function
        self.config = config
        self._is_running = True
        self.distro_name = config.get("name", "Unknown Distro")

    def run(self):
        if not self._is_running:
            self.finished.emit(None, self.distro_name)
            return

        distro_type = self.config["type"]
        versions_data = []
        error_message = None

        try:
            if distro_type == "archlinux":
                versions_data = [
                    {
                        "name": "Latest",
                        "id": "latest",
                        "url": self.config.get("base_url", ""),
                    }
                ]
            elif distro_type == "endeavouros":
                versions_data = [
                    {
                        "name": "Latest",
                        "id": "latest",
                        "url": self.config.get("base_url", ""),
                    }
                ]
            elif self.fetch_function:
                versions_data, error_message = self.fetch_function(self.config)
            else:
                error_message = f"No fetch function provided for type: {distro_type}"

            if not self._is_running:
                self.finished.emit(None, self.distro_name)
                return

            if error_message:
                self.error.emit(error_message, "versions")
            else:
                self.finished.emit(versions_data, self.distro_name)
        except Exception as e:
            if self._is_running:
                self.error.emit(
                    f"Error fetching versions for {self.distro_name}: {str(e)}",
                    "versions",
                )

    def stop(self):
        self._is_running = False


class IsoFetcherWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fetch_function, config, version_data):
        super().__init__()
        self._fetch_function = fetch_function
        self._config = config
        self._version_data = version_data
        self._is_running = True

    def run(self):
        if not self._is_running:
            self.finished.emit(None)
            return
        try:
            distro_type = self._config["type"]
            version_id = self._version_data.get("id")
            version_url = self._version_data.get("url")

            isos_data, error_message = None, None

            if distro_type == "ubuntu":
                isos_data, error_message = fetch_ubuntu_isos(version_id, self._config)
            elif distro_type == "fedora" or distro_type.startswith("fedora_"):
                isos_data, error_message = fetch_fedora_isos(version_url)
            elif distro_type == "debian":
                isos_data, error_message = fetch_debian_isos(self._config, version_id)
            elif distro_type.startswith("linuxmint"):
                isos_data, error_message = fetch_mint_isos(self._config, version_id)
            elif distro_type == "archlinux":
                isos_data, error_message = fetch_arch_isos(self._config)
            elif distro_type == "opensuse_leap" or distro_type == "opensuse_tumbleweed":
                isos_data, error_message = fetch_opensuse_isos(
                    version_url, self._config, self._version_data
                )
            elif distro_type == "endeavouros":
                isos_data, error_message = fetch_endeavouros_isos(self._config)
            else:
                error_message = f"ISO fetching not implemented for type: {distro_type}"

            if not self._is_running:
                self.finished.emit(None)
                return

            if error_message:
                self.error.emit(error_message)
            else:
                self.finished.emit(isos_data)
        except Exception as e:
            if self._is_running:
                self.error.emit(f"Failed to fetch ISOs: {str(e)}")

    def stop(self):
        self._is_running = False


class IsoDownloaderWidget(QWidget):
    # A widget for downloading ISO images of various Linux distributions.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_thread = None
        self.version_fetch_thread = None
        self.iso_fetch_thread = None
        self.currently_downloaded_file = None
        self.version_fetch_thread = None
        self.version_fetch_worker = None
        self.iso_fetch_thread = None
        self.iso_fetch_worker = None
        self.version_model = QStandardItemModel(self) # Keep for version_view
        self.iso_model = QStandardItemModel(self)     # Keep for iso_view
        self.setup_ui()
        self.load_default_download_location()

    def setup_ui(self):
        # Set up the user interface components.
        self.setWindowTitle("ISO Downloader")
        self.setMinimumSize(600, 200)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        distro_layout = QHBoxLayout()
        distro_label = QLabel("Linux Distribution:")
        self.distro_combo = QComboBox(self)  # Changed to QComboBox
        self.distro_combo.setPlaceholderText("Search distributions...") # Standard placeholder
        # self.distro_model is no longer set here for distro_combo
        self.populate_distro_combo()
        distro_layout.addWidget(distro_label)
        distro_layout.addWidget(self.distro_combo, 1)
        main_layout.addLayout(distro_layout)

        version_layout = QHBoxLayout()
        version_label = QLabel("Version:")
        # self.version_model is already initialized in __init__
        self.version_view = QComboBox(self)  # Changed to QComboBox
        self.version_view.setModel(self.version_model) # Still using model
        self.version_view.setPlaceholderText("Search versions...")
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_view, 1)
        main_layout.addLayout(version_layout)

        iso_layout = QHBoxLayout()
        iso_label = QLabel("ISO File:")
        # self.iso_model is already initialized in __init__
        self.iso_view = QComboBox(self)  # Changed to QComboBox
        self.iso_view.setModel(self.iso_model) # Still using model
        self.iso_view.setPlaceholderText("Search ISOs...")
        iso_layout.addWidget(iso_label)
        iso_layout.addWidget(self.iso_view, 1)
        main_layout.addLayout(iso_layout)

        dest_layout = QHBoxLayout()
        dest_label = QLabel("Destination:")
        self.dest_edit = QLineEdit(self)
        self.dest_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_dest)
        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_edit, 1)
        dest_layout.addWidget(browse_button)
        main_layout.addLayout(dest_layout)

        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_info_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.time_label = QLabel("")
        progress_info_layout.addWidget(self.status_label, 1)
        progress_info_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(progress_info_layout)
        main_layout.addLayout(progress_layout)

        buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_versions)
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_iso)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.download_button)
        buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(buttons_layout)

        self.distro_combo.currentIndexChanged.connect(self.on_distro_changed)
        self.version_view.currentIndexChanged.connect(self.on_version_changed)
        self.iso_view.currentIndexChanged.connect(self.on_iso_selected)

        self._update_ui_state(loading=False, ready_message="Select a distribution.")

    def populate_distro_combo(self):
        # Populate the distro combo box with categorized items.
        self.distro_combo.clear()
        # Add a placeholder item that signifies no selection
        self.distro_combo.addItem("Select a distribution...", None)

        categories_data = {
            "Ubuntu Family": [],
            "Fedora Family": [],
            "Debian Family": [],
            "Arch Family": [],
            "openSUSE": [],
            "Other": [],
        }

        # Assign distributions to categories_data (just names and config for now)
        for distro_name, config in DISTRO_CONFIG.items():
            distro_data = distro_name # This is the key for DISTRO_CONFIG

            if "ubuntu" in config["type"] or "ubuntu" in distro_name.lower():
                categories_data["Ubuntu Family"].append((distro_name, distro_data))
            elif "fedora" in config["type"] or "fedora" in distro_name.lower():
                categories_data["Fedora Family"].append((distro_name, distro_data))
            elif (
                "debian" in config["type"]
                or "debian" in distro_name.lower()
                or "mint" in distro_name.lower()
            ):
                categories_data["Debian Family"].append((distro_name, distro_data))
            elif (
                "arch" in config["type"]
                or "arch" in distro_name.lower()
                or "endeavour" in distro_name.lower()
            ):
                categories_data["Arch Family"].append((distro_name, distro_data))
            elif "suse" in config["type"] or "suse" in distro_name.lower():
                categories_data["openSUSE"].append((distro_name, distro_data))
            else:
                categories_data["Other"].append((distro_name, distro_data))

        # Add categories and items to the combo box model
        for category_name, items_data in categories_data.items():
            if not items_data:
                continue

            # Add category header as a disabled item
            self.distro_combo.addItem(f"--- {category_name} ---")
            model = self.distro_combo.model()
            last_item_idx = self.distro_combo.count() - 1
            if isinstance(model, QStandardItemModel): # Check if it's QStandardItemModel
                 item = model.item(last_item_idx)
                 if item:
                    item.setEnabled(False)
            else: # For default model, set flags
                index = model.index(last_item_idx, 0)
                model.setData(index, 0, Qt.ItemDataRole.UserRole - 1) # Make it non-selectable by clearing flags

            for item_name, item_data_payload in items_data:
                self.distro_combo.addItem(item_name, item_data_payload) # UserData is the distro_key

        # self.distro_combo.expand_all() # Not applicable for QComboBox

    def load_default_download_location(self):
        # Set the default download location to Downloads folder.
        download_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.dest_edit.setText(download_dir)

    def browse_dest(self):
        # Open a dialog to select download destination.
        current_dir = self.dest_edit.text()
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Download Location", current_dir
        )
        if dir_path:
            self.dest_edit.setText(dir_path)

    def get_selected_distro_name(self):
        # Get the name of the currently selected distribution.
        # This method might be simplified or removed if not used externally,
        # as currentData() is used directly in most places.
        return self.distro_combo.currentData(Qt.UserRole)

    def on_distro_changed(self, index):
        # Handle distribution change.
        # index is the numerical index in QComboBox.
        # We rely on currentData() to get the actual payload.
        distro_name_key = self.distro_combo.currentData(Qt.UserRole)

        if index < 0 or distro_name_key is None: # Handles placeholder or unselected state
            self.version_model.clear()
            self.iso_model.clear()
            self._update_ui_state(loading=False, ready_message="Select a distribution.")
            return

        self.refresh_versions()

    def refresh_versions(self):
        # Refresh the version list for the selected distribution.
        self._stop_thread_if_running("version")
        self._stop_thread_if_running("iso")

        self.version_model.clear()
        self.iso_model.clear()
        self._update_ui_state(loading=True, status_message="Fetching versions...")

        distro_name_key = self.distro_combo.currentData(Qt.UserRole)
        if not distro_name_key or distro_name_key not in DISTRO_CONFIG:
            self._update_ui_state(
                loading=False,
                error_message="No distribution selected or config not found.",
            )
            return

        distro_config = DISTRO_CONFIG[distro_name_key]
        distro_config["name"] = distro_name_key

        distro_type = distro_config.get("type")
        fetch_function = None

        if distro_type == "ubuntu":
            fetch_function = fetch_ubuntu_versions
        elif distro_type == "fedora" or distro_type.startswith("fedora_"):
            fetch_function = fetch_fedora_versions
        elif distro_type == "debian":
            fetch_function = fetch_debian_versions
        elif distro_type.startswith("linuxmint"):
            fetch_function = fetch_mint_versions
        elif distro_type == "opensuse_leap" or distro_type == "opensuse_tumbleweed":
            fetch_function = fetch_opensuse_versions
        elif distro_type not in ["archlinux", "endeavouros"]:
            self._update_ui_state(
                loading=False,
                error_message=f"Version fetching not implemented for {distro_type}",
            )
            return

        self.version_fetch_thread = QThread(self)
        self.version_fetch_worker = VersionFetcherWorker(fetch_function, distro_config)
        self.version_fetch_worker.moveToThread(self.version_fetch_thread)

        self.version_fetch_worker.finished.connect(self._on_versions_fetched)
        self.version_fetch_worker.error.connect(
            lambda msg, context: self._on_fetch_error(msg, context)
        )
        self.version_fetch_thread.started.connect(self.version_fetch_worker.run)
        self.version_fetch_thread.finished.connect(
            lambda: self._on_thread_finished_cleanup("version")
        )

        self.version_fetch_thread.start()

    def on_version_changed(self, index: int):
        # Handle version change and update ISO list.
        version_data = self.version_view.currentData(Qt.UserRole)

        if not version_data or not isinstance(version_data, dict):
            self.iso_model.clear()
            self._update_ui_state(
                loading=False, error_message="Select a valid version to see ISOs."
            )
            return

        self.update_iso_list()

    def on_iso_selected(self, index: int):
        # Handles ISO selection change.
        self._update_ui_state(loading=False)

    def update_iso_list(self):
        # Update the ISO file list for the selected version.
        self._stop_thread_if_running("iso")
        self.iso_model.clear()
        self._update_ui_state(loading=True, status_message="Fetching ISOs...")

        distro_name = self.distro_combo.currentData(Qt.UserRole)
        version_data = self.version_view.currentData(Qt.UserRole)

        if not distro_name or not version_data:
            self._update_ui_state(
                loading=False, error_message="Distribution or version not selected."
            )
            return

        distro_config = DISTRO_CONFIG.get(distro_name)
        if not distro_config:
            self._update_ui_state(
                loading=False,
                error_message=f"Configuration not found for {distro_name}.",
            )
            return

        self.iso_fetch_thread = QThread(self)
        self.iso_fetch_worker = IsoFetcherWorker(None, distro_config, version_data)
        self.iso_fetch_worker.moveToThread(self.iso_fetch_thread)

        self.iso_fetch_worker.finished.connect(self._on_isos_fetched)
        self.iso_fetch_worker.error.connect(
            lambda msg: self._on_fetch_error(msg, "iso")
        )
        self.iso_fetch_thread.started.connect(self.iso_fetch_worker.run)
        self.iso_fetch_thread.finished.connect(
            lambda: self._on_thread_finished_cleanup("iso")
        )

        self.iso_fetch_thread.start()

    def disable_download_controls(self, disable):
        # Enable or disable download-related controls.
        self.download_button.setEnabled(not disable)

    def download_iso(self):
        # Start downloading the selected ISO file.
        iso_data = self.iso_view.currentData(Qt.UserRole)
        if not iso_data:
            self.status_label.setText("Please select an ISO file to download.")
            return

        dest_dir = self.dest_edit.text()
        if not dest_dir or not os.path.isdir(dest_dir):
            self.status_label.setText("Please select a valid destination directory.")
            return

        distro_name = self.distro_combo.currentData(Qt.UserRole)
        version_data = self.version_view.currentData(Qt.UserRole)

        if not distro_name or not version_data:
            self.status_label.setText("Distro or version not selected properly.")
            return

        dest_file = os.path.join(
            dest_dir,
            clean_filename(
                iso_data["name"], base_prefix=distro_name, version=version_data["name"]
            ),
        )

        if os.path.exists(dest_file):
            self.status_label.setText(
                f"File already exists: {os.path.basename(dest_file)}"
            )
            return

        self.download_url = iso_data["url"]
        self.currently_downloaded_file = dest_file

        self.status_label.setText(f"Downloading {os.path.basename(dest_file)}...")
        self.progress_bar.setValue(0)
        self.time_label.setText("")

        self.download_thread = IsoDownloadWorker(self.download_url, dest_file, self)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.status.connect(self.update_status)
        self.download_thread.finished.connect(self.download_finished)

        self.download_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.download_thread.start()

    def update_progress(self, percent, speed_MBps, time_left_s, time_spent_s):
        # Update the progress bar and time information.
        self.progress_bar.setValue(percent)

        # Format speed
        if speed_MBps >= 1.0:
            speed_str = f"{speed_MBps:.1f} MB/s"
        else:
            speed_str = f"{speed_MBps * 1000:.0f} KB/s"

        # Format time
        time_left = format_time_display(time_left_s)
        time_spent = format_time_display(time_spent_s)

        self.time_label.setText(
            f"{speed_str} | Time left: {time_left} | Elapsed: {time_spent}"
        )

    def update_status(self, message):
        # Update the status label with a message.
        self.status_label.setText(message)

    def download_finished(self, success, message):
        # Handle download completion.
        self.download_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.download_thread = None

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(
                f"Download completed: {os.path.basename(self.currently_downloaded_file)}"
            )
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText(f"Download failed: {message}")

        self.currently_downloaded_file = None

    def cancel_download(self):
        # Cancel the current download.
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait(2000)

            if self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait()

                if self.currently_downloaded_file and os.path.exists(
                    self.currently_downloaded_file
                ):
                    try:
                        os.remove(self.currently_downloaded_file)
                        self.status_label.setText(
                            "Download cancelled and partial file removed."
                        )
                    except Exception as e:
                        self.status_label.setText(
                            f"Download cancelled but could not remove partial file: {str(e)}"
                        )
            else:
                self.status_label.setText("Download cancelled.")

            self.progress_bar.setValue(0)
            self.time_label.setText("")
            self.download_button.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.download_thread = None
            self.currently_downloaded_file = None

    def closeEvent(self, event):
        # Handle close event to make sure downloads and fetchers are properly terminated.
        self._stop_thread_if_running("version")
        self._stop_thread_if_running("iso")

        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            try:
                self.download_thread.progress.disconnect()
                self.download_thread.status.disconnect()
                self.download_thread.finished.disconnect()
            except RuntimeError:
                pass
            self.download_thread.wait(1000)
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait()

        self.download_thread = None
        self.currently_downloaded_file = None
        event.accept()

    def _stop_thread_if_running(self, thread_type):
        thread_attr = f"{thread_type}_fetch_thread"
        worker_attr = f"{thread_type}_fetch_worker"

        thread = getattr(self, thread_attr, None)
        worker = getattr(self, worker_attr, None)

        if thread and thread.isRunning():
            if worker:
                worker.stop()
            thread.quit()
            thread.wait(2000)
            if thread.isRunning():
                thread.terminate()
                thread.wait()

        setattr(self, thread_attr, None)
        setattr(self, worker_attr, None)

    def _update_ui_state(
        self, loading, status_message=None, ready_message=None, error_message=None
    ):
        self.distro_combo.setEnabled(not loading)
        self.version_view.setEnabled(not loading)
        self.iso_view.setEnabled(not loading)
        self.refresh_button.setEnabled(not loading)

        can_download = (
            not loading
            and self.iso_model.rowCount() > 0
            and self.iso_view.currentIndex() >= 0
        )
        self.download_button.setEnabled(can_download)

        if loading:
            self.status_label.setText(status_message or "Loading...")
        elif error_message:
            self.status_label.setText(error_message)
        elif ready_message:
            self.status_label.setText(ready_message)

    def _on_thread_finished_cleanup(self, thread_type):
        thread_attr = f"{thread_type}_fetch_thread"
        worker_attr = f"{thread_type}_fetch_worker"

        thread = getattr(self, thread_attr, None)
        worker = getattr(self, worker_attr, None)

        if thread and thread.isRunning():
            thread.quit()
            thread.wait(1000)
            if thread.isRunning():
                thread.terminate()
                thread.wait()

        if worker:
            worker.deleteLater()
        if thread:
            thread.deleteLater()

        setattr(self, thread_attr, None)
        setattr(self, worker_attr, None)

    def _on_versions_fetched(self, versions_data, distro_name_from_worker):
        if versions_data is not None:
            self.version_model.clear()
            for version_info in versions_data:
                item = QStandardItem(version_info["name"])
                item.setData(version_info, Qt.UserRole)
                self.version_model.appendRow(item)

            if self.version_model.rowCount() > 0:
                self.version_view.setCurrentIndex(0) # QComboBox will use model's first item
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No versions found for {distro_name_from_worker}.",
                )
        else:
            if self.version_fetch_worker and not self.version_fetch_worker._is_running:
                self._update_ui_state(
                    loading=False,
                    ready_message=f"Version fetching cancelled for {distro_name_from_worker}.",
                )
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No versions data received for {distro_name_from_worker}.",
                )

        if not (versions_data and self.version_model.rowCount() > 0):
            self._update_ui_state(loading=False)

    def _on_isos_fetched(self, isos_data):
        distro_name = self.distro_combo.currentData(Qt.UserRole)
        version_data = self.version_view.currentData(Qt.UserRole) # QComboBox.currentData()
        version_name = (
            version_data.get("name", "selected version")
            if isinstance(version_data, dict) # Ensure version_data is a dict
            else "selected version"
        )

        if isos_data:
            self.iso_model.clear()
            for iso_info in isos_data:
                item = QStandardItem(iso_info["name"])
                item.setData(iso_info, Qt.UserRole)
                self.iso_model.appendRow(item)

            if self.iso_model.rowCount() > 0:
                self.iso_view.setCurrentIndex(0) # QComboBox will use model's first item
                self._update_ui_state(
                    loading=False,
                    ready_message=f"Found {self.iso_model.rowCount()} ISOs for {distro_name} {version_name}.",
                )
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No ISOs found for {distro_name} {version_name}.",
                )
        else:
            if self.iso_fetch_worker and not self.iso_fetch_worker._is_running:
                self._update_ui_state(
                    loading=False, ready_message="ISO fetching cancelled."
                )
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No ISOs found or error for {distro_name} {version_name}.",
                )

        self._on_thread_finished_cleanup("iso")
        self._update_ui_state(loading=False)

    def _on_fetch_error(self, error_message, context_or_thread_type):
        thread_type = context_or_thread_type
        if context_or_thread_type == "versions":
            thread_type = "version"
        elif context_or_thread_type == "isos":
            thread_type = "iso"

        self.status_label.setText(f"Error: {error_message}")
        self._update_ui_state(
            loading=False, error_message=f"Error ({thread_type}): {error_message}"
        )
