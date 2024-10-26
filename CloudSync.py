from abc import ABC, abstractmethod

import requests
import os

from requests import Response


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
    def delete(self, file_path: str):
        pass

    @abstractmethod
    def get_info(self):
        pass


class YandexDriveCloud(CloudSync):


    def __init__(self, cloud_service_name: str, api_token: str, yandex_drive_folder: str):
        super().__init__(cloud_service_name)
        self.api_token = api_token
        self.yandex_folder = yandex_drive_folder
        self.headers = {'Authorization': f'OAuth {self.api_token}'}

        self.api_url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def get_upload_url(self, file_path: str):
        upload_url_request = f"{self.api_url}/upload"

        file_name = os.path.basename(file_path)
        downloading_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': downloading_path, 'overwrite': 'true'}
        response = requests.get(upload_url_request, headers=self.headers, params=params)
        upload_link = response.json().get('href')

        return upload_link


    def load(self, file_path: str) -> Response:
        upload_link = self.get_upload_url(file_path)

        with open(file_path, 'rb') as f:
            upload_response = requests.put(upload_link, files={'file': f})

        return upload_response


    def reload(self, file_path: str) -> Response:
        return self.load(file_path)


    def delete(self, file_path: str) -> Response:
        file_name = os.path.basename(file_path)
        deleting_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': deleting_path, 'permanently': 'True'}

        delete_response = requests.delete(self.api_url, headers=self.headers, params=params)

        return delete_response


    def get_info(self):
        pass


    def get_info(self, path):
        """Get metadata"""
        params = {"path": path}
        response = requests.get(self.api_url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()