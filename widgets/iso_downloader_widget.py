from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QFileDialog,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths
from PySide6.QtGui import QStandardItemModel, QStandardItem
import requests
import os
import re
from bs4 import BeautifulSoup
import time

# Unified configuration for all distributions
DISTRO_CONFIG = {
    # Ubuntu Flavors
    "Ubuntu (Official)": {"type": "ubuntu", "base_url": "https://releases.ubuntu.com/"},
    "Kubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/kubuntu/releases/",
    },
    "Xubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/xubuntu/releases/",
    },
    "Lubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/lubuntu/releases/",
    },
    "Ubuntu Budgie": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-budgie/releases/",
    },
    "Ubuntu MATE": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-mate/releases/",
    },
    "Ubuntu Studio": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntustudio/releases/",
    },
    "Ubuntu Kylin": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntukylin/releases/",
    },
    "Edubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/edubuntu/releases/",
    },
    "Ubuntu Cinnamon": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntucinnamon/releases/",
    },
    "Ubuntu Unity": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-unity/releases/",
    },
    # Fedora Main Editions
    "Fedora Workstation": {
        "type": "fedora_main",
        "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
        "path_segment": "Workstation",
        "name_key": "Workstation",
    },
    "Fedora Server": {
        "type": "fedora_main",
        "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
        "path_segment": "Server",
        "name_key": "Server",
    },
    "Fedora IoT": {
        "type": "fedora_main",
        "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
        "path_segment": "IoT",
        "name_key": "IoT",
    },
    "Fedora Silverblue": {
        "type": "fedora_main",
        "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
        "path_segment": "Silverblue",
        "name_key": "Silverblue",
    },
    "Fedora Kinoite": {
        "type": "fedora_main",
        "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
        "path_segment": "Kinoite",
        "name_key": "Kinoite",
    },
    # Fedora Spins and Labs (Secondary)
    "Fedora KDE Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "KDE",
    },
    "Fedora Xfce Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "Xfce",
    },
    "Fedora Cinnamon Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "Cinnamon",
    },
    "Fedora MATE-Compiz Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "MATE-Compiz",
    },
    "Fedora LXQt Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "LXQt",
    },
    "Fedora i3 Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "i3",
    },
    "Fedora Sway Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "Sway",
    },
    "Fedora Budgie Spin": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Spins",
        "name_key": "Budgie",
    },
    "Fedora Games Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Games",
    },
    "Fedora Design Suite Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Design-suite",
    },
    "Fedora Python Classroom Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Python-Classroom",
    },
    "Fedora Security Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Security",
    },
    "Fedora Astronomy Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Astronomy",
    },
    "Fedora Robotics Suite Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Robotics",
    },
    "Fedora Jam Lab": {
        "type": "fedora_secondary",
        "base_url": "https://download.fedoraproject.org/pub/fedora-secondary/releases/",
        "category": "Labs",
        "name_key": "Jam",
    },
    # Arch Linux
    "Arch Linux": {
        "type": "archlinux",
        "base_url": "https://geo.mirror.pkgbuild.com/iso/",
    },
}


def format_time_display(seconds):
    if seconds == float("inf") or seconds < 0:
        return "--:--:--"
    if not seconds or seconds < 1:  # handles 0 or very small fractions
        return "00:00" if seconds < 3600 else "00:00:00"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


