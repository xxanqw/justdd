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
    QFrame,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QStandardPaths, QModelIndex, QThread, Signal, QObject
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QPixmap
import os

from .download_worker import IsoDownloadWorker
from .distro_config import DISTRO_CONFIG
from .utils import format_time_display, clean_filename, send_notification, resource_path

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
                result = self.fetch_function(self.config)
                if isinstance(result, tuple) and len(result) == 2:
                    versions_data, error_message = result
                else:
                    versions_data = result if result else []
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
                result = fetch_fedora_isos(version_url)
                if isinstance(result, tuple) and len(result) == 2:
                    isos_data, error_message = result
                else:
                    isos_data = result if result else []
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
        self.version_model = QStandardItemModel(self)
        self.iso_model = QStandardItemModel(self)
        self.setup_ui()
        self.load_default_download_location()

    def setup_ui(self):
        self.setWindowTitle("JustDD - ISO Downloader")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        # Remove local stylesheet - use global styles only
        self.setStyleSheet("")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header with proper spacing
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel("💿")
        icon_label.setStyleSheet("font-size: 32pt; border: none; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(48, 48)
        
        # Title and subtitle container
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        
        title_label = QLabel("ISO Downloader")
        title_label.setProperty("class", "title")
        
        subtitle_label = QLabel("Download Linux distributions directly")
        subtitle_label.setProperty("class", "subtitle")
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)

        # Selection Section with improved layout
        selection_frame = QFrame()
        selection_frame.setObjectName("selectionFrame")
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setContentsMargins(25, 25, 25, 25)
        selection_layout.setSpacing(20)

        # Grid layout with consistent spacing
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowMinimumHeight(0, 50)  # Distribution row
        grid_layout.setRowMinimumHeight(1, 50)  # Version row
        grid_layout.setRowMinimumHeight(2, 50)  # ISO row
        grid_layout.setRowMinimumHeight(3, 50)  # Destination row

        # Distribution selection
        distro_label = QLabel("Distribution:")
        distro_label.setProperty("class", "field-label")
        distro_label.setFixedWidth(100)
        distro_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.distro_combo = QComboBox()
        self.distro_combo.setMinimumHeight(36)
        self.distro_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.populate_distro_combo()
        
        grid_layout.addWidget(distro_label, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(self.distro_combo, 0, 1)

        # Version selection
        version_label = QLabel("Version:")
        version_label.setProperty("class", "field-label")
        version_label.setFixedWidth(100)
        version_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.version_view = QComboBox()
        self.version_view.setModel(self.version_model)
        self.version_view.setMinimumHeight(36)
        self.version_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.version_view.setEnabled(False)
        
        grid_layout.addWidget(version_label, 1, 0, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(self.version_view, 1, 1)

        # ISO selection
        iso_label = QLabel("ISO File:")
        iso_label.setProperty("class", "field-label")
        iso_label.setFixedWidth(100)
        iso_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.iso_view = QComboBox()
        self.iso_view.setModel(self.iso_model)
        self.iso_view.setMinimumHeight(36)
        self.iso_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.iso_view.setEnabled(False)
        
        grid_layout.addWidget(iso_label, 2, 0, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(self.iso_view, 2, 1)

        # Destination selection
        dest_label = QLabel("Destination:")
        dest_label.setProperty("class", "field-label")
        dest_label.setFixedWidth(100)
        dest_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        dest_layout = QHBoxLayout()
        dest_layout.setSpacing(10)
        
        self.dest_edit = QLineEdit()
        self.dest_edit.setReadOnly(True)
        self.dest_edit.setMinimumHeight(36)
        self.dest_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        browse_button = QPushButton("Browse...")
        browse_button.setFixedWidth(100)
        browse_button.setMinimumHeight(36)
        browse_button.clicked.connect(self.browse_dest)
        
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(browse_button)
        
        grid_layout.addWidget(dest_label, 3, 0, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addLayout(dest_layout, 3, 1)

        selection_layout.addLayout(grid_layout)
        main_layout.addWidget(selection_frame)

        # Progress Section
        progress_frame = QFrame()
        progress_frame.setProperty("class", "section")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(25, 25, 25, 25)
        progress_layout.setSpacing(15)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(28)
        
        # Status information
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        self.status_label = QLabel("Ready to download")
        self.status_label.setProperty("class", "status")
        
        self.time_label = QLabel("")
        self.time_label.setProperty("class", "status-secondary")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.time_label)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(status_layout)
        main_layout.addWidget(progress_frame)

        # Action buttons with proper spacing
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(5, 15, 5, 15)
        buttons_layout.setSpacing(15)

        # Left side buttons
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.setFixedWidth(120)
        self.refresh_button.clicked.connect(self.refresh_versions)

        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addStretch()

        # Right side buttons
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("class", "danger")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        
        self.download_button = QPushButton("📥 Download")
        self.download_button.setProperty("class", "primary")
        self.download_button.setMinimumHeight(40)
        self.download_button.setFixedWidth(130)
        self.download_button.clicked.connect(self.download_iso)
        self.download_button.setEnabled(False)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.download_button)

        main_layout.addWidget(QWidget())  # Add some spacing
        main_layout.addLayout(buttons_layout)

        # Connect signals
        self.distro_combo.currentIndexChanged.connect(self.on_distro_changed)
        self.version_view.currentIndexChanged.connect(self.on_version_changed)
        self.iso_view.currentIndexChanged.connect(self.on_iso_selected)

        self._update_ui_state(loading=False, ready_message="Select a distribution to begin.")

    def populate_distro_combo(self):
        self.distro_combo.clear()
        self.distro_combo.addItem("Select a distribution...", None)

        categories_data = {
            "Ubuntu Family": [],
            "Fedora Family": [],
            "Debian Family": [],
            "Arch Family": [],
            "openSUSE": [],
            "Other": [],
        }

        for distro_name, config in DISTRO_CONFIG.items():
            distro_data = distro_name

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

        for category_name, items_data in categories_data.items():
            if not items_data:
                continue

            # Add category separator
            self.distro_combo.addItem(f"─── {category_name} ───")
            model = self.distro_combo.model()
            last_item_idx = self.distro_combo.count() - 1
            if isinstance(model, QStandardItemModel):
                item = model.item(last_item_idx)
                if item:
                    item.setEnabled(False)
                    # Style category headers
                    item.setForeground(QStandardItem().foreground())
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)

            for item_name, item_data_payload in items_data:
                self.distro_combo.addItem(f"  {item_name}", item_data_payload)

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

        if index < 0 or distro_name_key is None:
            self.version_model.clear()
            self.iso_model.clear()
            self.version_view.setEnabled(False)
            self.iso_view.setEnabled(False)
            self._update_ui_state(loading=False, ready_message="Select a distribution to begin.")
            return

        self.version_view.setEnabled(True)
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
            self.iso_view.setEnabled(False)
            self._update_ui_state(
                loading=False, ready_message="Select a version to see available ISOs."
            )
            return

        self.iso_view.setEnabled(True)
        self.update_iso_list()

    def on_iso_selected(self, index: int):
        iso_data = self.iso_view.currentData(Qt.UserRole)
        dest_valid = self.dest_edit.text().strip() and os.path.isdir(self.dest_edit.text())
        can_download = (
            iso_data is not None and dest_valid
        )
        self.download_button.setEnabled(can_download)
        
        if can_download:
            self._update_ui_state(loading=False, ready_message="Ready to download.")
        else:
            self._update_ui_state(loading=False, ready_message="Select an ISO file to download.")

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
            filename = os.path.basename(self.currently_downloaded_file)
            self.status_label.setText(f"✅ Download completed: {filename}")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            send_notification(
                title="ISO Download Complete", 
                message=f"Successfully downloaded {filename}",
            )
            self.time_label.setText("Download complete!")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText(f"❌ Download failed: {message}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.time_label.setText("")

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
        # Update UI state based on current operation
        self.distro_combo.setEnabled(not loading)
        self.version_view.setEnabled(not loading and self.version_model.rowCount() > 0)
        self.iso_view.setEnabled(not loading and self.iso_model.rowCount() > 0)
        self.refresh_button.setEnabled(not loading and self.distro_combo.currentData() is not None)

        # Enable download only when everything is ready
        iso_data = self.iso_view.currentData(Qt.UserRole)
        dest_valid = self.dest_edit.text().strip() and os.path.isdir(self.dest_edit.text())
        can_download = (
            not loading
            and iso_data is not None
            and dest_valid
        )
        self.download_button.setEnabled(can_download)

        # Update status message
        if loading:
            self.status_label.setText(status_message or "Loading...")
            self.status_label.setStyleSheet("color: #f9e79f;")
        elif error_message:
            self.status_label.setText(f"❌ {error_message}")
            self.status_label.setStyleSheet("color: #e74c3c;")
        elif ready_message:
            self.status_label.setText(f"✓ {ready_message}")
            self.status_label.setStyleSheet("color: #27ae60;")
        else:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #ffffff;")

    def _on_versions_fetched(self, versions_data, distro_name_from_worker):
        if versions_data is not None and len(versions_data) > 0:
            self.version_model.clear()
            for version_info in versions_data:
                item = QStandardItem(version_info["name"])
                item.setData(version_info, Qt.UserRole)
                self.version_model.appendRow(item)

            self.version_view.setCurrentIndex(0)
            self.version_view.setEnabled(True)
            self._update_ui_state(
                loading=False,
                ready_message=f"Found {len(versions_data)} versions for {distro_name_from_worker}."
            )
        else:
            self.version_view.setEnabled(False)
            if self.version_fetch_worker and not self.version_fetch_worker._is_running:
                self._update_ui_state(
                    loading=False,
                    ready_message=f"Version fetching cancelled for {distro_name_from_worker}.",
                )
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No versions found for {distro_name_from_worker}.",
                )

    def _on_isos_fetched(self, isos_data):
        distro_name = self.distro_combo.currentData(Qt.UserRole)
        version_data = self.version_view.currentData(Qt.UserRole)
        version_name = (
            version_data.get("name", "selected version")
            if isinstance(version_data, dict)
            else "selected version"
        )

        if isos_data and len(isos_data) > 0:
            self.iso_model.clear()
            for iso_info in isos_data:
                item = QStandardItem(iso_info["name"])
                item.setData(iso_info, Qt.UserRole)
                self.iso_model.appendRow(item)

            self.iso_view.setCurrentIndex(0)
            self.iso_view.setEnabled(True)
            self._update_ui_state(
                loading=False,
                ready_message=f"Found {len(isos_data)} ISOs for {distro_name} {version_name}.",
            )
        else:
            self.iso_view.setEnabled(False)
            if self.iso_fetch_worker and not self.iso_fetch_worker._is_running:
                self._update_ui_state(
                    loading=False, ready_message="ISO fetching cancelled."
                )
            else:
                self._update_ui_state(
                    loading=False,
                    error_message=f"No ISOs found for {distro_name} {version_name}.",
                )

        self._on_thread_finished_cleanup("iso")

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
