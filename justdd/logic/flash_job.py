"""
FlashJob

A NiceGUI-friendly, polling-oriented replacement for the Qt-based `FlashWorker`.
This module provides a background worker implemented with `threading.Thread`
that performs the same high-level tasks as the original FlashWorker:

- Linux flashing using `dd` (via `pkexec dd ... status=progress`) and parsing
  dd progress output to infer progress percentage.
- Windows USB creation by generating a bash script and running it via `pkexec`.
  The generated script prints step markers like "Step X/Y: <desc>" which we
  parse to update progress & status.

Differences vs the Qt variant:
- No dependency on PySide6/QThread or Qt signals. Instead, this class is
  designed to be polled from an event loop (e.g. NiceGUI via `ui.timer`) or
  to use optional callbacks.
- Thread-safe access to status, progress and logs via a `threading.Lock`.

Usage (example):
    job = FlashJob('/path/to.iso', '/dev/sdb', mode='linux', partition_scheme='gpt')
    job.start()
    # Option 1: Poll job.get_progress(), job.get_status(), job.get_logs() periodically
    # Option 2: Provide callbacks on init: on_progress, on_status, on_log, on_finished

Note: This worker runs shell tools that generally require elevated privileges
(e.g. `pkexec dd ...`, `parted`, `mkfs.*`). Running these will prompt for
authentication (graphical or otherwise) depending on the system configuration.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import threading
import time
from typing import Callable, List, Optional, Tuple

__all__ = ["FlashJob"]


class FlashJob:
    """
    Background job that performs flashing operations.

    Attributes (read under lock via getters):
        progress (int) : 0-100
        status (str) : human readable status
        logs (List[str]) : accumulated log lines
        finished (bool) : True when job finished (success or failure)
        success (bool) : True if succeeded
        finished_message (Optional[str]) : message produced on finish (success/failure)
    """

    def __init__(
        self,
        iso_path: str,
        target_drive: str,
        mode: str = "linux",
        partition_scheme: str = "gpt",
        on_progress: Optional[Callable[[int], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None,
    ):
        self.iso_path = iso_path
        self.target_drive = target_drive
        self.mode = mode
        self.partition_scheme = partition_scheme

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._process: Optional[subprocess.Popen] = None

        # Internal state (protected by _lock)
        self._lock = threading.Lock()
        self._progress: int = 0
        self._status: str = ""
        self._logs: List[str] = []
        self._finished: bool = False
        self._success: bool = False
        self._finished_message: Optional[str] = None

        # Optional callbacks (invoked under the lock when set)
        self._on_progress = on_progress
        self._on_status = on_status
        self._on_log = on_log
        self._on_finished = on_finished

    # ---- Public / Polling-friendly getters ----
    def get_progress(self) -> int:
        with self._lock:
            return self._progress

    def get_status(self) -> str:
        with self._lock:
            return self._status

    def get_logs(self) -> List[str]:
        with self._lock:
            return list(self._logs)

    def is_finished(self) -> bool:
        with self._lock:
            return self._finished

    def was_successful(self) -> bool:
        with self._lock:
            return self._success

    def get_finished_message(self) -> Optional[str]:
        with self._lock:
            return self._finished_message

    # ---- Control methods ----
    def start(self) -> None:
        """Start the job in a background thread."""
        if self._thread and self._thread.is_alive():
            # already running
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Signal the job to stop and attempt to terminate any running subprocess."""
        self._stop_event.set()
        # try to kill running process promptly
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for the thread to complete. Returns True if thread joined in time."""
        if not self._thread:
            return True
        self._thread.join(timeout)
        return not self._thread.is_alive()

    # ---- Internal helpers ----
    def _set_progress(self, value: int) -> None:
        with self._lock:
            self._progress = max(0, min(100, int(value)))
            cb = self._on_progress
        if cb:
            try:
                cb(self._progress)
            except Exception:
                pass

    def _set_status(self, text: str) -> None:
        with self._lock:
            self._status = text
            cb = self._on_status
        if cb:
            try:
                cb(text)
            except Exception:
                pass

    def _log(self, text: str) -> None:
        # Normalize line endings and append single lines
        lines = [ln for ln in text.splitlines() if ln.strip() != ""]
        if not lines:
            return
        with self._lock:
            for ln in lines:
                self._logs.append(ln)
            cb = self._on_log
        if cb:
            try:
                for ln in lines:
                    cb(ln)
            except Exception:
                pass

    def _finish(self, success: bool, message: str) -> None:
        with self._lock:
            self._finished = True
            self._success = success
            self._finished_message = message
            cb = self._on_finished
        if cb:
            try:
                cb(success, message)
            except Exception:
                pass

    def _should_stop(self) -> bool:
        return self._stop_event.is_set()

    # ---- Run logic ----
    def _run(self) -> None:
        try:
            if self.mode == "windows":
                self._flash_windows()
            else:
                self._flash_linux()
        except Exception as e:
            # Unhandled exception; log and finish with failure
            self._log(f"Unexpected error: {e}")
            self._finish(False, f"Flash failed: {e}")
        finally:
            # Ensure subprocess is terminated if stop requested
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    pass
                self._process = None

    # ---- Linux (dd) flow ----
    def _flash_linux(self) -> None:
        self._set_status("Preparing to flash...")
        self._log("Starting Linux flash process")
        self._log(f"ISO: {self.iso_path}")
        self._log(f"Target: {self.target_drive}")

        try:
            iso_size = os.path.getsize(self.iso_path)
            self._log(f"ISO size: {iso_size} bytes ({iso_size / (1024**3):.2f} GB)")
        except Exception as e:
            self._log(f"Could not get ISO size: {e}")
            iso_size = 0

        self._set_progress(5)
        time.sleep(0.5)

        # Check device busy via fuser (best-effort)
        try:
            result = subprocess.run(
                ["fuser", "-m", self.target_drive],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._log(f"Device busy - PIDs: {result.stdout.strip()}")
                self._finish(False, "Device is busy or mounted")
                return
        except Exception:
            # If fuser isn't available or fails, continue
            pass

        self._set_progress(10)
        self._set_status("Starting dd operation...")

        cmd = [
            "pkexec",
            "dd",
            f"if={self.iso_path}",
            f"of={self.target_drive}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
        ]

        self._log(f"Command: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            self._process = process
            stdout = process.stdout
            if stdout is None:
                self._log("Flash process started without stdout - aborting")
                self._finish(False, "Flash process started without stdout")
                return

            progress_value = 10
            while True:
                if self._should_stop():
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except Exception:
                        pass
                    self._log("Flash operation cancelled")
                    self._finish(False, "Flash cancelled")
                    return

                line = stdout.readline()
                if line:
                    line = line.strip()
                    self._log(line)

                    # Parse dd progress output for 'bytes' copied
                    if "bytes" in line.lower() and iso_size > 0:
                        try:
                            match = re.search(r"(\d+)\s+bytes", line)
                            if match:
                                bytes_copied = int(match.group(1))
                                percentage = (bytes_copied / iso_size) * 80 + 10
                                progress_value = min(int(percentage), 90)
                                self._set_progress(progress_value)

                                if "copied" in line.lower():
                                    self._set_status(
                                        f"Copying... {bytes_copied / (1024**3):.2f} GB / {iso_size / (1024**3):.2f} GB"
                                    )
                        except Exception:
                            # parsing problem: fallback to incremental updates
                            if "copied" in line.lower():
                                progress_value = min(progress_value + 2, 90)
                                self._set_progress(progress_value)
                    elif "copied" in line.lower():
                        # fallback
                        progress_value = min(progress_value + 2, 90)
                        self._set_progress(progress_value)

                elif process.poll() is not None:
                    break

                # Throttle loop to yield CPU
                time.sleep(0.1)

            return_code = process.wait()

            if return_code == 0:
                self._set_progress(95)
                self._set_status("Syncing filesystem...")
                self._log("Running final sync...")

                try:
                    subprocess.run(["sync"], timeout=30, check=True)
                    time.sleep(1)
                except Exception as e:
                    self._log(f"Sync warning: {e}")

                self._set_progress(100)
                self._set_status("Flash completed successfully!")
                self._finish(True, "Flash completed successfully!")
            else:
                self._finish(False, f"dd command failed with exit code {return_code}")

        except subprocess.TimeoutExpired:
            self._finish(False, "Flash operation timed out")
        except Exception as e:
            self._finish(False, f"Flash failed: {e}")
        finally:
            self._process = None

    # ---- Windows flow (script-based) ----
    def _flash_windows(self) -> None:
        if self._should_stop():
            return

        self._set_status("Preparing Windows USB...")
        self._log("Starting Windows USB preparation")
        self._log(f"ISO: {self.iso_path}")
        self._log(f"Target: {self.target_drive}")
        self._log(f"Partition scheme: {self.partition_scheme.upper()}")

        self._set_progress(5)

        try:
            result = subprocess.run(
                ["fuser", "-m", self.target_drive],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._log(f"Device busy - PIDs: {result.stdout.strip()}")
                self._finish(False, "Device is busy or mounted")
                return
        except Exception:
            pass

        drive = self.target_drive
        iso_mount = "/mnt/justdd_iso"

        if self.partition_scheme == "mbr":
            steps = self._windows_mbr_steps(drive, iso_mount)
            scheme_name = "MBR (BIOS)"
        else:
            steps = self._windows_gpt_steps(drive, iso_mount)
            scheme_name = "GPT (UEFI)"

        self._execute_windows_script(steps, drive, scheme_name)

    def _windows_gpt_steps(
        self, drive: str, iso_mount: str
    ) -> List[Tuple[str, int, List[str]]]:
        p1, p2 = f"{drive}1", f"{drive}2"
        return [
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
                ["mkdir", "-p", iso_mount, "/mnt/justdd_vfat", "/mnt/justdd_ntfs"],
            ),
            ("Mounting ISO", 50, ["mount", "-o", "loop", self.iso_path, iso_mount]),
            ("Mounting BOOT partition", 55, ["mount", p1, "/mnt/justdd_vfat"]),
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
                    "/mnt/justdd_vfat/",
                ],
            ),
            (
                "Creating sources directory",
                65,
                ["mkdir", "-p", "/mnt/justdd_vfat/sources"],
            ),
            (
                "Copying boot.wim",
                70,
                ["cp", f"{iso_mount}/sources/boot.wim", "/mnt/justdd_vfat/sources/"],
            ),
            ("Mounting INSTALL partition", 75, ["mount", p2, "/mnt/justdd_ntfs"]),
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
                    "/mnt/justdd_ntfs/",
                ],
            ),
            ("Unmounting INSTALL partition", 90, ["umount", "/mnt/justdd_ntfs"]),
            ("Unmounting BOOT partition", 95, ["umount", "/mnt/justdd_vfat"]),
            ("Unmounting ISO", 97, ["umount", iso_mount]),
            ("Syncing filesystem", 99, ["sync"]),
            (
                "Cleaning up mount directories",
                100,
                ["rmdir", iso_mount, "/mnt/justdd_vfat", "/mnt/justdd_ntfs"],
            ),
        ]

    def _windows_mbr_steps(
        self, drive: str, iso_mount: str
    ) -> List[Tuple[str, int, List[str]]]:
        p1 = f"{drive}1"
        return [
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
                ["mkdir", "-p", iso_mount, "/mnt/justdd_ntfs"],
            ),
            ("Mounting ISO", 50, ["mount", "-o", "loop", self.iso_path, iso_mount]),
            ("Mounting Windows partition", 55, ["mount", p1, "/mnt/justdd_ntfs"]),
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
                    "/mnt/justdd_ntfs/",
                ],
            ),
            ("Installing bootloader", 85, ["ms-sys", "-7", drive]),
            ("Unmounting Windows partition", 95, ["umount", "/mnt/justdd_ntfs"]),
            ("Unmounting ISO", 97, ["umount", iso_mount]),
            ("Syncing filesystem", 99, ["sync"]),
            (
                "Cleaning up mount directories",
                100,
                ["rmdir", iso_mount, "/mnt/justdd_ntfs"],
            ),
        ]

    def _execute_windows_script(
        self, steps: List[Tuple[str, int, List[str]]], drive: str, scheme_name: str
    ) -> None:
        """
        Create a temporary bash script that runs the ordered steps and run it via pkexec.
        The script prints "Step i/N: Description" lines which we parse to update progress.
        """
        try:
            script_lines: List[str] = [
                "#!/bin/bash",
                "set -e",
                "",
                f"# Windows USB creation script - {scheme_name}",
                "",
                # Interruption check function (looks for a cancel file)
                "check_interruption() {",
                '    if [ -f "/tmp/justdd_cancel_$$" ]; then',
                '        echo "Operation cancelled by user"',
                "        exit 130",
                "    fi",
                "}",
                "",
                # Safe unmount helper
                "safe_unmount() {",
                '    local mount_point="$1"',
                '    if mountpoint -q "$mount_point" 2>/dev/null; then',
                '        echo "Unmounting $mount_point"',
                '        umount "$mount_point" 2>/dev/null || umount -l "$mount_point" 2>/dev/null || true',
                "    fi",
                "}",
                "",
                # Unmount device partitions helper
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
                # Kill processes using the device
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
                # Retry wipefs function (resiliency)
                "retry_wipefs() {",
                '    local device="$1"',
                "    local max_attempts=3",
                "    local attempt=1",
                "    ",
                "    while [ $attempt -le $max_attempts ]; do",
                '        echo "Wipefs attempt $attempt/$max_attempts"',
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
                    # ms-sys handling (best-effort)
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
                    quoted = []
                    for arg in cmd:
                        if " " in arg or any(c in arg for c in ["$", "`", '"', "'"]):
                            quoted.append(f'"{arg}"')
                        else:
                            quoted.append(arg)
                    script_lines.append(" ".join(quoted))

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
            except Exception:
                pass

            self._log(f"Created Windows USB preparation script: {script_path}")

            cancel_file = f"/tmp/justdd_cancel_{os.getpid()}"

            # Launch via pkexec; capture combined stdout/stderr
            try:
                self._process = subprocess.Popen(
                    ["pkexec", "bash", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
            except FileNotFoundError as e:
                # pkexec not available or other system problem
                self._log(f"Failed to start script: {e}")
                self._finish(False, f"Failed to start Windows script: {e}")
                try:
                    os.unlink(script_path)
                except Exception:
                    pass
                return

            stdout = self._process.stdout
            if stdout is None:
                self._log("Windows script started without stdout - aborting")
                self._finish(False, "Windows script has no stdout")
                try:
                    os.unlink(script_path)
                except Exception:
                    pass
                return

            while True:
                if self._should_stop():
                    # signal cancellation to the script by creating the cancel file
                    try:
                        with open(cancel_file, "w") as f:
                            f.write("cancel")
                    except Exception as e:
                        self._log(f"Failed to write cancel file: {e}")

                    try:
                        self._process.terminate()
                        self._process.wait(timeout=5)
                    except Exception:
                        pass

                    self._log("Windows USB preparation cancelled")
                    self._finish(False, "Windows USB preparation cancelled")
                    break

                line = stdout.readline()
                if line:
                    line = line.strip()
                    self._log(line)

                    if line.startswith("Step "):
                        try:
                            step_info = line.split(": ", 1)
                            if len(step_info) > 1:
                                step_num = int(step_info[0].split()[1].split("/")[0])
                                if 1 <= step_num <= len(steps):
                                    progress_val = steps[step_num - 1][1]
                                    self._set_progress(progress_val)
                                    self._set_status(step_info[1])
                        except Exception:
                            pass
                elif self._process.poll() is not None:
                    break

                time.sleep(0.1)

            # cleanup cancel file if present
            try:
                if os.path.exists(cancel_file):
                    os.unlink(cancel_file)
            except Exception:
                pass

            return_code = self._process.wait()
            try:
                os.unlink(script_path)
            except Exception:
                pass

            if return_code == 0:
                self._set_progress(100)
                self._set_status(f"Windows USB preparation completed ({scheme_name})!")
                self._finish(
                    True, f"Windows USB created successfully with {scheme_name}!"
                )
            elif return_code == 130:
                # cancel signal
                self._log("Operation cancelled by user")
                self._finish(False, "Operation cancelled")
            else:
                self._finish(
                    False, f"Windows script failed with exit code {return_code}"
                )

        except Exception as e:
            self._log(f"Error executing Windows USB script: {e}")
            self._finish(False, f"Error executing Windows USB script: {e}")
        finally:
            self._process = None
