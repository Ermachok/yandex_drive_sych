import os
import time
import threading
from typing import Dict, List, Tuple


class FolderMonitor:
    def __init__(self, folder_path: str, interval: int = 10):
        self.folder_path = folder_path
        self.interval = interval
        self.previous_state = None
        self.monitoring = False
        self.monitoring_thread = None

    def get_folder_state(self) -> Dict[str, float]:
        folder_state = {}
        for name in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, name)
            if os.path.isfile(file_path):
                folder_state[file_path] = os.path.getmtime(file_path)
        return folder_state

    def has_folder_changed(self) -> Tuple[bool, Dict[str, float], List[Tuple[str, str]]]:
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
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor, args=(on_change_callback,))
        self.monitoring_thread.start()

    def _monitor(self, on_change_callback) -> None:
        while self.monitoring:
            is_changed, new_state, changes = self.has_folder_changed()
            if is_changed:
                on_change_callback(changes)
            self.previous_state = new_state
            time.sleep(self.interval)

    def stop_monitoring(self) -> None:
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()

