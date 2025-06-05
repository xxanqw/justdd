import sys
import os


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from styles import get_etcher_style
from widgets.logs_window import LogsWindow
from widgets.iso_downloader_widget import IsoDownloaderWidget
from widgets.about_widget import AboutWidget
import subprocess
import tempfile
import re


class ISODetector:
    @staticmethod
    def detect_iso_type(iso_path):
        # Detect if ISO is Linux or Windows based on file contents and structure
        try:
            import subprocess

            try:
                result = subprocess.run(
                    ["file", iso_path], capture_output=True, text=True, timeout=5
                )
                file_output = result.stdout.lower()
            except:
                file_output = ""

            details = {
                "name": "Unknown",
                "version": "Unknown",
                "architecture": "Unknown",
                "size": ISODetector._get_file_size(iso_path),
            }

            filename = os.path.basename(iso_path).lower()

            windows_patterns = [
                "windows",
                "win10",
                "win11",
                "win7",
                "win8",
                "server",
                "msdn",
                "microsoft",
                "office",
            ]

            linux_patterns = [
                "ubuntu",
                "debian",
                "fedora",
                "centos",
                "rhel",
                "opensuse",
                "mint",
                "arch",
                "manjaro",
                "kali",
                "parrot",
                "elementary",
                "zorin",
                "pop",
                "endeavour",
                "garuda",
                "solus",
                "void",
            ]

            for pattern in windows_patterns:
                if pattern in filename:
                    details["name"] = ISODetector._extract_windows_info(filename)
                    return ("windows", details)

            for pattern in linux_patterns:
                if pattern in filename:
                    details["name"] = ISODetector._extract_linux_info(filename)
                    return ("linux", details)

            iso_type, iso_details = ISODetector._examine_iso_contents(iso_path)
            if iso_type != "unknown":
                details.update(iso_details)
                return (iso_type, details)

            if "boot" in file_output:
                if "microsoft" in file_output or "windows" in file_output:
                    details["name"] = "Windows (detected)"
                    return ("windows", details)
                else:
                    details["name"] = "Linux (detected)"
                    return ("linux", details)

            return ("unknown", details)

        except Exception as e:
            return (
                "unknown",
                {
                    "name": "Detection failed",
                    "error": str(e),
                    "size": ISODetector._get_file_size(iso_path),
                },
            )

    @staticmethod
    def _get_file_size(file_path):
        # Get human readable file size
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ["B", "KB", "MB", "GB"]:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        except:
            return "Unknown"

    @staticmethod
    def _extract_windows_info(filename):
        # Extract Windows version info from filename
        if "win11" in filename or "windows11" in filename:
            return "Windows 11"
        elif "win10" in filename or "windows10" in filename:
            return "Windows 10"
        elif "win8" in filename or "windows8" in filename:
            return "Windows 8"
        elif "win7" in filename or "windows7" in filename:
            return "Windows 7"
        elif "server" in filename:
            return "Windows Server"
        else:
            return "Windows"

    @staticmethod
    def _extract_linux_info(filename):
        # Extract Linux distribution info from filename
        distros = {
            "ubuntu": "Ubuntu",
            "debian": "Debian",
            "fedora": "Fedora",
            "centos": "CentOS",
            "mint": "Linux Mint",
            "arch": "Arch Linux",
            "manjaro": "Manjaro",
            "kali": "Kali Linux",
            "opensuse": "openSUSE",
            "elementary": "elementary OS",
            "zorin": "Zorin OS",
            "pop": "Pop!_OS",
        }

        for key, name in distros.items():
            if key in filename:
                return name

        return "Linux"

    @staticmethod
    def _examine_iso_contents(iso_path):
        # Examine ISO contents using isoinfo if available
        try:
            result = subprocess.run(
                ["isoinfo", "-d", "-i", iso_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.lower()

                if "microsoft" in output or "windows" in output:
                    return ("windows", {"name": "Windows (ISO analysis)"})

                if any(
                    term in output for term in ["linux", "ubuntu", "debian", "fedora"]
                ):
                    return ("linux", {"name": "Linux (ISO analysis)"})

            result = subprocess.run(
                ["isoinfo", "-l", "-i", iso_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                file_list = result.stdout.lower()

                windows_files = [
                    "setup.exe",
                    "autorun.inf",
                    "bootmgr",
                    "sources/install.wim",
                ]
                if any(wfile in file_list for wfile in windows_files):
                    return ("windows", {"name": "Windows (file analysis)"})

                linux_files = ["vmlinuz", "initrd", "casper/", "live/", "isolinux/"]
                if any(lfile in file_list for lfile in linux_files):
                    return ("linux", {"name": "Linux (file analysis)"})

        except:
            pass

        return ("unknown", {})


class FlashWorker(QThread):
    progress = Signal(int)
    status_update = Signal(str)
    log_message = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, iso_path, target_drive, mode="linux"):
        super().__init__()
        self.iso_path = iso_path
        self.target_drive = target_drive
        self.mode = mode
        self._process = None

    def run(self):
        try:
            if self.mode == "windows":
                self._flash_windows()
            else:
                self._flash_linux()
        except Exception as e:
            if not self.isInterruptionRequested():
                self.log_message.emit(f"Error: {str(e)}")
                self.finished.emit(False, f"Flash failed: {str(e)}")
        finally:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except:
                    pass
                self._process = None

    def _flash_linux(self):
        self.status_update.emit("Preparing to flash...")
        self.log_message.emit(f"Starting Linux flash process")
        self.log_message.emit(f"ISO: {self.iso_path}")
        self.log_message.emit(f"Target: {self.target_drive}")

        # Get ISO file size for progress calculation
        try:
            iso_size = os.path.getsize(self.iso_path)
            self.log_message.emit(
                f"ISO size: {iso_size} bytes ({iso_size / (1024**3):.2f} GB)"
            )
        except Exception as e:
            self.log_message.emit(f"Could not get ISO size: {e}")
            iso_size = 0

        self.status_update.emit("Checking device status...")
        self.progress.emit(5)
        self.msleep(500)

        try:
            result = subprocess.run(
                ["fuser", "-m", self.target_drive],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                self.log_message.emit(f"Device busy - PIDs: {result.stdout.strip()}")
                self.finished.emit(False, "Device is busy or mounted")
                return
        except subprocess.TimeoutExpired:
            self.log_message.emit("fuser check timed out, proceeding...")
        except FileNotFoundError:
            self.log_message.emit("fuser command not found, proceeding...")
        except Exception as e:
            self.log_message.emit(f"fuser check failed: {e}, proceeding...")

        self.progress.emit(10)
        self.status_update.emit("Starting dd operation...")

        cmd = [
            "pkexec",
            "dd",
            f"if={self.iso_path}",
            f"of={self.target_drive}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
        ]

        self.log_message.emit(f"Command: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            progress_value = 10
            while True:
                if self.isInterruptionRequested():
                    process.terminate()
                    process.wait()
                    self.log_message.emit("Flash operation cancelled")
                    return

                output = process.stdout.readline()
                if output:
                    self.log_message.emit(output.strip())

                    # Parse dd progress output to calculate percentage
                    if "bytes" in output.lower() and iso_size > 0:
                        try:
                            # Extract bytes copied from dd output
                            # Format is usually like: "1073741824 bytes (1.1 GB, 1.0 GiB) copied"
                            match = re.search(r"(\d+)\s+bytes", output)
                            if match:
                                bytes_copied = int(match.group(1))
                                # Calculate percentage between 10% and 90%
                                percentage = (bytes_copied / iso_size) * 80 + 10
                                progress_value = min(int(percentage), 90)
                                self.progress.emit(progress_value)

                                # Update status with transfer rate and progress
                                if "copied" in output.lower():
                                    self.status_update.emit(
                                        f"Copying... {bytes_copied / (1024**3):.2f} GB / {iso_size / (1024**3):.2f} GB"
                                    )
                        except (ValueError, AttributeError):
                            # Fallback to incremental progress if parsing fails
                            if "copied" in output.lower():
                                progress_value = min(progress_value + 2, 90)
                                self.progress.emit(progress_value)
                    elif "copied" in output.lower():
                        # Fallback progress update
                        progress_value = min(progress_value + 2, 90)
                        self.progress.emit(progress_value)

                elif process.poll() is not None:
                    break

                self.msleep(100)

            return_code = process.wait()

            if return_code == 0:
                self.progress.emit(95)
                self.status_update.emit("Syncing filesystem...")
                self.log_message.emit("Running final sync...")

                try:
                    subprocess.run(["sync"], timeout=30, check=True)
                    self.msleep(1000)
                except Exception as e:
                    self.log_message.emit(f"Sync warning: {e}")

                self.progress.emit(100)
                self.status_update.emit("Flash completed successfully!")
                self.finished.emit(True, "Flash completed successfully!")
            else:
                self.finished.emit(
                    False, f"dd command failed with exit code {return_code}"
                )

        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Flash operation timed out")
        except Exception as e:
            self.finished.emit(False, f"Flash failed: {str(e)}")

    def _flash_windows(self):
        if self.isInterruptionRequested():
            return

        self.status_update.emit("Preparing Windows USB...")
        self.log_message.emit(f"Starting Windows USB preparation")
        self.log_message.emit(f"ISO: {self.iso_path}")
        self.log_message.emit(f"Target: {self.target_drive}")

        self.status_update.emit("Checking device status...")
        self.progress.emit(5)

        try:
            result = subprocess.run(
                ["fuser", "-m", self.target_drive],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                self.log_message.emit(f"Device busy - PIDs: {result.stdout.strip()}")
                self.finished.emit(False, "Device is busy or mounted")
                return
        except:
            pass

        drive = self.target_drive
        p1, p2 = f"{drive}1", f"{drive}2"
        iso_mount, vfat_mount, ntfs_mount = (
            "/mnt/justdd_iso",
            "/mnt/justdd_vfat",
            "/mnt/justdd_ntfs",
        )

        steps = [
            ("Wiping filesystem signatures", 10, ["wipefs", "-a", drive]),
            (
                "Creating GPT partition table",
                15,
                ["parted", "--script", drive, "mklabel", "gpt"],
            ),
            (
                "Creating BOOT partition",
                20,
                ["parted", "--script", drive, "mkpart", "BOOT", "fat32", "0%", "1GiB"],
            ),
            (
                "Creating INSTALL partition",
                25,
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
            ("Waiting for partition recognition", 28, ["partprobe", drive]),
            ("Waiting for devices", 30, ["sleep", "2"]),
            ("Formatting BOOT partition", 35, ["mkfs.vfat", "-n", "BOOT", p1]),
            (
                "Formatting INSTALL partition",
                40,
                ["mkfs.ntfs", "--quick", "-L", "INSTALL", p2],
            ),
            (
                "Creating mount directories",
                45,
                ["mkdir", "-p", iso_mount, vfat_mount, ntfs_mount],
            ),
            ("Mounting ISO", 50, ["mount", "-o", "loop", self.iso_path, iso_mount]),
            ("Mounting BOOT partition", 55, ["mount", p1, vfat_mount]),
            (
                "Copying boot files",
                60,
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
            (
                "Creating sources directory",
                65,
                ["mkdir", "-p", f"{vfat_mount}/sources"],
            ),
            (
                "Copying boot.wim",
                70,
                ["cp", f"{iso_mount}/sources/boot.wim", f"{vfat_mount}/sources/"],
            ),
            ("Mounting INSTALL partition", 75, ["mount", p2, ntfs_mount]),
            (
                "Copying Windows files (this takes a long time)",
                80,
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
            ("Unmounting INSTALL partition", 90, ["umount", ntfs_mount]),
            ("Unmounting BOOT partition", 95, ["umount", vfat_mount]),
            ("Unmounting ISO", 97, ["umount", iso_mount]),
            ("Syncing filesystem", 99, ["sync"]),
            (
                "Cleaning up mount directories",
                100,
                ["rmdir", iso_mount, vfat_mount, ntfs_mount],
            ),
        ]

        try:
            script_lines = [
                "#!/bin/bash",
                "set -e",
                "",
                "# Function to check for interruption",
                "check_interruption() {",
                '    if [ -f "/tmp/justdd_cancel_$$" ]; then',
                '        echo "Operation cancelled by user"',
                "        exit 130",
                "    fi",
                "}",
                "",
                "# Function to safely unmount",
                "safe_unmount() {",
                '    local mount_point="$1"',
                '    if mountpoint -q "$mount_point" 2>/dev/null; then',
                '        echo "Unmounting $mount_point"',
                '        umount "$mount_point" 2>/dev/null || umount -l "$mount_point" 2>/dev/null || true',
                "    fi",
                "}",
                "",
                "# Function to unmount device partitions",
                "unmount_device_partitions() {",
                '    local device="$1"',
                '    echo "Unmounting all partitions on $device"',
                "    # Get all mounted partitions for this device",
                "    mount | grep \"^$device\" | awk '{print $1}' | while read partition; do",
                '        if [ -n "$partition" ]; then',
                '            echo "Unmounting partition: $partition"',
                '            umount "$partition" 2>/dev/null || umount -l "$partition" 2>/dev/null || true',
                "        fi",
                "    done",
                "    # Also try to unmount by device pattern",
                f"    for part in {drive}*; do",
                f'        if [ "$part" != "{drive}" ] && mountpoint -q "$part" 2>/dev/null; then',
                '            echo "Force unmounting: $part"',
                '            umount "$part" 2>/dev/null || umount -l "$part" 2>/dev/null || true',
                "        fi",
                "    done",
                "    sync",
                "    sleep 1",
                "}",
                "",
                "# Function to kill processes using device",
                "kill_device_processes() {",
                '    local device="$1"',
                '    echo "Checking for processes using $device"',
                "    # Try fuser first",
                "    if command -v fuser >/dev/null 2>&1; then",
                f'        fuser -km "{drive}" 2>/dev/null || true',
                f'        fuser -km "{drive}"* 2>/dev/null || true',
                "    fi",
                "    # Try lsof as backup",
                "    if command -v lsof >/dev/null 2>&1; then",
                f'        lsof "{drive}"* 2>/dev/null | awk "NR>1 {{print \\$2}}" | xargs -r kill -9 2>/dev/null || true',
                "    fi",
                "    sleep 2",
                "}",
                "",
                "# Function to retry wipefs",
                "retry_wipefs() {",
                '    local device="$1"',
                "    local max_attempts=3",
                "    local attempt=1",
                "    ",
                "    while [ $attempt -le $max_attempts ]; do",
                '        echo "Wipefs attempt $attempt/$max_attempts"',
                "        ",
                "        # First unmount all partitions",
                '        unmount_device_partitions "$device"',
                "        ",
                "        # Kill processes using the device",
                '        kill_device_processes "$device"',
                "        ",
                "        # Try wipefs",
                '        if wipefs -a "$device" 2>/dev/null; then',
                '            echo "Wipefs successful"',
                "            return 0",
                "        else",
                '            echo "Wipefs failed on attempt $attempt"',
                "            if [ $attempt -lt $max_attempts ]; then",
                '                echo "Retrying in 2 seconds..."',
                "                sleep 2",
                "            fi",
                "            attempt=$((attempt + 1))",
                "        fi",
                "    done",
                "    ",
                '    echo "All wipefs attempts failed, trying force method..."',
                '    unmount_device_partitions "$device"',
                '    kill_device_processes "$device"',
                '    dd if=/dev/zero of="$device" bs=1M count=10 2>/dev/null || true',
                "    sync",
                "    sleep 1",
                "}",
                "",
                "# Cleanup function",
                "cleanup() {",
                '    echo "Performing cleanup..."',
                "    for mnt in /mnt/justdd_iso /mnt/justdd_vfat /mnt/justdd_ntfs; do",
                '        safe_unmount "$mnt"',
                '        rm -rf "$mnt" 2>/dev/null || true',
                "    done",
                "}",
                "",
                "# Set trap for cleanup on exit",
                "trap cleanup EXIT",
                "",
                "# Initial cleanup",
                "cleanup",
                "",
                f"# Initial device preparation for {drive}",
                f'echo "Preparing device {drive}"',
                "",
                "# Step 1: Unmount all partitions on the device",
                f'unmount_device_partitions "{drive}"',
                "",
                "# Step 2: Kill any remaining processes",
                f'kill_device_processes "{drive}"',
                "",
                "# Step 3: Wait for everything to settle",
                "sleep 3",
                "",
                "# Now execute the actual Windows USB creation steps",
                "",
            ]

            for idx, (desc, progress_val, cmd) in enumerate(steps, 1):
                script_lines.append(f'echo "Step {idx}/{len(steps)}: {desc}"')
                script_lines.append("check_interruption")

                if cmd[0] == "wipefs":
                    script_lines.append(f'retry_wipefs "{drive}"')
                else:
                    script_lines.append(f'echo "Running: {" ".join(cmd)}"')
                    quoted_cmd = []
                    for arg in cmd:
                        if " " in arg or any(
                            char in arg for char in ["$", "`", '"', "'"]
                        ):
                            quoted_cmd.append(f'"{arg}"')
                        else:
                            quoted_cmd.append(arg)
                    script_lines.append(" ".join(quoted_cmd))

                script_lines.append("")

            script_lines.extend(
                [
                    'echo "Windows USB creation completed successfully!"',
                    'echo "The USB drive is ready for use."',
                ]
            )

            script_content = "\n".join(script_lines)

            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as tf:
                tf.write(script_content)
                script_path = tf.name

            try:
                os.chmod(script_path, 0o700)
                self.log_message.emit(
                    f"Created Windows USB preparation script: {script_path}"
                )

                cancel_file = f"/tmp/justdd_cancel_{os.getpid()}"

                self._process = subprocess.Popen(
                    ["pkexec", "bash", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                while True:
                    if self.isInterruptionRequested():
                        try:
                            with open(cancel_file, "w") as f:
                                f.write("cancel")
                        except:
                            pass

                        self._process.terminate()
                        self._process.wait(timeout=5)
                        self.log_message.emit("Windows USB preparation cancelled")
                        return

                    output = self._process.stdout.readline()
                    if output:
                        line = output.strip()
                        self.log_message.emit(line)

                        if line.startswith("Step "):
                            try:
                                step_info = line.split(": ", 1)
                                if len(step_info) > 1:
                                    step_num = int(
                                        step_info[0].split()[1].split("/")[0]
                                    )
                                    if step_num <= len(steps):
                                        progress_val = steps[step_num - 1][1]
                                        self.progress.emit(progress_val)
                                        self.status_update.emit(step_info[1])
                            except (ValueError, IndexError):
                                pass

                    elif self._process.poll() is not None:
                        break

                    self.msleep(100)

                try:
                    os.unlink(cancel_file)
                except:
                    pass

                return_code = self._process.wait()

                if return_code == 0:
                    self.progress.emit(100)
                    self.status_update.emit("Windows USB preparation completed!")
                    self.finished.emit(True, "Windows USB created successfully!")
                elif return_code == 130:
                    self.log_message.emit("Operation cancelled by user")
                    return
                else:
                    self.finished.emit(
                        False,
                        f"Windows USB preparation failed with exit code {return_code}",
                    )

            except Exception as e:
                if not self.isInterruptionRequested():
                    self.log_message.emit(
                        f"Error executing Windows USB script: {str(e)}"
                    )
                    self.finished.emit(
                        False, f"Windows USB preparation failed: {str(e)}"
                    )
            finally:
                try:
                    os.unlink(script_path)
                except:
                    pass
                self._process = None

        except Exception as e:
            if not self.isInterruptionRequested():
                self.log_message.emit(f"Windows USB preparation failed: {str(e)}")
                self.finished.emit(False, f"Windows USB preparation failed: {str(e)}")


class CompactStepIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 1
        self.total_steps = 3
        self.setFixedHeight(25)
        self.setFixedWidth(120)

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

        icon_label = QLabel("📁")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            "font-size: 48pt; border: none; background: transparent;"
        )

        title_label = QLabel("Select Image")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #f9e79f;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(icon_label)
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
        file_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """
        )
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(0)

        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_path_label.setStyleSheet(
            "color: #888888; font-style: italic; font-size: 11pt;"
        )
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.iso_type_label = QLabel("")
        self.iso_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iso_type_label.setStyleSheet(
            "color: #666666; font-size: 9pt; margin-top: 5px;"
        )
        self.iso_type_label.setWordWrap(True)
        self.iso_type_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.iso_type_label.hide()

        file_layout.addWidget(self.file_path_label, 3)
        file_layout.addWidget(self.iso_type_label, 1)

        file_layout.addStretch(1)

        browse_button = QPushButton("Browse for Image")
        browse_button.setProperty("class", "primary")
        browse_button.clicked.connect(self.browse_file)
        browse_button.setMinimumHeight(32)
        browse_button.setMaximumHeight(32)

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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ISO File", "", "ISO Files (*.iso);;All Files (*)"
        )
        if file_path:
            self.iso_path = file_path
            filename = os.path.basename(file_path)

            self.iso_type, self.iso_details = ISODetector.detect_iso_type(file_path)

            if len(filename) > 35:
                filename = filename[:32] + "..."
            self.file_path_label.setText(filename)
            self.file_path_label.setStyleSheet(
                "color: #ffffff; font-style: normal; font-size: 11pt; font-weight: bold;"
            )

            self._update_iso_type_display()

            self.selection_changed.emit()

    def _update_iso_type_display(self):
        # Update the ISO type display
        if self.iso_type == "unknown":
            self.iso_type_label.setText("⚠️ Unknown ISO type")
            self.iso_type_label.setStyleSheet(
                "color: #f39c12; font-size: 9pt; margin-top: 5px;"
            )
        elif self.iso_type == "linux":
            distro_name = self.iso_details.get("name", "Linux")
            size = self.iso_details.get("size", "")
            self.iso_type_label.setText(f"🐧 {distro_name} • {size}")
            self.iso_type_label.setStyleSheet(
                "color: #f9e79f; font-size: 9pt; margin-top: 5px;"
            )
        elif self.iso_type == "windows":
            os_name = self.iso_details.get("name", "Windows")
            size = self.iso_details.get("size", "")
            self.iso_type_label.setText(f"🪟 {os_name} • {size}")
            self.iso_type_label.setStyleSheet(
                "color: #3498db; font-size: 9pt; margin-top: 5px;"
            )

        self.iso_type_label.show()

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

        icon_label = QLabel("💾")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            "font-size: 48pt; border: none; background: transparent;"
        )

        title_label = QLabel("Select Drive")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #f9e79f;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(icon_label)
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
        drive_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """
        )
        drive_layout = QVBoxLayout(drive_frame)
        drive_layout.setContentsMargins(15, 15, 15, 15)
        drive_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_label = QLabel("Available USB Drives:")
        header_label.setStyleSheet(
            "font-size: 12pt; font-weight: bold; color: #ffffff;"
        )

        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setFixedHeight(32)
        refresh_button.clicked.connect(self.refresh_drives)
        refresh_button.setToolTip("Refresh drive list")

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)

        self.drive_list = QListWidget()
        self.drive_list.setFixedHeight(200)
        self.drive_list.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 5px;
                font-size: 11pt;
            }
            QListWidget::item {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 12px;
                margin: 2px;
                color: #ffffff;
                min-height: 50px;
            }
            QListWidget::item:hover {
                background-color: #404040;
                border-color: #505050;
            }
            QListWidget::item:selected {
                background-color: #f9e79f;
                color: #2c3e50;
                border-color: #f9e79f;
                font-weight: bold;
            }
        """
        )
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

        icon_label = QLabel("⚡")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            "font-size: 48pt; border: none; background: transparent;"
        )

        title_label = QLabel("Ready to Flash")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #f9e79f;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(icon_label)
        left_layout.addWidget(title_label)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_widget.setFixedWidth(450)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 40, 0, 40)
        right_layout.setSpacing(20)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.content_container = QWidget()
        self.content_container.setFixedSize(400, 280)
        content_widget_layout = QVBoxLayout(self.content_container)
        content_widget_layout.setContentsMargins(0, 0, 0, 0)
        content_widget_layout.setSpacing(15)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """
        )
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        summary_layout.setSpacing(10)

        summary_title = QLabel("Flash Summary")
        summary_title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #ffffff; margin-bottom: 5px; background-color: transparent; border: none;"
        )

        image_layout = QVBoxLayout()
        image_layout.setSpacing(5)
        image_label_title = QLabel("Image:")
        image_label_title.setStyleSheet(
            "font-size: 11pt; color: #aaaaaa; background-color: transparent; border: none;"
        )
        self.image_label = QLabel("No image selected")
        self.image_label.setStyleSheet(
            "font-weight: bold; color: #f9e79f; font-size: 11pt; background-color: transparent; border: none;"
        )
        image_layout.addWidget(image_label_title)
        image_layout.addWidget(self.image_label)

        drive_layout = QVBoxLayout()
        drive_layout.setSpacing(5)
        drive_label_title = QLabel("Drive:")
        drive_label_title.setStyleSheet(
            "font-size: 11pt; color: #aaaaaa; background-color: transparent; border: none;"
        )
        self.drive_label = QLabel("No drive selected")
        self.drive_label.setStyleSheet(
            "font-weight: bold; color: #f9e79f; font-size: 11pt; background-color: transparent; border: none;"
        )
        drive_layout.addWidget(drive_label_title)
        drive_layout.addWidget(self.drive_label)

        summary_layout.addWidget(summary_title)
        summary_layout.addLayout(image_layout)
        summary_layout.addLayout(drive_layout)

        warning_frame = QFrame()
        warning_frame.setStyleSheet(
            """
            QFrame {
                background-color: #3d2a2a;
                border: 1px solid #e74c3c;
                border-radius: 8px;
            }
        """
        )
        warning_layout = QVBoxLayout(warning_frame)
        warning_layout.setContentsMargins(15, 10, 15, 10)
        warning_layout.setSpacing(8)

        warning_title = QLabel("⚠️ Warning")
        warning_title.setStyleSheet(
            "color: #e74c3c; font-weight: bold; font-size: 13pt; background-color: transparent; border: none;"
        )

        warning_text = QLabel(
            "This will completely erase all data on the selected drive. This action cannot be undone."
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet(
            "color: #e74c3c; font-size: 10pt; line-height: 1.3; background-color: transparent; border: none;"
        )

        warning_layout.addWidget(warning_title)
        warning_layout.addWidget(warning_text)

        content_widget_layout.addWidget(summary_frame)
        content_widget_layout.addWidget(warning_frame)

        self.progress_container = QWidget()
        self.progress_container.setFixedSize(400, 280)
        progress_main_layout = QVBoxLayout(self.progress_container)
        progress_main_layout.setContentsMargins(0, 0, 0, 0)
        progress_main_layout.setSpacing(0)
        progress_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress_info_frame = QFrame()
        progress_info_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """
        )
        progress_info_layout = QVBoxLayout(progress_info_frame)
        progress_info_layout.setContentsMargins(30, 40, 30, 40)
        progress_info_layout.setSpacing(20)
        progress_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        operation_title = QLabel("Flash Operation in Progress")
        operation_title.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #ffffff; background-color: transparent; border: none;"
        )
        operation_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Preparing to flash...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 12pt; color: #f9e79f; font-weight: bold; background-color: transparent; border: none;"
        )
        self.status_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 8px;
                text-align: center;
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: bold;
                font-size: 11pt;
            }
            QProgressBar::chunk {
                background-color: #f9e79f;
                border-radius: 6px;
            }
        """
        )

        progress_info_layout.addWidget(operation_title)
        progress_info_layout.addWidget(self.status_label)
        progress_info_layout.addWidget(self.progress_bar)

        progress_main_layout.addWidget(progress_info_frame)

        self.progress_container.hide()

        right_layout.addWidget(self.content_container)
        right_layout.addWidget(self.progress_container)

        container_layout.addWidget(left_widget)
        container_layout.addWidget(right_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 0, 50, 50)
        main_layout.addStretch(1)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1)

    def set_flash_info(
        self, iso_path, drive_path, drive_display, iso_type="unknown", iso_details=None
    ):
        self.iso_path = iso_path
        self.drive_path = drive_path
        self.drive_display = drive_display
        self.iso_type = iso_type
        self.iso_details = iso_details or {}

        self.flashing = False
        self.content_container.show()
        self.progress_container.hide()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to flash...")
        self.status_label.setStyleSheet(
            "font-size: 12pt; color: #f9e79f; font-weight: bold; margin: 10px 0; background-color: transparent; border: none;"
        )

        filename = os.path.basename(iso_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."

        if self.iso_type == "linux":
            type_indicator = "🐧"
        elif self.iso_type == "windows":
            type_indicator = "🪟"
        else:
            type_indicator = "💿"

        self.image_label.setText(f"{type_indicator} {filename}")

        drive_display_short = drive_display
        if len(drive_display) > 35:
            drive_display_short = drive_display[:32] + "..."
        self.drive_label.setText(drive_display_short)

    def start_flash(self):
        self.flashing = True

        self.content_container.hide()
        self.progress_container.show()

        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing to flash...")
        self.status_label.setStyleSheet(
            "font-size: 12pt; color: #f9e79f; font-weight: bold; margin: 10px 0; background-color: transparent; border: none;"
        )

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def flash_completed(self, success, message):
        self.flashing = False

        if success:
            self.status_label.setText("Flash completed successfully!")
            self.status_label.setStyleSheet(
                "font-size: 12pt; color: #f9e79f; font-weight: bold; margin: 10px 0; background-color: transparent; border: none;"
            )
        else:
            self.status_label.setText(f"Flash failed: {message}")
            self.status_label.setStyleSheet(
                "font-size: 12pt; color: #e74c3c; font-weight: bold; margin: 10px 0; background-color: transparent; border: none;"
            )
            QMessageBox.critical(self, "Error", f"Flash failed: {message}")

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

        icon_label = QLabel("🎉")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            "font-size: 60pt; border: none; background: transparent;"
        )

        title_label = QLabel("Flash Completed Successfully!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #f9e79f;")

        message_label = QLabel("Your image has been successfully written to the drive.")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("font-size: 12pt; color: #ffffff;")

        self.flash_another_button = QPushButton("Flash Another Image")
        self.flash_another_button.setProperty("class", "primary")
        self.flash_another_button.setMinimumHeight(40)
        self.flash_another_button.setFixedWidth(250)
        self.flash_another_button.clicked.connect(self.flash_another_requested.emit)
        self.flash_another_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f9e79f; color: #2c3e50; border: 1px solid #f9e79f;
                border-radius: 6px; font-weight: bold; font-size: 11pt; padding: 10px;
            }
            QPushButton:hover { background-color: #f7dc6f; border-color: #f7dc6f; }
            QPushButton:pressed { background-color: #f4d03f; }
        """
        )

        container_layout.addWidget(icon_label)
        container_layout.addWidget(title_label)
        container_layout.addWidget(message_label)
        container_layout.addSpacing(20)
        container_layout.addWidget(
            self.flash_another_button, alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(container)


class EtcherWizardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JustDD - USB Image Writer")
        self.setMinimumSize(800, 450)
        self.resize(900, 500)

        self.iso_path = ""
        self.drive_path = ""
        self.drive_display = ""
        self.flash_worker = None
        self.current_page = 0
        self._shutdown_in_progress = False

        self.logs_window = LogsWindow()

        self.iso_downloader_widget = IsoDownloaderWidget()

        self.about_widget = AboutWidget()

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
                QMessageBox.StandardButton.No,
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
            except:
                pass

        self._cleanup_all_resources()

        event.accept()

    def _force_cleanup_worker(self):
        # Force cleanup of worker thread
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

            except Exception as e:
                self.flash_worker = None

    def _cleanup_all_resources(self):
        # Clean up all application resources
        try:
            if self.flash_worker:
                self._force_cleanup_worker()

            QApplication.processEvents()

        except Exception:
            pass

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
            }
        """
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        header_layout.setSpacing(15)

        title_container = QWidget()
        title_container.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        icon_label = QLabel()
        icon_path = resource_path("images/icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_title = QLabel("JustDD")
        app_title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #f9e79f;")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(app_title)

        indicator_container = QWidget()
        indicator_container.setStyleSheet("background-color: transparent;")
        indicator_layout = QVBoxLayout(indicator_container)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.step_indicator = CompactStepIndicator()
        self.step_indicator.setStyleSheet("background-color: transparent;")
        indicator_layout.addWidget(self.step_indicator)

        header_layout.addWidget(title_container)
        header_layout.addStretch()
        header_layout.addWidget(indicator_container)

        self.stacked_widget = QStackedWidget()

        self.iso_page = ISOSelectionPage()
        self.drive_page = DriveSelectionPage()
        self.flash_page = FlashPage()
        self.success_page = SuccessPage()

        self.iso_page.selection_changed.connect(self.update_navigation_buttons)
        self.drive_page.selection_changed.connect(self.update_navigation_buttons)
        self.success_page.flash_another_requested.connect(self.reset_to_start)

        self.stacked_widget.addWidget(self.iso_page)
        self.stacked_widget.addWidget(self.drive_page)
        self.stacked_widget.addWidget(self.flash_page)
        self.stacked_widget.addWidget(self.success_page)

        footer_frame = QFrame()
        footer_frame.setFixedHeight(60)
        footer_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d2d;
                border-top: 1px solid #404040;
            }
        """
        )
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(30, 10, 30, 10)
        footer_layout.setSpacing(15)

        left_buttons_layout = QHBoxLayout()

        logs_button = QPushButton("Show Logs")
        logs_button.setFixedSize(100, 35)
        logs_button.clicked.connect(self.show_logs)

        iso_downloader_button = QPushButton("ISO")
        iso_downloader_button.setFixedSize(120, 35)
        iso_downloader_button.clicked.connect(self.show_iso_downloader)

        about_button = QPushButton("About")
        about_button.setFixedSize(80, 35)
        about_button.clicked.connect(self.show_about)

        left_buttons_layout.addWidget(logs_button)
        left_buttons_layout.addWidget(iso_downloader_button)
        left_buttons_layout.addWidget(about_button)
        left_buttons_layout.addStretch()

        footer_layout.addLayout(left_buttons_layout)
        footer_layout.addStretch()

        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_container.setStyleSheet("background-color: #2d2d2d;")
        nav_layout.setSpacing(15)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setMinimumHeight(35)
        self.back_button.setFixedWidth(80)
        self.back_button.setStyleSheet(
            """
            QPushButton {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #505050;
            border-radius: 8px;
            font-weight: bold;
            }
            QPushButton:hover {
            background-color: #505050;
            border-color: #606060;
            }
            QPushButton:pressed {
            background-color: #353535;
            }
        """
        )

        self.continue_button = QPushButton("Continue")
        self.continue_button.setProperty("class", "primary")
        self.continue_button.setStyleSheet(
            """
            QPushButton {
            background-color: #f9e79f;
            color: #2c3e50;
            border: 1px solid #f9e79f;
            border-radius: 8px;
            font-weight: bold;
            }
            QPushButton:hover {
            background-color: #f7dc6f;
            border-color: #f7dc6f;
            }
            QPushButton:disabled {
            background-color: #404040;
            color: #888888;
            border-color: #404040;
            }
            QPushButton:pressed {
            background-color: #f4d03f;
            }
        """
        )
        self.continue_button.clicked.connect(self.go_forward)
        self.continue_button.setMinimumHeight(35)
        self.continue_button.setFixedWidth(100)

        self.flash_button = QPushButton("Flash!")
        self.flash_button.setProperty("class", "danger")
        self.flash_button.clicked.connect(self.start_flash)
        self.flash_button.setMinimumHeight(35)
        self.flash_button.setFixedWidth(100)
        self.flash_button.setStyleSheet(
            """
            QPushButton {
            background-color: #e74c3c;
            color: #ffffff;
            border: 1px solid #e74c3c;
            border-radius: 8px;
            font-weight: bold;
            }
            QPushButton:hover {
            background-color: #c0392b;
            border-color: #c0392b;
            }
            QPushButton:pressed {
            background-color: #a93226;
            }
        """
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_flash)
        self.cancel_button.setMinimumHeight(35)
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
            background-color: #e74c3c;
            color: #ffffff;
            border: 1px solid #e74c3c;
            border-radius: 8px;
            font-weight: bold;
            }
            QPushButton:hover {
            background-color: #c0392b;
            border-color: #c0392b;
            }
            QPushButton:pressed {
            background-color: #a93226;
            }
        """
        )
        self.cancel_button.setFixedWidth(80)

        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.cancel_button)
        nav_layout.addWidget(self.continue_button)
        nav_layout.addWidget(self.flash_button)

        footer_layout.addWidget(nav_container)

        layout.addWidget(header_frame)
        layout.addWidget(self.stacked_widget, 1)
        layout.addWidget(footer_frame)

    def update_navigation_buttons(self):
        page = self.current_page
        is_flashing = self.flash_page.is_flashing()

        self.back_button.hide()
        self.continue_button.hide()
        self.flash_button.hide()
        self.cancel_button.hide()

        if is_flashing:
            self.cancel_button.show()
        elif page == 0:
            self.continue_button.show()
            self.continue_button.setEnabled(self.iso_page.has_valid_selection())
        elif page == 1:
            self.back_button.show()
            self.continue_button.show()
            self.continue_button.setEnabled(self.drive_page.has_valid_selection())
        elif page == 2:
            self.back_button.show()
            self.flash_button.show()
        elif page == 3:
            pass

    def go_back(self):
        if self.current_page > 0 and self.current_page <= 2:
            self.current_page -= 1
            self.step_indicator.set_step(self.current_page + 1)
            self.stacked_widget.setCurrentIndex(self.current_page)
            self.update_navigation_buttons()

    def go_forward(self):
        if self.current_page == 0:
            iso_path = self.iso_page.get_selected_iso()
            if iso_path:
                self.iso_path = iso_path
                iso_type = self.iso_page.get_iso_type()
                iso_details = self.iso_page.get_iso_details()

                self.logs_window.append_log(f"Selected ISO: {iso_path}")
                self.logs_window.append_log(f"Detected type: {iso_type}")
                if iso_details.get("name"):
                    self.logs_window.append_log(f"OS: {iso_details['name']}")

                self.current_page = 1
                self.step_indicator.set_step(2)
                self.stacked_widget.setCurrentIndex(1)
                self.update_navigation_buttons()
        elif self.current_page == 1:
            drive_path, drive_display = self.drive_page.get_selected_drive()
            if drive_path:
                self.drive_path = drive_path
                self.drive_display = drive_display
                self.logs_window.append_log(f"Selected drive: {drive_path}")
                self.current_page = 2
                self.step_indicator.set_step(3)

                iso_type = self.iso_page.get_iso_type()
                iso_details = self.iso_page.get_iso_details()
                self.flash_page.set_flash_info(
                    self.iso_path,
                    self.drive_path,
                    self.drive_display,
                    iso_type,
                    iso_details,
                )

                self.stacked_widget.setCurrentIndex(2)
                self.update_navigation_buttons()

    def start_flash(self):
        reply = QMessageBox.warning(
            self,
            "Confirm Flash Operation",
            f"Are you absolutely sure you want to flash the image to {self.drive_path}?\n\n"
            f"This will DESTROY ALL DATA on the drive!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.flash_page.start_flash()
            self.update_navigation_buttons()

            iso_type = self.iso_page.get_iso_type()
            mode = "windows" if iso_type == "windows" else "linux"

            self.flash_worker = FlashWorker(self.iso_path, self.drive_path, mode)
            self.flash_worker.progress.connect(self.flash_page.update_progress)
            self.flash_worker.status_update.connect(self.flash_page.update_status)
            self.flash_worker.log_message.connect(self.logs_window.append_log)
            self.flash_worker.finished.connect(self.on_flash_finished)
            self.flash_worker.start()

    def cancel_flash(self):
        if self.flash_worker:
            reply = QMessageBox.warning(
                self,
                "Cancel Flash Operation",
                "⚠️ Are you sure you want to cancel the flash operation?\n\n"
                "Cancelling during the flash process may leave your USB drive in a corrupted "
                "or unusable state. You may need to reformat the drive to use it again.\n\n"
                "Do you want to continue with cancellation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
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
        self.flash_page.status_label.setStyleSheet(
            "font-size: 12pt; color: #f39c12; font-weight: bold; background-color: transparent; border: none;"
        )

    def log_message_safe(self, message):
        # Safely log a message, checking if logs_window still exists
        try:
            if self.logs_window and not self._shutdown_in_progress:
                self.logs_window.append_log(message)
        except:
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
                except:
                    pass

                self.flash_worker.deleteLater()
                self.flash_worker = None

            if success:
                self.current_page = 3
                self.stacked_widget.setCurrentWidget(self.success_page)
                self.step_indicator.set_step(self.step_indicator.total_steps + 1)

            self.update_navigation_buttons()

        except Exception as e:
            if not self._shutdown_in_progress:
                self.log_message_safe(f"Error in flash finish handler: {e}")

    def reset_to_start(self):
        self.current_page = 0
        self.iso_path = ""
        self.drive_path = ""
        self.drive_display = ""

        self.iso_page.iso_path = None
        self.iso_page.iso_type = "unknown"
        self.iso_page.iso_details = {}
        self.iso_page.file_path_label.setText("No file selected")
        self.iso_page.file_path_label.setStyleSheet(
            "color: #888888; font-style: italic; font-size: 11pt;"
        )
        self.iso_page.iso_type_label.hide()

        self.drive_page.drive_list.clearSelection()

        self.flash_page.set_flash_info("", "", "")
        self.flash_page.content_container.show()
        self.flash_page.progress_container.hide()
        self.flash_page.progress_bar.setValue(0)

        self.step_indicator.set_step(1)
        self.stacked_widget.setCurrentWidget(self.iso_page)
        self.update_navigation_buttons()

    def show_logs(self):
        self.logs_window.show()
        self.logs_window.raise_()
        self.logs_window.activateWindow()

    def show_iso_downloader(self):
        self.iso_downloader_widget.show()
        self.iso_downloader_widget.raise_()
        self.iso_downloader_widget.activateWindow()

    def show_about(self):
        self.about_widget.show()
        self.about_widget.raise_()
        self.about_widget.activateWindow()


if __name__ == "__main__":
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland.textinput=false"

    app = QApplication(sys.argv)
    app.setStyleSheet(get_etcher_style())

    icon_path = resource_path("images/icon.png")
    app.setWindowIcon(QIcon(icon_path))
    os.environ["XDG_CURRENT_DESKTOP"] = os.environ.get("XDG_CURRENT_DESKTOP", "")

    window = EtcherWizardApp()
    window.show()

    sys.exit(app.exec())
