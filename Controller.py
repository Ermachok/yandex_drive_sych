from typing import List, Tuple, Dict
from loguru import logger
from abc import ABC, abstractmethod
import os

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
    """
        Controls the synchronization process between a local folder and Yandex Disk cloud storage, managing file
        operations such as uploading, updating, and deleting based on detected changes in the local directory.
    """

    action_map = {
        "new": {
            "method": "load",
            "success_code": 201,
            "success_message": "File uploaded",
            "error_message": "Upload error"
        },
        "modified": {
            "method": "reload",
            "success_code": 201,
            "success_message": "Cloud updated",
            "error_message": "Update error"
        },
        "deleted": {
            "method": "delete",
            "success_code": 204,
            "success_message": "File deleted",
            "error_message": "Deletion error",
            "alt_code": 202,
            "alt_message": "Removing began"
        }
    }
    service_name = 'Yandex Drive'

    def __init__(self, folder_monitor: FolderMonitor, cloud_sync: CloudSync, logger_file: str):
        """
            Initializes the SyncYandexController instance with the specified folder monitor, cloud sync service, and
            logger file for recording sync operations.

            Args:
                folder_monitor (FolderMonitor): Instance responsible for monitoring changes in a local folder.
                cloud_sync (CloudSync): Instance responsible for interacting with Yandex Disk cloud storage.
                logger_file (str): Path to the log file where sync operations are recorded.
        """
        self.folder_monitor = folder_monitor
        self.cloud_sync = cloud_sync
        self.logger_file = logger_file
        self.setup_logging()

    def setup_logging(self):
        """
              Configures logging for the synchronization process, specifying the log file, message format, and
              logging level.
        """
        logger.add(f"{self.logger_file}", format="{time} {level} {message}", level="INFO")

    def handle_changes(self, changes: List[Tuple[str, str]]):
        """
              Processes detected changes in the local folder by determining the corresponding cloud action
              (upload, update, or delete) and executing it for each file.

              Args:
                  changes (List[Tuple[str, str]]): A list of tuples, each containing the file path and the type of change
                                                   ('new', 'modified', 'deleted').

              Logs:
                  - Logs a warning if an unknown change type is encountered.
                  - Logs the start of processing for each file change and the result (success, error, or alternative response).
        """
        for file_path, change_type in changes:
            try:
                action = self.action_map.get(change_type)
                if not action:
                    logger.warning(f"[{self.service_name}] Unknown change type: {change_type}")
                    continue

                logger.info(f"[{self.service_name}] Detected {change_type} file: {file_path}. Processing in cloud.")

                method = getattr(self.cloud_sync, action["method"])
                response = method(os.path.basename(file_path) if action["method"] == "delete" else file_path)

                self._process_response(response, action, file_path)

            except Exception as e:
                logger.error(f"[{self.service_name}] Error handling {change_type} for {file_path}: {e}")

    def start(self):
        """
              Starts monitoring the local folder for changes and initiates the initial synchronization with the cloud.

              Logs:
                  - Logs the beginning of the folder monitoring and sync process.
        """
        logger.info(f"[{self.service_name}] Starting folder monitoring and sync process.")
        self._sync_initial_state()
        self.folder_monitor.start_monitoring(self.handle_changes)

    def stop(self):
        """
              Stops the monitoring process for the local folder, ceasing further sync actions.

              Logs:
                  - Logs the stopping of the folder monitoring and sync process.
        """

        logger.info(f"[{self.service_name}] Stopping folder monitoring and sync process.")
        self.folder_monitor.stop_monitoring()

    def _process_response(self, response, action, file_path):
        """
               Processes the HTTP response from a cloud action and logs the outcome based on success, alternative, or error
               codes specified in the action map.

               Args:
                   response (Response): The HTTP response object from the cloud operation.
                   action (dict): The action details from the action_map, including success and error codes and messages.
                   file_path (str): The local path of the file being processed.

               Logs:
                   - Logs success, alternative success, or error messages for the file operation, along with response details.
                   - If an alternative success code is received, logs the link for checking operation status.
        """
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

    def _sync_initial_state(self):
        """
               Synchronizes the initial state of the local folder with Yandex Disk cloud storage, ensuring consistency
               by deleting any existing files in the cloud folder and uploading all files from the local folder.

               Logs:
                   - Logs the start of the initial sync process.
                   - Logs successful deletion and upload operations, as well as any errors encountered during the process.
                   - Logs completion of the initial synchronization.
        """
        logger.info(f"[{self.service_name}] Started initial synchronising process")

        drive_files: List[Dict] = self.cloud_sync.get_info()
        for file_dict in  drive_files:
            try:
                self.cloud_sync.delete(file_dict["name"])
            except Exception as e:
                logger.error(f"[{self.service_name}] Error cleaning for {file_dict["name"]} for"
                             f" {self.cloud_sync.cloud_service_name}: {e}")


        current_folder_files = self.folder_monitor.get_folder_state()
        for file_path in current_folder_files.keys():
            try:
                self.cloud_sync.load(file_path)
            except Exception as e:
                logger.error(f"[{self.service_name}] Error uploading for {file_path}: {e}")

        logger.info(f"[{self.service_name}] Files synchronised")