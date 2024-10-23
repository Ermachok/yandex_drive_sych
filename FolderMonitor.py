import os
import time
from os import PathLike
from typing import Dict, List, Tuple
from loguru import logger
import threading

from SynchManager import SyncManager

class FolderMonitor:
    def __init__(self, folder_path: str | PathLike, sync_manager: SyncManager, interval: int = 10):
        """
        :param folder_path: Path to the folder being monitored.
        :param sync_manager: Instance of SyncManager for synchronizing with the cloud.
        :param interval: Monitoring interval in seconds.
        """
        self.folder_path = folder_path
        self.sync_manager = sync_manager
        self.interval = interval
        self.previous_state = None
        self.monitoring = False
        self.monitoring_thread = None

        logger.add("folder_changes.log", format="{time} {level} {message}", level="INFO")

    def get_folder_state(self) -> Dict:
        """Returns the current folder states of files."""
        folder_state = {}
        try:
            for name in os.listdir(self.folder_path):
                file_path = os.path.join(self.folder_path, name)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    folder_state[file_path] = file_mtime
        except FileNotFoundError:
            logger.error(f"Folder {self.folder_path} not found.")

        return folder_state

    def has_folder_changed(self) -> Tuple[bool, Dict, List[tuple]]:
        """Checks if the contents of a folder have changed based on file modification times."""
        current_state = self.get_folder_state()

        if self.previous_state is None:
            return False, current_state, []

        changed_files = []

        for file_path, mtime in self.previous_state.items():
            if file_path not in current_state:
                changed_files.append((file_path, "deleted"))
            elif current_state[file_path] != mtime:
                changed_files.append((file_path, "modified"))

        for file_path in current_state:
            if file_path not in self.previous_state:
                changed_files.append((file_path, "new"))

        has_changed = len(changed_files) > 0
        return has_changed, current_state, changed_files

    def _monitor(self) -> None:
        """Private method for monitoring folder changes."""
        while self.monitoring:
            is_changed, new_state, changes = self.has_folder_changed()
            if is_changed:
                logger.info("Changes detected in the folder:")
                for file, change_type in changes:
                    logger.info(f"File {file} was {change_type}")

                    if change_type == "new":
                        self.sync_manager.sync_new_file(file)
                    elif change_type == "modified":
                        self.sync_manager.sync_updated_file(file)
                    elif change_type == "deleted":
                        self.sync_manager.sync_deleted_file(file)
            else:
                logger.info("No changes found")

            self.previous_state = new_state

            time.sleep(self.interval)

    def start_monitoring(self) -> None:
        """Starts monitoring changes in the folder."""
        self.monitoring = True
        logger.info(f"Start monitoring folder: {self.folder_path}")

        self.monitoring_thread = threading.Thread(target=self._monitor)
        self.monitoring_thread.start()

    def stop_monitoring(self) -> None:
        """Stops monitoring the folder."""
        if self.monitoring:
            self.monitoring = False
            self.monitoring_thread.join()
            logger.info("Stopped monitoring folder.")
        else:
            logger.warning("Monitoring is not running.")
