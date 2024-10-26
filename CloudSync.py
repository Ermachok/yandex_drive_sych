from abc import ABC, abstractmethod

import requests
import os

from requests import Response


class CloudSync(ABC):
    def __init__(self, cloud_service_name: str):
        self.cloud_service_name = cloud_service_name
        print(f"Connected to {cloud_service_name} cloud.")

    @abstractmethod
    def sync_new_file(self, file):
        pass

    @abstractmethod
    def sync_updated_file(self, file_path: str):
        pass

    @abstractmethod
    def sync_deleted_file(self, file_path: str):
        pass

    @abstractmethod
    def get_info(self, file_path: str):
        pass


class YandexDriveCloud(CloudSync):


    def __init__(self, cloud_service_name: str, api_token: str, yandex_drive_folder: str):
        super().__init__(cloud_service_name)
        self.api_token = api_token
        self.yandex_folder = yandex_drive_folder

        self.api_url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def get_upload_url(self, file_path: str):
        upload_url_request = f"{self.api_url}/upload"

        file_name = os.path.basename(file_path)
        downloading_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': downloading_path, 'overwrite': 'true'}
        headers = {'Authorization': f'OAuth {self.api_token}'}
        response = requests.get(upload_url_request, headers=headers, params=params)
        upload_link = response.json().get('href')

        return upload_link


    def sync_new_file(self, file_path: str) -> Response:
        upload_link = self.get_upload_url(file_path)

        with open(file_path, 'rb') as f:
            upload_response = requests.put(upload_link, files={'file': f})

        return upload_response


    def sync_updated_file(self, file_path: str) -> Response:
        return self.sync_new_file(file_path)


    def sync_deleted_file(self, file_path: str) -> Response:
        file_name = os.path.basename(file_path)
        deleting_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': deleting_path, 'permanently': 'True'}
        headers = {'Authorization': f'OAuth {self.api_token}'}

        delete_response = requests.delete(self.api_url, headers=headers, params=params)

        return delete_response


    def get_info(self, file_path: str):
        pass
