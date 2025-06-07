import asyncio
import aiohttp
import json
import re
from packaging import version
from PySide6.QtCore import QObject, Signal, QThread
from constants import __VERSION__, __GITHUB_URL__


class UpdateChecker(QObject):
    update_available = Signal(str, str)  # new_version, download_url
    no_update = Signal()
    check_failed = Signal(str)  # error_message

    def __init__(self):
        super().__init__()
        self.current_version = __VERSION__
        self.github_api_url = self._get_github_api_url()
        self._check_thread = None

    def _get_github_api_url(self):
        """Convert GitHub URL to API URL for releases"""
        # Extract owner/repo from GitHub URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)', __GITHUB_URL__)
        if match:
            owner, repo = match.groups()
            repo = repo.rstrip('/')  # Remove trailing slash if present
            return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        return None

    def _normalize_version(self, version_str):
        """Normalize version string for comparison"""
        # Remove 'v' prefix if present and handle different formats
        version_str = version_str.lstrip('v')
        # Convert format like "0.1.3-2" or "0.1.3 (2)" to standard format
        version_str = re.sub(r'[\s\(\)]+', '-', version_str).strip('-')
        return version_str

    def _compare_versions(self, current, latest):
        """Compare two version strings"""
        try:
            current_norm = self._normalize_version(current)
            latest_norm = self._normalize_version(latest)
            
            return version.parse(latest_norm) > version.parse(current_norm)
        except Exception:
            # Fallback to string comparison if parsing fails
            return latest != current

    async def _fetch_latest_version(self):
        """Fetch latest version from GitHub API"""
        if not self.github_api_url:
            raise Exception("Invalid GitHub URL")

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(self.github_api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        tag_name = data.get('tag_name', '')
                        download_url = data.get('html_url', __GITHUB_URL__)
                        return tag_name, download_url
                    else:
                        raise Exception(f"GitHub API returned status {response.status}")
            except asyncio.TimeoutError:
                raise Exception("Request timed out")
            except aiohttp.ClientError as e:
                raise Exception(f"Network error: {str(e)}")

    async def check_for_updates_async(self):
        """Async method to check for updates"""
        try:
            latest_version, download_url = await self._fetch_latest_version()
            
            if self._compare_versions(self.current_version, latest_version):
                return True, latest_version, download_url
            else:
                return False, latest_version, download_url
                
        except Exception as e:
            raise Exception(f"Update check failed: {str(e)}")

    def check_for_updates(self):
        """Start async update check in thread"""
        # Clean up existing thread if any
        self.cleanup_thread()
        
        self._check_thread = UpdateCheckThread(self)
        self._check_thread.result_ready.connect(self._handle_result)
        self._check_thread.error_occurred.connect(self._handle_error)
        self._check_thread.finished.connect(self._on_thread_finished)
        self._check_thread.start()

    def cleanup_thread(self):
        """Clean up the update check thread"""
        if self._check_thread and self._check_thread.isRunning():
            try:
                # Disconnect signals first
                self._check_thread.result_ready.disconnect()
                self._check_thread.error_occurred.disconnect()
                self._check_thread.finished.disconnect()
            except:
                pass
            
            # Request interruption and wait
            self._check_thread.requestInterruption()
            if not self._check_thread.wait(2000):  # Wait 2 seconds
                self._check_thread.terminate()
                self._check_thread.wait(1000)  # Wait 1 second for termination
            
            self._check_thread = None

    def _on_thread_finished(self):
        """Handle thread finished signal"""
        if self._check_thread:
            self._check_thread.deleteLater()
            self._check_thread = None

    def _handle_result(self, has_update, latest_version, download_url):
        """Handle update check result"""
        if has_update:
            self.update_available.emit(latest_version, download_url)
        else:
            self.no_update.emit()

    def _handle_error(self, error_message):
        """Handle update check error"""
        self.check_failed.emit(error_message)


class UpdateCheckThread(QThread):
    result_ready = Signal(bool, str, str)  # has_update, version, url
    error_occurred = Signal(str)

    def __init__(self, update_checker):
        super().__init__()
        self.update_checker = update_checker
        self._loop = None

    def run(self):
        """Run the async update check in thread"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            has_update, latest_version, download_url = self._loop.run_until_complete(
                self.update_checker.check_for_updates_async()
            )
            
            if not self.isInterruptionRequested():
                self.result_ready.emit(has_update, latest_version, download_url)
            
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error_occurred.emit(str(e))
        finally:
            if self._loop:
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(self._loop)
                    for task in pending:
                        task.cancel()
                    
                    # Wait for tasks to complete cancellation
                    if pending:
                        self._loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    
                    self._loop.close()
                except:
                    pass
                self._loop = None