class IsoDownloadWorker(QThread):
    progress = Signal(
        int, float, float, float
    )  # percent, speed_MBps, time_left_s, time_spent_s
    status = Signal(
        str
    )  # This signal can still be emitted, but the widget won't display it in QTextEdit
    finished = Signal(bool, str)

    def __init__(self, url, dest, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest = dest
        self.start_time = 0
        self.last_update_time = 0
        self._is_running = True

    def run(self):
        try:
            self.status.emit(f"Starting download: {self.url}")
            self.start_time = time.time()
            self.last_update_time = self.start_time

            with requests.get(
                self.url, stream=True, timeout=30
            ) as r:  # Increased timeout
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                with open(self.dest, "wb") as f:
                    downloaded_size = 0
                    for chunk in r.iter_content(
                        chunk_size=8192 * 4
                    ):  # Increased chunk size
                        if not self._is_running:
                            self.status.emit("Download cancelled by user.")
                            self.finished.emit(False, "Download cancelled.")
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            current_time = time.time()
                            elapsed_time_total = current_time - self.start_time

                            if (
                                current_time - self.last_update_time >= 0.5
                                or downloaded_size == total_size
                            ):
                                percent = 0
                                if total_size > 0:
                                    percent = int(downloaded_size * 100 / total_size)

                                time_spent_s = elapsed_time_total

                                speed_bps = 0.0
                                speed_MBps = 0.0
                                time_left_s = float("inf")

                                if (
                                    elapsed_time_total > 0.001
                                ):  # Avoid division by zero or tiny elapsed time
                                    speed_bps = downloaded_size / elapsed_time_total
                                    speed_MBps = speed_bps / (
                                        1024 * 1024
                                    )  # Bytes to MegaBytes

                                if total_size > 0:
                                    if speed_bps > 0:
                                        time_left_s = (
                                            total_size - downloaded_size
                                        ) / speed_bps
                                    elif (
                                        downloaded_size < total_size
                                    ):  # Still downloading but no speed yet
                                        time_left_s = float("inf")
                                    else:  # Downloaded == total_size
                                        time_left_s = 0
                                # If total_size is 0, time_left_s remains float('inf')

                                self.progress.emit(
                                    percent, speed_MBps, time_left_s, time_spent_s
                                )
                                self.last_update_time = current_time

            if (
                not self._is_running
            ):  # Check again after loop in case of cancellation during final chunk
                return

            self.status.emit("Download complete.")
            final_elapsed_time = time.time() - self.start_time
            final_speed_MBps = 0.0
            if final_elapsed_time > 0 and total_size > 0:
                final_speed_MBps = (total_size / final_elapsed_time) / (1024 * 1024)
            self.progress.emit(100, final_speed_MBps, 0, final_elapsed_time)
            self.finished.emit(True, self.dest)
        except Exception as e:
            if self._is_running:  # Only emit error if not cancelled
                self.status.emit(f"Download failed: {e}")
                self.finished.emit(False, str(e))

    def stop(self):
        self._is_running = False


class IsoDownloaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Linux ISO Downloader")
        layout = QVBoxLayout(self)

        distro_layout = QHBoxLayout()
        distro_layout.addWidget(QLabel("Distribution:"))
        self.distro_combo = QComboBox()

        model = QStandardItemModel()
        self.distro_combo.setModel(model)

        sorted_distros = sorted(DISTRO_CONFIG.keys())

        categories = {
            "Ubuntu": "Ubuntu---",
            "Fedora": "Fedora---",
            "Arch": "Arch Linux---",
        }

        grouped_distros = {"Ubuntu": [], "Fedora": [], "Arch": [], "Other": []}
        for distro_name in sorted_distros:
            if distro_name.startswith("Ubuntu"):
                grouped_distros["Ubuntu"].append(distro_name)
            elif distro_name.startswith("Fedora"):
                grouped_distros["Fedora"].append(distro_name)
            elif distro_name.startswith("Arch"):
                grouped_distros["Arch"].append(distro_name)
            else:
                grouped_distros["Other"].append(distro_name)

        for category_name, separator_text in categories.items():
            if grouped_distros.get(category_name):  # Use .get for safety
                separator = QStandardItem(separator_text)
                separator.setFlags(Qt.NoItemFlags)
                separator.setData("separator", Qt.AccessibleDescriptionRole)
                model.appendRow(separator)
                for distro_name in grouped_distros[category_name]:
                    item = QStandardItem(distro_name)
                    model.appendRow(item)

        if grouped_distros["Other"]:
            if categories:
                separator = QStandardItem("Other---")
                separator.setFlags(Qt.NoItemFlags)
                separator.setData("separator", Qt.AccessibleDescriptionRole)
                model.appendRow(separator)
            for distro_name in grouped_distros["Other"]:
                item = QStandardItem(distro_name)
                model.appendRow(item)

        distro_layout.addWidget(self.distro_combo)
        layout.addLayout(distro_layout)

        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self.version_combo = QComboBox()
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)

        self.iso_type_combo = QComboBox()
        layout.addWidget(self.iso_type_combo)

        loc_layout = QHBoxLayout()
        self.location_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_location)
        loc_layout.addWidget(self.location_edit)
        loc_layout.addWidget(self.browse_button)
        layout.addLayout(loc_layout)

        self.download_button = QPushButton("Download ISO")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        progress_outer_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        progress_outer_layout.addWidget(self.progress_bar)

        self.progress_info_label = QLabel("--.- MB/s  --:--:-- left  --:--:-- spent")
        self.progress_info_label.setMinimumWidth(280)
        progress_outer_layout.addWidget(self.progress_info_label)
        layout.addLayout(progress_outer_layout)

        # QTextEdit for status_output is removed

        self._versions = None
        self._current_distro_isos = None
        self.worker = None

        self.default_download_dir = QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation
        )
        if not self.default_download_dir:
            self.default_download_dir = os.path.join(
                os.path.expanduser("~"), "Downloads"
            )
        os.makedirs(self.default_download_dir, exist_ok=True)

        self.distro_combo.currentTextChanged.connect(self._on_distro_selected)
        self.version_combo.currentTextChanged.connect(
            self.fetch_isos_for_selected_version
        )
        self.version_combo.currentTextChanged.connect(
            self._update_download_location_text
        )
        self.iso_type_combo.currentTextChanged.connect(
            self._update_download_location_text
        )

        first_selectable_index = -1
        for i in range(model.rowCount()):
            if model.item(i).flags() & Qt.ItemIsSelectable:
                first_selectable_index = i
                break
        if first_selectable_index != -1:
            self.distro_combo.setCurrentIndex(first_selectable_index)
            self._on_distro_selected(self.distro_combo.currentText())
        else:
            self._on_distro_selected(None)

    def _on_distro_selected(self, distro_name):
        if not distro_name or distro_name.endswith("---"):
            self.setWindowTitle("Linux ISO Downloader")
            self.version_combo.clear()
            self.iso_type_combo.clear()
            self.iso_type_combo.addItem("N/A (select distribution)")
            self.iso_type_combo.setEnabled(False)
            self.version_combo.setEnabled(False)
            self.download_button.setEnabled(False)
            self._update_download_location_text()
            return

        self.download_button.setEnabled(True)
        self.setWindowTitle(f"{distro_name} ISO Downloader")
        self._versions = None
        self._current_distro_isos = {}
        self.version_combo.clear()
        self.iso_type_combo.clear()
        self.iso_type_combo.addItem("N/A (select version)")
        self.iso_type_combo.setEnabled(False)
        self.fetch_versions()
        self._update_download_location_text()

    def _update_download_location_text(self):
        distro_name = self.distro_combo.currentText()
        version = self.version_combo.currentText()
        iso_type_selected = self.iso_type_combo.currentText()

        if not distro_name or distro_name.endswith("---"):
            self.location_edit.setText(
                os.path.join(self.default_download_dir, "select-distro.iso")
            )
            return

        distro_file_prefix = (
            distro_name.replace(" (Official)", "")
            .replace(" Spin", "")
            .replace(" Lab", "")
            .replace(" ", "-")
            .lower()
        )
        filename_base = distro_file_prefix

        if (
            version
            and "Loading..." not in version
            and "Error" not in version
            and "No versions" not in version
        ):
            filename_base = f"{distro_file_prefix}-{version.replace('/', '')}"
        else:
            filename_base = f"{distro_file_prefix}-latest"

        suggested_filename = f"{filename_base}.iso"

        is_iso_type_valid = (
            self.iso_type_combo.isEnabled()
            and iso_type_selected
            and not any(
                indicator in iso_type_selected
                for indicator in ["N/A", "Error", "No ISOs", "Loading"]
            )
        )

        if is_iso_type_valid:
            iso_type_slug = (
                re.sub(r"[\(\)]", "", iso_type_selected).replace(" ", "-").lower()
            )
            iso_type_slug = re.sub(r"-+", "-", iso_type_slug)

            if iso_type_slug.startswith(distro_file_prefix):
                suggested_filename = f"{iso_type_slug}.iso"
            elif iso_type_slug:
                suggested_filename = f"{filename_base}-{iso_type_slug}.iso"

        suggested_filename = re.sub(r"[^\w\.\-]", "_", suggested_filename)
        suggested_filename = (
            suggested_filename.replace("__", "_")
            .replace("-_", "-")
            .replace("_-", "-")
            .lower()
        )
        suggested_filename = suggested_filename.replace("--", "-")

        full_path = os.path.join(self.default_download_dir, suggested_filename)
        if self.location_edit.text() != full_path:
            self.location_edit.setText(full_path)

    def fetch_versions(self):
        selected_distro_name = self.distro_combo.currentText()
        if (
            not selected_distro_name
            or selected_distro_name.endswith("---")
            or selected_distro_name not in DISTRO_CONFIG
        ):
            self.on_versions_fetched(
                [], f"Invalid distribution: {selected_distro_name}"
            )
            return

        self.version_combo.clear()
        self.version_combo.addItem("Loading versions...")
        self.version_combo.setEnabled(False)

        config = DISTRO_CONFIG[selected_distro_name]
        distro_type = config.get("type")

        if distro_type == "ubuntu":
            self._fetch_ubuntu_versions(config)
        elif distro_type in ["fedora_main", "fedora_secondary"]:
            self._fetch_fedora_versions(config)
        elif distro_type == "archlinux":
            self._fetch_arch_versions(config)
        else:
            self.on_versions_fetched([], f"Unsupported distro type: {distro_type}")

    def _fetch_arch_versions(self, config):
        base_url = config["base_url"]
        versions_list = []
        error_msg = ""
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            # Arch versions are dates like YYYY.MM.DD/
            versions_list = sorted(
                [
                    l.strip("/")
                    for l in links
                    if re.match(r"^\d{4}\.\d{2}\.\d{2}/?$", l)
                ],
                reverse=True,
            )
            versions_list = [v.replace("/", "") for v in versions_list]
        except Exception as e:
            error_msg = str(e)
        self.on_versions_fetched(versions_list, error_msg)

    def _fetch_ubuntu_versions(self, config):
        base_url = config["base_url"]
        versions_list = []
        error_msg = ""
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            versions_list = sorted(
                [
                    l.strip("/")
                    for l in links
                    if re.match(r"^[0-9]+\.[0-9]+(\.[0-9]+)?/?$", l)
                ],
                reverse=True,
            )
            versions_list = [v.replace("/", "") for v in versions_list]
        except Exception as e:
            error_msg = str(e)
        self.on_versions_fetched(versions_list, error_msg)

    def _fetch_fedora_versions(self, config):
        base_url = config["base_url"]
        versions_list = []
        error_msg = ""
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            version_candidates = [
                l.strip("/")
                for l in links
                if re.match(r"^[0-9]+/?$", l)
                and all(
                    keyword not in l.lower()
                    for keyword in ["development", "test", "rawhide", "beta", "latest"]
                )
            ]
            versions_list = sorted(
                [v.replace("/", "") for v in version_candidates],
                key=lambda v_str: int(v_str) if v_str.isdigit() else -1,
                reverse=True,
            )

        except Exception as e:
            error_msg = str(e)
        self.on_versions_fetched(versions_list, error_msg)

    def on_versions_fetched(self, versions_list, error):
        self.version_combo.clear()
        selected_distro_name = self.distro_combo.currentText()
        if error:
            self.version_combo.addItem(f"Error fetching versions")
            print(
                f"Version fetch error for {selected_distro_name}: {error}"
            )  # Optional: print to console
            self.version_combo.setEnabled(False)
        elif not versions_list:
            self.version_combo.addItem(f"No versions found")
            print(
                f"No versions found for {selected_distro_name}"
            )  # Optional: print to console
            self.version_combo.setEnabled(False)
        else:
            self._versions = versions_list
            self.version_combo.addItems(versions_list)
            self.version_combo.setEnabled(True)
            if versions_list:
                self.version_combo.setCurrentIndex(0)
                return
        self._update_download_location_text()

    def fetch_isos_for_selected_version(self, version_text):
        selected_distro_name = self.distro_combo.currentText()
        if (
            not selected_distro_name
            or selected_distro_name.endswith("---")
            or selected_distro_name not in DISTRO_CONFIG
        ):
            self.on_isos_fetched(
                version_text,
                {},
                f"Invalid distribution for ISO fetch: {selected_distro_name}",
            )
            return

        if (
            not version_text
            or "Loading..." in version_text
            or "Error" in version_text
            or "No versions" in version_text
        ):
            self.iso_type_combo.clear()
            self.iso_type_combo.addItem("N/A (select version)")
            self.iso_type_combo.setEnabled(False)
            self.download_button.setEnabled(False)
            return

        self.iso_type_combo.clear()
        self.iso_type_combo.addItem("Loading ISOs...")
        self.iso_type_combo.setEnabled(False)
        self.download_button.setEnabled(False)

        config = DISTRO_CONFIG[selected_distro_name]
        distro_type = config.get("type")

        if distro_type == "ubuntu":
            self._fetch_ubuntu_isos(config, version_text)
        elif distro_type == "fedora_main":
            self._fetch_fedora_main_isos(config, version_text)
        elif distro_type == "fedora_secondary":
            self._fetch_fedora_secondary_isos(config, version_text)
        elif distro_type == "archlinux":
            self._fetch_arch_isos(config, version_text)
        else:
            self.on_isos_fetched(
                version_text, {}, f"Unsupported distro type for ISOs: {distro_type}"
            )

    def _fetch_arch_isos(self, config, version):
        base_url = config["base_url"]
        iso_page_url = f"{base_url}{version}/"
        isos = {}
        error_msg = ""
        try:
            print(f"Trying Arch ISO path: {iso_page_url}")  # Optional
            resp = requests.get(iso_page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [
                a.get("href")
                for a in soup.find_all("a", href=True)
                if a.get("href", "").endswith(".iso")
            ]

            # Arch typically has one main ISO like archlinux-YYYY.MM.DD-x86_64.iso
            # Or archlinux-bootstrap-YYYY.MM.DD-x86_64.iso
            # Or archlinux-gui-YYYY.MM.DD-x86_64.iso (for unofficial spins if they were listed here)
            # We'll prioritize the standard one.

            standard_iso_pattern = rf"archlinux-{re.escape(version)}-x86_64\.iso$"
            found_standard = False
            for link_href in links:
                if re.search(standard_iso_pattern, link_href):
                    isos["Arch Linux (x86_64)"] = iso_page_url + link_href
                    found_standard = True
                    break

            if (
                not found_standard and links
            ):  # Fallback to any x86_64 iso if standard not found
                for link_href in links:
                    if "x86_64.iso" in link_href:
                        # Try to make a somewhat descriptive name
                        name_key = "Arch Linux"
                        if "bootstrap" in link_href:
                            name_key = "Arch Linux Bootstrap"
                        elif "gui" in link_href:
                            name_key = "Arch Linux GUI"  # Example

                        display_name = f"{name_key} (x86_64)"
                        counter = 1
                        original_display_name = display_name
                        while display_name in isos:
                            display_name = f"{original_display_name} v{counter+1}"
                            counter += 1
                        isos[display_name] = iso_page_url + link_href
                        # Take the first x86_64 if multiple, or list all if desired
                        # For simplicity, let's just take the first one if standard is not found
                        if not isos:  # if we want only one fallback
                            isos[display_name] = iso_page_url + link_href
                            break

            if not isos:
                error_msg = f"No suitable ISO files found on {iso_page_url}"

        except Exception as e:
            error_msg = f"Error fetching Arch Linux ISOs: {e}"
            print(error_msg)  # Optional
        self.on_isos_fetched(version, isos, error_msg)

    def _fetch_ubuntu_isos(self, config, version):
        distro_base_url = config["base_url"]
        isos = {}
        error_msg = ""
        try:
            base_version_path = f"{distro_base_url}{version}/"
            parent_dir_url = distro_base_url
            soup = None
            actual_iso_page_url = ""
            possible_paths = [f"{base_version_path}release/", base_version_path]

            try:
                resp_parent = requests.get(parent_dir_url, timeout=10)
                resp_parent.raise_for_status()
                soup_parent = BeautifulSoup(resp_parent.text, "html.parser")
                sub_version_links = [
                    a.get("href")
                    for a in soup_parent.find_all("a", href=True)
                    if a.get("href", "").startswith(version)
                    and a.get("href", "").endswith("/")
                ]
                sub_version_links = sorted(sub_version_links, reverse=True)
                for sub_ver_link in sub_version_links:
                    possible_paths.append(f"{parent_dir_url}{sub_ver_link}release/")
                    possible_paths.append(f"{parent_dir_url}{sub_ver_link}")
            except Exception as e_parent:
                print(f"Could not list parent directory {parent_dir_url}: {e_parent}")

            for path_attempt in possible_paths:
                try:
                    print(f"Trying ISO path: {path_attempt}")
                    resp = requests.get(path_attempt, timeout=10)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    actual_iso_page_url = path_attempt
                    print(f"Found ISOs at: {actual_iso_page_url}")
                    break
                except requests.exceptions.HTTPError as http_err:
                    if http_err.response.status_code == 404:
                        print(f"Path not found (404): {path_attempt}")
                        continue
                    else:
                        print(f"HTTP error for {path_attempt}: {http_err}")
                except requests.exceptions.RequestException as req_err:
                    print(f"Request error for {path_attempt}: {req_err}")

            if not soup:
                error_msg = f"Could not find ISO listing page for {self.distro_combo.currentText()} {version} after trying multiple paths."
                self.on_isos_fetched(version, isos, error_msg)
                return

            links = [
                a.get("href")
                for a in soup.find_all("a", href=True)
                if a.get("href", "").endswith(".iso")
            ]

            distro_name_key = self.distro_combo.currentText().lower()
            distro_name_key = (
                distro_name_key.replace(" (official)", "")
                .replace(" ubuntu", "")
                .strip()
            )

            if (
                "ubuntu" == distro_name_key
                or self.distro_combo.currentText() == "Ubuntu (Official)"
            ):
                iso_patterns = {
                    "Desktop (AMD64)": rf".*{re.escape(version)}.*desktop-amd64\.iso$",
                    "Server (AMD64)": rf".*{re.escape(version)}.*(?:live-)?server-amd64\.iso$",
                    "Desktop (ARM64)": rf".*{re.escape(version)}.*desktop-arm64\.iso$",
                    "Server (ARM64)": rf".*{re.escape(version)}.*(?:live-)?server-arm64\.iso$",
                    "Minimal (AMD64)": rf".*{re.escape(version)}.*minimal-amd64\.iso$",
                }
            else:
                iso_patterns = {
                    f"{distro_name_key.capitalize()} Desktop (AMD64)": rf".*{distro_name_key}.*{re.escape(version)}.*(?:desktop-)?amd64\.iso$",
                    f"{distro_name_key.capitalize()} (AMD64)": rf".*{distro_name_key}.*{re.escape(version)}.*amd64\.iso$",
                    f"{distro_name_key.capitalize()} Desktop (ARM64)": rf".*{distro_name_key}.*{re.escape(version)}.*(?:desktop-)?arm64\.iso$",
                    f"{distro_name_key.capitalize()} (ARM64)": rf".*{distro_name_key}.*{re.escape(version)}.*arm64\.iso$",
                }

            found_isos_this_round = {}
            for display_name, pattern in iso_patterns.items():
                for link_href in links:
                    if re.search(pattern, link_href, re.IGNORECASE):
                        if display_name not in found_isos_this_round:
                            found_isos_this_round[display_name] = (
                                actual_iso_page_url + link_href
                            )
                            break
            isos.update(found_isos_this_round)

            if not isos:
                print(
                    f"No specific ISOs found for {distro_name_key} {version}, trying generic amd64."
                )
                generic_amd64_isos = [
                    l for l in links if "amd64.iso" in l and version in l
                ]
                if generic_amd64_isos:
                    for i, iso_link in enumerate(generic_amd64_isos):
                        name_part = (
                            iso_link.replace(".iso", "")
                            .replace(f"-{version}", "")
                            .replace("-amd64", "")
                        )
                        name_part = (
                            name_part.split("-")[-1] if "-" in name_part else "Generic"
                        )
                        isos[
                            f"{name_part.capitalize()} (AMD64) {i+1 if len(generic_amd64_isos)>1 else ''}".strip()
                        ] = (actual_iso_page_url + iso_link)
                elif links:
                    print(f"No amd64 ISOs found, grabbing first available ISO.")
                    isos[f"ISO (from {links[0][:20]}...)"] = (
                        actual_iso_page_url + links[0]
                    )

            if not isos:
                error_msg = f"No ISO files found on {actual_iso_page_url}"

        except Exception as e:
            error_msg = f"Error fetching Ubuntu ISOs: {e}"
            print(error_msg)
        self.on_isos_fetched(version, isos, error_msg)

    def _parse_fedora_iso_filename(self, filename, name_key, arch):
        name_key_regex_part = re.escape(name_key)
        pattern_str = rf"Fedora(?:-{name_key_regex_part})?-(.*?)-{arch}-[\d\.\-]+(?:-CHECKSUM)?\.iso"
        match = re.match(pattern_str, filename, re.IGNORECASE)

        type_part_str = "ISO"
        if match:
            type_part = match.group(1)
            if type_part:
                type_part_str = type_part.replace("-", " ").strip().capitalize()
        else:
            temp_name = filename.replace(".iso", "")
            temp_name = re.sub(
                rf"Fedora-{name_key_regex_part}-?", "", temp_name, flags=re.IGNORECASE
            )
            temp_name = temp_name.replace(f"Fedora-", "")
            temp_name = temp_name.replace(f"-{arch}", "")
            temp_name = re.sub(r"-[\d\.\-]+(?:-CHECKSUM)?$", "", temp_name)
            temp_name = temp_name.replace("-", " ").strip()
            if temp_name:
                type_part_str = temp_name.capitalize()
            elif "live" in filename.lower():
                type_part_str = "Live"
            elif "dvd" in filename.lower():
                type_part_str = "DVD"
            elif "netinst" in filename.lower():
                type_part_str = "Netinstall"
            elif "ostree" in filename.lower():
                type_part_str = "Ostree"

        return f"{type_part_str} ({arch})"

    def _fetch_fedora_isos_common(
        self, base_iso_page_url_template, config, version, filter_name_key=None
    ):
        isos = {}
        error_msg_accumulator = []
        archs_to_try = ["x86_64", "aarch64"]

        distro_name_for_log = self.distro_combo.currentText()

        for arch in archs_to_try:
            iso_page_url = base_iso_page_url_template.format(version=version, arch=arch)
            print(f"Trying Fedora ISO path: {iso_page_url} for {distro_name_for_log}")

            try:
                resp = requests.get(iso_page_url, timeout=15)
                resp.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                if http_err.response.status_code == 404:
                    msg = f"No ISOs at {iso_page_url} (404)"
                    print(msg)
                    error_msg_accumulator.append(msg)
                    continue
                error_msg_accumulator.append(
                    f"HTTP error for {iso_page_url}: {http_err}"
                )
                print(f"HTTP error for {iso_page_url}: {http_err}")
                continue
            except requests.exceptions.RequestException as req_err:
                msg = f"Error accessing {iso_page_url}: {req_err}"
                print(msg)
                error_msg_accumulator.append(msg)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links_with_checksum = [
                a.get("href")
                for a in soup.find_all("a", href=True)
                if a.get("href", "").endswith(".iso.CHECKSUM")
            ]
            iso_filenames_from_checksum = [
                link.replace(".CHECKSUM", "") for link in links_with_checksum
            ]

            direct_iso_links = [
                a.get("href")
                for a in soup.find_all("a", href=True)
                if a.get("href", "").endswith(".iso")
            ]

            all_potential_iso_filenames = sorted(
                list(set(iso_filenames_from_checksum + direct_iso_links))
            )

            found_for_arch = False
            for iso_filename in all_potential_iso_filenames:
                if not iso_filename.endswith(".iso"):
                    continue

                expected_filename_part = filter_name_key or config.get("name_key")

                if expected_filename_part:
                    if (
                        f"Fedora-{expected_filename_part.replace(' ', '-')}-"
                        not in iso_filename
                    ):
                        continue

                if (
                    f"-{version}-" not in iso_filename
                    and f"_{version}_" not in iso_filename
                ):
                    pass

                display_name_key_for_parser = filter_name_key or config.get(
                    "name_key", "Fedora"
                )
                iso_type_display = self._parse_fedora_iso_filename(
                    iso_filename, display_name_key_for_parser, arch
                )

                original_iso_type_display = iso_type_display
                counter = 1
                while iso_type_display in isos:
                    iso_type_display = f"{original_iso_type_display} v{counter+1}"
                    counter += 1

                isos[iso_type_display] = iso_page_url.rstrip("/") + "/" + iso_filename
                found_for_arch = True

            if found_for_arch:
                print(f"Found ISOs for {arch} at {iso_page_url}")
            else:
                msg = f"No matching ISOs found for {arch} at {iso_page_url} (filter: {filter_name_key or config.get('name_key')})"
                print(msg)

        final_error_message = ""
        if not isos:
            if error_msg_accumulator:
                final_error_message = (
                    f"No ISOs found for {distro_name_for_log} {version}. Errors: "
                    + "; ".join(list(set(error_msg_accumulator)))
                )
            else:
                final_error_message = f"No ISOs found for {distro_name_for_log} {version} matching criteria."

        self.on_isos_fetched(version, isos, final_error_message)

    def _fetch_fedora_main_isos(self, config, version):
        base_url = config["base_url"]
        path_segment = config["path_segment"]
        iso_page_url_template = f"{base_url}{{version}}/{path_segment}/{{arch}}/iso/"
        self._fetch_fedora_isos_common(
            iso_page_url_template,
            config,
            version,
            filter_name_key=config.get("name_key"),
        )

    def _fetch_fedora_secondary_isos(self, config, version):
        base_url = config["base_url"]
        category = config["category"]
        iso_page_url_template = f"{base_url}{{version}}/{category}/{{arch}}/iso/"
        self._fetch_fedora_isos_common(
            iso_page_url_template,
            config,
            version,
            filter_name_key=config.get("name_key"),
        )

    def on_isos_fetched(self, version, isos, error):
        if self._current_distro_isos is None:
            self._current_distro_isos = {}
        self._current_distro_isos[version] = isos

        self.iso_type_combo.clear()
        selected_distro_name = self.distro_combo.currentText()

        self.download_button.setEnabled(False)

        if error and not isos:
            print(f"Failed to fetch ISOs for {selected_distro_name} {version}: {error}")
            self.iso_type_combo.addItem(f"Error fetching ISOs")
            self.iso_type_combo.setEnabled(False)
        else:
            available_iso_types = sorted(list(isos.keys()))
            if available_iso_types:
                self.iso_type_combo.addItems(available_iso_types)
                self.iso_type_combo.setEnabled(True)
                if available_iso_types:
                    self.iso_type_combo.setCurrentIndex(0)
                    self.download_button.setEnabled(True)
                    return
            else:
                self.iso_type_combo.addItem(f"No ISOs found")
                self.iso_type_combo.setEnabled(False)
                if not error:
                    print(
                        f"No standard ISOs found for {selected_distro_name} {version}."
                    )

        self._update_download_location_text()

    def update_progress_display(self, percent, speed_MBps, time_left_s, time_spent_s):
        self.progress_bar.setValue(percent)

        speed_str = f"{speed_MBps:.1f} MB/s" if speed_MBps > 0.001 else "--.- MB/s"
        time_left_str = format_time_display(time_left_s)
        time_spent_str = format_time_display(time_spent_s)

        self.progress_info_label.setText(
            f"{speed_str}  {time_left_str} left  {time_spent_str} spent"
        )

    def start_download(self):
        distro_name = self.distro_combo.currentText()
        version = self.version_combo.currentText()
        iso_type_selected = self.iso_type_combo.currentText()

        if not (
            self.iso_type_combo.isEnabled()
            and iso_type_selected
            and not any(
                indicator in iso_type_selected.lower()
                for indicator in ["n/a", "error", "no isos", "loading"]
            )
        ):
            print(f"No valid ISO type selected for {distro_name} {version}.")
            return

        url = None
        if (
            self._current_distro_isos
            and isinstance(self._current_distro_isos, dict)
            and version in self._current_distro_isos
        ):
            url = self._current_distro_isos[version].get(iso_type_selected)

        dest = self.location_edit.text().strip()
        if not url:
            print(f"URL not found for {distro_name} {version} - {iso_type_selected}.")
            return
        if not dest:
            print("Select download location.")
            return

        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except OSError as e:
                print(f"Cannot create directory {dest_dir}: {e}")
                return

        self.download_button.setEnabled(False)
        self.distro_combo.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.iso_type_combo.setEnabled(False)
        self.browse_button.setEnabled(False)

        self.progress_bar.setValue(0)
        self.progress_info_label.setText("--.- MB/s  --:--:-- left  --:--:-- spent")
        print(f"Downloading {distro_name} {version} ({iso_type_selected})...")
        print(f"URL: {url}")
        print(f"Destination: {dest}")

        self.worker = IsoDownloadWorker(url, dest)
        self.worker.progress.connect(self.update_progress_display)
        self.worker.status.connect(
            lambda msg: print(f"Worker Status: {msg}")
        )  # Optional: print worker status to console
        self.worker.finished.connect(self.on_download_finished)
        self.worker.start()

    def on_download_finished(self, success, msg):
        if success:
            print(f"Download finished: {msg}")
        else:
            print(f"Error/Cancelled: {msg}")
            self.progress_bar.setValue(0)
            self.progress_info_label.setText("--.- MB/s  --:--:-- left  --:--:-- spent")

        self.download_button.setEnabled(True)
        self.distro_combo.setEnabled(True)
        self.version_combo.setEnabled(True)
        self.iso_type_combo.setEnabled(True)
        self.browse_button.setEnabled(True)

        if (
            self.version_combo.count() == 0
            or "Error" in self.version_combo.currentText()
            or "No versions" in self.version_combo.currentText()
        ):
            self.version_combo.setEnabled(False)
        if (
            self.iso_type_combo.count() == 0
            or "Error" in self.iso_type_combo.currentText()
            or "No ISOs" in self.iso_type_combo.currentText()
            or "N/A" in self.iso_type_combo.currentText()
        ):
            self.iso_type_combo.setEnabled(False)
            self.download_button.setEnabled(False)

        self.worker = None

    def browse_location(self):
        current_path_suggestion = self.location_edit.text()
        current_dir_suggestion = os.path.dirname(current_path_suggestion)
        if not os.path.isdir(current_dir_suggestion):
            current_dir_suggestion = self.default_download_dir
            current_path_suggestion = os.path.join(
                current_dir_suggestion, os.path.basename(current_path_suggestion)
            )

        path, _ = QFileDialog.getSaveFileName(
            self, "Save ISO As", current_path_suggestion, "ISO Files (*.iso)"
        )
        if path:
            if not path.lower().endswith(".iso"):
                path += ".iso"
            self.location_edit.setText(path)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            print("Attempting to stop active download...")
            self.worker.stop()
            if not self.worker.wait(3000):
                print("Download worker did not terminate gracefully on close. Forcing.")
                self.worker.terminate()
                self.worker.wait()
            else:
                print("Download worker stopped.")
        event.accept()
