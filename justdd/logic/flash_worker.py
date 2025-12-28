"""
FlashWorker

Background thread that performs the actual flashing / USB preparation work.

This is a copy of the `FlashWorker` class from the main application moved into
the `logic` package as a copy-only change (no behavior changes).
"""

import os
import re
import subprocess
import tempfile

from PySide6.QtCore import QThread, Signal


class FlashWorker(QThread):
    progress = Signal(int)
    status_update = Signal(str)
    log_message = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, iso_path, target_drive, mode="linux", partition_scheme="gpt"):
        super().__init__()
        self.iso_path = iso_path
        self.target_drive = target_drive
        self.mode = mode
        self.partition_scheme = partition_scheme
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
                except Exception as e:
                    try:
                        self.log_message.emit(
                            f"Error terminating process during run() cleanup: {e}"
                        )
                    except Exception:
                        pass
                self._process = None

    def _flash_linux(self):
        self.status_update.emit("Preparing to flash...")
        self.log_message.emit("Starting Linux flash process")
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

            # Ensure stdout exists (stubs may show it as Optional[IO])
            stdout = process.stdout
            if stdout is None:
                self.log_message.emit("Flash process has no stdout - aborting")
                self.finished.emit(False, "Flash process started without stdout")
                return

            progress_value = 10
            while True:
                if self.isInterruptionRequested():
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except Exception as e:
                        try:
                            self.log_message.emit(f"Error terminating dd process: {e}")
                        except Exception:
                            pass
                    self.log_message.emit("Flash operation cancelled")
                    return

                output = stdout.readline()
                if output:
                    self.log_message.emit(output.strip())

                    # Parse dd progress output to calculate percentage
                    if "bytes" in output.lower() and iso_size > 0:
                        try:
                            # Extract bytes copied from dd output
                            match = re.search(r"(\d+)\s+bytes", output)
                            if match:
                                bytes_copied = int(match.group(1))
                                percentage = (bytes_copied / iso_size) * 80 + 10
                                progress_value = min(int(percentage), 90)
                                self.progress.emit(progress_value)

                                if "copied" in output.lower():
                                    self.status_update.emit(
                                        f"Copying... {bytes_copied / (1024**3):.2f} GB / {iso_size / (1024**3):.2f} GB"
                                    )
                        except (ValueError, AttributeError):
                            if "copied" in output.lower():
                                progress_value = min(progress_value + 2, 90)
                                self.progress.emit(progress_value)
                    elif "copied" in output.lower():
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
        self.log_message.emit("Starting Windows USB preparation")
        self.log_message.emit(f"ISO: {self.iso_path}")
        self.log_message.emit(f"Target: {self.target_drive}")
        self.log_message.emit(f"Partition scheme: {self.partition_scheme.upper()}")

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
        except Exception as e:
            self.log_message.emit(f"fuser check failed (windows): {e}")

        drive = self.target_drive
        iso_mount = "/mnt/justdd_iso"

        if self.partition_scheme == "mbr":
            self._flash_windows_mbr(drive, iso_mount)
        else:
            self._flash_windows_gpt(drive, iso_mount)

    def _flash_windows_gpt(self, drive, iso_mount):
        """Flash Windows using GPT partition scheme (UEFI)"""
        p1, p2 = f"{drive}1", f"{drive}2"
        vfat_mount, ntfs_mount = "/mnt/justdd_vfat", "/mnt/justdd_ntfs"

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
            ("Setting boot flag", 28, ["parted", drive, "set", "1", "esp", "on"]),
            ("Waiting for partition recognition", 30, ["partprobe", drive]),
            ("Waiting for devices", 32, ["sleep", "2"]),
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

        self._execute_windows_script(steps, drive, "GPT (UEFI)")

    def _flash_windows_mbr(self, drive, iso_mount):
        p1 = f"{drive}1"
        ntfs_mount = "/mnt/justdd_ntfs"

        steps = [
            ("Wiping filesystem signatures", 10, ["wipefs", "-a", drive]),
            (
                "Creating MBR partition table",
                15,
                ["parted", "--script", drive, "mklabel", "msdos"],
            ),
            (
                "Creating Windows partition",
                20,
                [
                    "parted",
                    "--script",
                    drive,
                    "mkpart",
                    "primary",
                    "ntfs",
                    "0%",
                    "100%",
                ],
            ),
            ("Setting boot flag", 25, ["parted", drive, "set", "1", "boot", "on"]),
            ("Waiting for partition recognition", 30, ["partprobe", drive]),
            ("Waiting for devices", 35, ["sleep", "2"]),
            (
                "Formatting Windows partition",
                40,
                ["mkfs.ntfs", "--quick", "-L", "WINDOWS", p1],
            ),
            (
                "Creating mount directories",
                45,
                ["mkdir", "-p", iso_mount, ntfs_mount],
            ),
            ("Mounting ISO", 50, ["mount", "-o", "loop", self.iso_path, iso_mount]),
            ("Mounting Windows partition", 55, ["mount", p1, ntfs_mount]),
            (
                "Copying Windows files (this takes a long time)",
                60,
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
            ("Installing bootloader", 85, ["ms-sys", "-7", drive]),
            ("Unmounting Windows partition", 95, ["umount", ntfs_mount]),
            ("Unmounting ISO", 97, ["umount", iso_mount]),
            ("Syncing filesystem", 99, ["sync"]),
            (
                "Cleaning up mount directories",
                100,
                ["rmdir", iso_mount, ntfs_mount],
            ),
        ]

        self._execute_windows_script(steps, drive, "MBR (BIOS)")

    def _execute_windows_script(self, steps, drive, scheme_name):
        try:
            script_lines = [
                "#!/bin/bash",
                "set -e",
                "",
                f"# Windows USB creation script - {scheme_name}",
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
                "    mount | grep \"^$device\" | awk '{print $1}' | while read partition; do",
                '        if [ -n "$partition" ]; then',
                '            echo "Unmounting partition: $partition"',
                '            umount "$partition" 2>/dev/null || umount -l "$partition" 2>/dev/null || true',
                "        fi",
                "    done",
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
                "    if command -v fuser >/dev/null 2>&1; then",
                f'        fuser -km "{drive}" 2>/dev/null || true',
                f'        fuser -km "{drive}"* 2>/dev/null || true',
                "    fi",
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
                '        unmount_device_partitions "$device"',
                '        kill_device_processes "$device"',
                "        ",
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
                "trap cleanup EXIT",
                "cleanup",
                "",
                f'echo "Preparing device {drive} with {scheme_name}"',
                f'unmount_device_partitions "{drive}"',
                f'kill_device_processes "{drive}"',
                "sleep 3",
                "",
            ]

            for idx, (desc, progress_val, cmd) in enumerate(steps, 1):
                script_lines.append(f'echo "Step {idx}/{len(steps)}: {desc}"')
                script_lines.append("check_interruption")

                if cmd[0] == "wipefs":
                    script_lines.append(f'retry_wipefs "{drive}"')
                elif cmd[0] == "ms-sys":
                    # Special handling for ms-sys (MBR bootloader)
                    script_lines.append("# Installing MBR bootloader")
                    script_lines.append("if command -v ms-sys >/dev/null 2>&1; then")
                    script_lines.append(
                        '    echo "Installing Windows 7 MBR bootloader with ms-sys"'
                    )
                    script_lines.append(
                        f'    ms-sys -7 "{drive}" && echo "MBR bootloader installed successfully" || echo "Warning: ms-sys failed, trying alternative method"'
                    )
                    script_lines.append("else")
                    script_lines.append(
                        '    echo "ms-sys not found, trying alternative bootloader installation..."'
                    )
                    script_lines.append(
                        "    # Try to install bootloader using syslinux if available"
                    )
                    script_lines.append(
                        "    if command -v syslinux >/dev/null 2>&1; then"
                    )
                    script_lines.append(
                        '        echo "Installing bootloader with syslinux"'
                    )
                    script_lines.append(
                        f'        syslinux -i "{drive}1" && echo "Syslinux bootloader installed" || echo "Syslinux installation failed"'
                    )
                    script_lines.append("    else")
                    script_lines.append(
                        '        echo "Warning: No bootloader installation method available"'
                    )
                    script_lines.append(
                        '        echo "The USB may not be bootable on BIOS systems"'
                    )
                    script_lines.append(
                        '        echo "Consider installing ms-sys package: sudo pacman -S ms-sys"'
                    )
                    script_lines.append("    fi")
                    script_lines.append("fi")
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
                    f'echo "Windows USB creation completed successfully with {scheme_name}!"',
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

                stdout = self._process.stdout
                if stdout is None:
                    try:
                        self.log_message.emit(
                            "Windows script started without stdout - aborting"
                        )
                    except Exception:
                        pass
                    self.finished.emit(False, "Windows script has no stdout")
                    return

                while True:
                    if self.isInterruptionRequested():
                        try:
                            with open(cancel_file, "w") as f:
                                f.write("cancel")
                        except Exception as e:
                            try:
                                self.log_message.emit(
                                    f"Failed to write cancel file: {e}"
                                )
                            except Exception:
                                pass

                        try:
                            self._process.terminate()
                            self._process.wait(timeout=5)
                        except Exception as e:
                            try:
                                self.log_message.emit(
                                    f"Failed to terminate windows script process: {e}"
                                )
                            except Exception:
                                pass

                        self.log_message.emit("Windows USB preparation cancelled")
                        return

                    output = stdout.readline()
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
                except Exception as e:
                    try:
                        self.log_message.emit(f"Failed to remove cancel file: {e}")
                    except Exception:
                        pass

                return_code = self._process.wait()

                if return_code == 0:
                    self.progress.emit(100)
                    self.status_update.emit(
                        f"Windows USB preparation completed ({scheme_name})!"
                    )
                    self.finished.emit(
                        True, f"Windows USB created successfully with {scheme_name}!"
                    )
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
                except Exception as e:
                    try:
                        self.log_message.emit(f"Failed to remove temporary script: {e}")
                    except Exception:
                        pass
                self._process = None

        except Exception as e:
            if not self.isInterruptionRequested():
                self.log_message.emit(f"Windows USB preparation failed: {str(e)}")
                self.finished.emit(False, f"Windows USB preparation failed: {str(e)}")
