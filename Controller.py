from typing import List, Tuple
from loguru import logger
from abc import ABC, abstractmethod

from CloudSync import CloudSync
from FolderMonitor import FolderMonitor

class SyncController(ABC):
    @abstractmethod
    def setup_logging(self):
        pass

    @abstractmethod
    def handle_changes(self, changes: List[Tuple[str, str]]):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class SyncYandexController(SyncController):
    action_map = {
        "new": {
            "method": "sync_new_file",
            "success_code": 201,
            "success_message": "File uploaded",
            "error_message": "Upload error"
        },
        "modified": {
            "method": "sync_updated_file",
            "success_code": 201,
            "success_message": "Cloud updated",
            "error_message": "Update error"
        },
        "deleted": {
            "method": "sync_deleted_file",
            "success_code": 204,
            "success_message": "File deleted",
            "error_message": "Deletion error",
            "alt_code": 202,
            "alt_message": "Removing began"
        }
    }
    service_name = 'Yandex Drive'

    def __init__(self, folder_monitor: FolderMonitor, cloud_sync: CloudSync, logger_file: str):
        self.folder_monitor = folder_monitor
        self.cloud_sync = cloud_sync
        self.logger_file = logger_file
        self.setup_logging()

    def setup_logging(self):
        logger.add(f"{self.logger_file}", format="{time} {level} {message}", level="INFO")

    def handle_changes(self, changes: List[Tuple[str, str]]):
        for file_path, change_type in changes:
            try:
                action = self.action_map.get(change_type)
                if not action:
                    logger.warning(f"[{self.service_name}] Unknown change type: {change_type}")
                    continue

                logger.info(f"[{self.service_name}] Detected {change_type} file: {file_path}. Processing in cloud.")

                method = getattr(self.cloud_sync, action["method"])
                response = method(file_path)

                self._process_response(response, action, file_path)

            except Exception as e:
                logger.error(f"[{self.service_name}] Error handling {change_type} for {file_path}: {e}")

    def _process_response(self, response, action, file_path):
        if response.status_code == action["success_code"]:
            logger.info(f"[{self.service_name}] {action['success_message']} for {file_path}.")
        elif response.status_code == action.get("alt_code"):
            logger.info(f"[{self.service_name}] {action['alt_message']} for {file_path}.")
            operation_link = response.json().get("href")
            if operation_link:
                logger.info(f"[{self.service_name}] Link to check status for {file_path}: {operation_link}.")
        else:
            logger.info(
                f"[{self.service_name}] {action['error_message']} for {file_path}: {response.status_code}, {response.json()}.")

    def start(self):
        logger.info(f"[{self.service_name}] Starting folder monitoring and sync process.")
        self.folder_monitor.start_monitoring(self.handle_changes)

    def stop(self):
        logger.info(f"[{self.service_name}] Stopping folder monitoring and sync process.")
        self.folder_monitor.stop_monitoring()

