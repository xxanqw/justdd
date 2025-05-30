from PySide6.QtCore import QThread, Signal
import requests
import time
import os


class IsoDownloadWorker(QThread):
    progress = Signal(
        int, float, float, float
    )  # percent, speed_MBps, time_left_s, time_spent_s
    status = Signal(str)
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

            with requests.get(self.url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                with open(self.dest, "wb") as f:
                    downloaded_size = 0
                    for chunk in r.iter_content(chunk_size=8192 * 4):
                        if not self._is_running:
                            self.status.emit("Download cancelled by user.")
                            self.finished.emit(False, "Download cancelled.")
                            if os.path.exists(self.dest):  # Clean up partial file
                                try:
                                    os.remove(self.dest)
                                    self.status.emit(
                                        f"Removed partial file: {self.dest}"
                                    )
                                except OSError as e:
                                    self.status.emit(
                                        f"Error removing partial file: {e}"
                                    )
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

                                if elapsed_time_total > 0.001:
                                    speed_bps = downloaded_size / elapsed_time_total
                                    speed_MBps = speed_bps / (1024 * 1024)

                                if total_size > 0:
                                    if speed_bps > 0:
                                        time_left_s = (
                                            total_size - downloaded_size
                                        ) / speed_bps
                                    elif downloaded_size < total_size:
                                        time_left_s = float("inf")
                                    else:
                                        time_left_s = 0

                                self.progress.emit(
                                    percent, speed_MBps, time_left_s, time_spent_s
                                )
                                self.last_update_time = current_time
            if not self._is_running:  # Check again after loop
                if os.path.exists(self.dest):  # Clean up partial file
                    try:
                        os.remove(self.dest)
                        self.status.emit(
                            f"Removed partial file: {self.dest} after loop"
                        )
                    except OSError as e:
                        self.status.emit(f"Error removing partial file after loop: {e}")
                return

            self.status.emit("Download complete.")
            final_elapsed_time = time.time() - self.start_time
            final_speed_MBps = 0.0
            if final_elapsed_time > 0 and total_size > 0:
                final_speed_MBps = (total_size / final_elapsed_time) / (1024 * 1024)
            self.progress.emit(100, final_speed_MBps, 0, final_elapsed_time)
            self.finished.emit(True, self.dest)
        except Exception as e:
            if self._is_running:
                self.status.emit(f"Download failed: {e}")
                self.finished.emit(False, str(e))
                if os.path.exists(self.dest):  # Clean up partial file on error
                    try:
                        os.remove(self.dest)
                        self.status.emit(f"Removed partial file on error: {self.dest}")
                    except OSError as err_rem:
                        self.status.emit(
                            f"Error removing partial file on error: {err_rem}"
                        )

    def stop(self):
        self._is_running = False
