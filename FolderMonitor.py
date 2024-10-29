import os
import time
import threading
from typing import Dict, List, Tuple


class FolderMonitor:
    """
    Monitors a specified folder for any changes in file states, such as file additions, modifications, and deletions.
    Calls a specified callback function when changes are detected.
    """

    def __init__(self, folder_path: str, interval: int = 10):
        """
        Initializes the FolderMonitor.

        Args:
            folder_path (str): Path of the folder to monitor.
            interval (int, optional): Time interval in seconds between checks. Defaults to 10.
        """
        self.folder_path = folder_path
        self.interval = interval
        self.previous_state = None
        self.monitoring = False
        self.monitoring_thread = None

    def get_folder_state(self) -> Dict[str, float]:
        """
        Retrieves the current state of the folder by mapping file paths to their last modified times.

        Returns:
            Dict[str, float]: A dictionary where keys are file paths and values are modification times.
        """
        folder_state = {}
        for name in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, name)
            if os.path.isfile(file_path):
                folder_state[file_path] = os.path.getmtime(file_path)
        return folder_state

    def has_folder_changed(self) -> Tuple[bool, Dict[str, float], List[Tuple[str, str]]]:
        """
        Checks for changes in the folder by comparing the current state to the previous state.

        Returns:
            Tuple[bool, Dict[str, float], List[Tuple[str, str]]]: A tuple containing:
                - A boolean indicating if changes were detected.
                - The current state of the folder as a dictionary.
                - A list of tuples, each containing the file path and type of change (e.g., "new", "modified", "deleted").
        """
        current_state = self.get_folder_state()
        if self.previous_state is None:
            return False, current_state, []

        changes = []
        for file_path, mtime in self.previous_state.items():
            if file_path not in current_state:
                changes.append((file_path, "deleted"))
            elif current_state[file_path] != mtime:
                changes.append((file_path, "modified"))

        for file_path in current_state:
            if file_path not in self.previous_state:
                changes.append((file_path, "new"))

        return bool(changes), current_state, changes

    def start_monitoring(self, on_change_callback) -> None:
        """
        Starts monitoring the folder for changes in a separate thread.

        Args:
            on_change_callback (callable): Function to call when changes are detected.
                                           This function should accept a list of change tuples as a parameter.
        """
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor, args=(on_change_callback,))
        self.monitoring_thread.start()

    def stop_monitoring(self) -> None:
        """
        Stops monitoring the folder and waits for the monitoring thread to finish.
        """
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()

    def _monitor(self, on_change_callback) -> None:
        """
        Internal method that continuously monitors the folder at set intervals and calls the callback
        function when changes are detected.

        Args:
            on_change_callback (callable): Function to call when changes are detected.
        """
        while self.monitoring:
            is_changed, new_state, changes = self.has_folder_changed()
            if is_changed:
                on_change_callback(changes)
            self.previous_state = new_state
            time.sleep(self.interval)
