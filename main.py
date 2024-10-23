import os
from dotenv import load_dotenv

from FolderMonitor import FolderMonitor
from SynchManager import YandexDriveManager


if __name__ == '__main__':

    load_dotenv()
    TOKEN = os.getenv("TOKEN")

    sync_manager = YandexDriveManager('YandexDrive',
                                      api_token = TOKEN,
                                      yandex_drive_folder='sync_test')

    folder_monitor = FolderMonitor(folder_path=os.getenv("USER_DIRECTORY_ABSOLUTE_PATH"),
                                   sync_manager=sync_manager,
                                   interval=60)

    folder_monitor.start_monitoring()
