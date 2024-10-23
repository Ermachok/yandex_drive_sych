import requests
import os

class SyncManager:
    def __init__(self, cloud_service_name: str):
        self.cloud_service_name = cloud_service_name
        print(f"Connected to {cloud_service_name} cloud.")

    def sync_new_file(self, file_path: str):
        pass

    def sync_updated_file(self, file_path: str):
        pass

    def sync_deleted_file(self, file_path: str):
        pass

    def get_info(self, file_path: str):
        pass



class YandexDriveManager(SyncManager):
    def __init__(self, cloud_service_name: str, api_token: str, yandex_drive_folder: str):
        super().__init__(cloud_service_name)
        self.api_token = api_token
        self.yandex_folder = yandex_drive_folder

    def sync_new_file(self, file_path: str):
        upload_url_request = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

        file_name = os.path.basename(file_path)
        downloading_path = f'{self.yandex_folder}/{file_name}'

        params = {'path': downloading_path, 'overwrite': 'true'}
        headers = {'Authorization': f'OAuth {self.api_token}'}
        response = requests.get(upload_url_request, headers=headers, params=params)
        upload_link = response.json().get('href')

        with open(file_path, 'rb') as f:
            upload_response = requests.put(upload_link, files={'file': f})

        if upload_response.status_code == 201:
            print('Successfully downloaded')
        else:
            print(f'Download error: {upload_response.status_code}')
