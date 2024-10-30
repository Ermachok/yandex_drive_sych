from abc import ABC, abstractmethod

import requests
import os

from requests import Response
from typing import List, Dict


class CloudSync(ABC):
    def __init__(self, cloud_service_name: str):
        self.cloud_service_name = cloud_service_name
        print(f"Connected to {cloud_service_name} cloud.")

    @abstractmethod
    def load(self, file):
        pass

    @abstractmethod
    def reload(self, file_path: str):
        pass

    @abstractmethod
    def delete(self, file_name: str):
        pass

    @abstractmethod
    def get_info(self):
        pass


class YandexDriveCloud(CloudSync):
    """
    Manages file synchronization with Yandex Disk cloud storage, providing methods to upload, update,
    and delete files using Yandex Disk's REST API.
    """

    def __init__(self, cloud_service_name: str, api_token: str, yandex_drive_folder: str):
        """
        Initializes the YandexDriveCloud with the specified service name, API token, and folder path.

        Args:
            cloud_service_name (str): The name of the cloud service (e.g., 'Yandex Drive').
            api_token (str): The OAuth token for accessing Yandex Disk API.
            yandex_drive_folder (str): The Yandex Disk folder path where files will be synced.
        """
        super().__init__(cloud_service_name)
        self.api_token = api_token
        self.yandex_folder = yandex_drive_folder
        self.headers = {'Authorization': f'OAuth {self.api_token}'}
        self.api_url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def get_upload_url(self, file_path: str) -> str:
        """
        Retrieves a URL for uploading a file to Yandex Disk, allowing file overwrites.

        Args:
            file_path (str): The local path of the file to be uploaded.

        Returns:
            str: The upload link provided by Yandex Disk.
        """
        upload_url_request = f"{self.api_url}/upload"
        file_name = os.path.basename(file_path)
        downloading_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': downloading_path, 'overwrite': 'true'}
        response = requests.get(upload_url_request, headers=self.headers, params=params)
        upload_link = response.json().get('href')

        return upload_link

    def load(self, file_path: str) -> Response:
        """
        Uploads a new file to Yandex Disk using the generated upload URL.

        Args:
            file_path (str): The local path of the file to upload.

        Returns:
            Response: The HTTP response from the upload request.
        """
        upload_link = self.get_upload_url(file_path)
        with open(file_path, 'rb') as f:
            upload_response = requests.put(upload_link, files={'file': f})

        return upload_response

    def reload(self, file_path: str) -> Response:
        """
        Re-uploads or updates an existing file on Yandex Disk.

        Args:
            file_path (str): The local path of the file to update.

        Returns:
            Response: The HTTP response from the upload request.
        """
        return self.load(file_path)

    def delete(self, file_name: str) -> Response:
        """
        Deletes a specified file from Yandex Disk.

        Args:
            file_name (str): The name of the file to delete on Yandex Disk.

        Returns:
            Response: The HTTP response from the delete request.
        """
        deleting_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': deleting_path, 'permanently': 'True'}
        delete_response = requests.delete(self.api_url, headers=self.headers, params=params)

        return delete_response

    def get_info(self, limit: int = 100, offset: int = 0) -> list:
        """
        Retrieves all files from the specified folder on Yandex Disk in a paginated manner.

        Args:
            limit (int): Maximum number of files to retrieve in one request. Default is 100.
            offset (int): Number of files to skip from the beginning of the list. Default is 0.

        Returns:
            list: List of files' metadata from the specified folder.
        """
        all_files = []

        while True:
            params = {
                'path': self.yandex_folder,
                'limit': limit,
                'offset': offset,
                'fields': '_embedded.items.name,_embedded.items.path,_embedded.items.type'
            }
            response = requests.get(self.api_url, headers=self.headers, params=params)
            response.raise_for_status()

            files = response.json().get('_embedded', {}).get('items', [])
            all_files.extend(files)

            if len(files) < limit:
                break
            offset += limit

        return all_files

