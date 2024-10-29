import os
from dotenv import load_dotenv

from CloudSync import YandexDriveCloud
from Controller import SyncYandexController
from FolderMonitor import FolderMonitor


if __name__ == '__main__':

    load_dotenv()
    TOKEN = os.getenv("YANDEX_TOKEN")
    USER_FOLDER = os.getenv("USER_DIRECTORY_ABSOLUTE_PATH")
    YANDEX_FOLDER = os.getenv("YANDEX_FOLDER")
    LOGGER_FILE = os.getenv("LOGGER_FILE")

    cloud_sync = YandexDriveCloud("Yandex Drive", api_token= TOKEN, yandex_drive_folder=YANDEX_FOLDER)
    folder_monitor = FolderMonitor(USER_FOLDER, interval = 5)
    controller = SyncYandexController(folder_monitor, cloud_sync, LOGGER_FILE)

    try:
        controller.start()
    except KeyboardInterrupt:
        controller.stop()
