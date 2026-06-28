"""Rclone-based upload backend with progress tracking."""

import subprocess
import threading
import re
from typing import Callable, Optional
from pathlib import Path
from gi.repository import GLib
from app.logger import setup_logger

logger = setup_logger()

class UploadManager:
    """Manages rclone upload operations with progress tracking."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        """Returns True if an upload is currently in progress."""
        return self._thread is not None and self._thread.is_alive()

    def cancel(self) -> None:
        """Cancels the current upload operation."""
        if self._process:
            logger.info("Cancelling upload...")
            self._cancelled = True
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def upload_folder(
        self,
        source_path: str,
        folder_name: str,
        remote: str,
        backup_root: str,
        on_progress: Callable[[float, str, str], None],
        on_log: Callable[[str], None],
        on_complete: Callable[[bool, str], None]
    ) -> None:
        if self.is_running():
            on_complete(False, "Another upload is already in progress")
            return

        self._cancelled = False
        self._thread = threading.Thread(
            target=self._upload_thread,
            args=(source_path, folder_name, remote, backup_root, on_progress, on_log, on_complete),
            daemon=True
        )
        self._thread.start()

    def _upload_thread(
        self,
        source_path: str,
        folder_name: str,
        remote: str,
        backup_root: str,
        on_progress: Callable[[float, str, str], None],
        on_log: Callable[[str], None],
        on_complete: Callable[[bool, str], None]
    ) -> None:
        try:
            if not Path(source_path).exists():
                GLib.idle_add(on_complete, False, f"Source path does not exist: {source_path}")
                return

            dest_path = f"{remote}:{backup_root}/{folder_name}"
            cmd = [
                "rclone", "sync",
                "--progress",
                "--stats", "1s",
                "--stats-log-level", "NOTICE",
                source_path,
                dest_path
            ]

            logger.info(f"Starting upload: {source_path} -> {dest_path}")
            GLib.idle_add(on_log, f"Starting upload: {folder_name}\n")
            GLib.idle_add(on_log, f"Source: {source_path}\n")
            GLib.idle_add(on_log, f"Destination: {dest_path}\n")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            if self._process.stdout:
                for line in self._process.stdout:
                    if self._cancelled:
                        break
                    
                    line = line.strip()
                    if line:
                        # SAFELY pass to main thread
                        GLib.idle_add(on_log, line + "\n")
                        
                        progress = self._parse_progress(line)
                        if progress:
                            current_file, percent = progress
                            GLib.idle_add(on_progress, folder_name, current_file, percent)

            return_code = self._process.wait()
            self._process = None

            if self._cancelled:
                GLib.idle_add(on_log, "Upload cancelled by user.\n")
                GLib.idle_add(on_complete, False, "Upload cancelled")
            elif return_code == 0:
                GLib.idle_add(on_log, f"Upload completed successfully: {folder_name}\n")
                GLib.idle_add(on_progress, folder_name, "", 100.0)
                GLib.idle_add(on_complete, True, f"Upload completed: {folder_name}")
            else:
                GLib.idle_add(on_log, f"Upload failed with code {return_code}: {folder_name}\n")
                GLib.idle_add(on_complete, False, f"Upload failed: {folder_name}")

        except FileNotFoundError:
            error_msg = "rclone not found. Please install rclone."
            logger.error(error_msg)
            GLib.idle_add(on_log, f"ERROR: {error_msg}\n")
            GLib.idle_add(on_complete, False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            GLib.idle_add(on_log, f"ERROR: {error_msg}\n")
            GLib.idle_add(on_complete, False, error_msg)

    def _parse_progress(self, line: str) -> Optional[tuple[str, float]]:
        file_match = re.match(r'\s+\*\s+(.+)', line)
        if file_match:
            return (file_match.group(1).strip(), -1.0)
        
        percent_match = re.search(r'(\d+\.?\d*)\s*%', line)
        if percent_match:
            return ("", float(percent_match.group(1)))
        
        return None