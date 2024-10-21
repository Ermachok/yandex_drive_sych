import os
import time
import logging


def get_folder_state(folder_path):
    """Возвращает текущее состояние папки в виде словаря: {файл: время изменения}"""
    folder_state = {}

    for root, dirs, files in os.walk(folder_path):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                file_mtime = os.path.getmtime(file_path)
                folder_state[file_path] = file_mtime
            except FileNotFoundError:

                continue

    return folder_state


def has_folder_changed(folder_path, previous_state=None):
    """Проверяет, изменилось ли содержимое папки на основе времени изменения файлов"""
    current_state = get_folder_state(folder_path)

    if previous_state is None:

        return False, current_state, []


    changed_files = []

    for file_path, mtime in previous_state.items():
        if file_path not in current_state:
            changed_files.append((file_path, "deleted"))
        elif current_state[file_path] != mtime:
            changed_files.append((file_path, "modified"))


    for file_path in current_state:
        if file_path not in previous_state:
            changed_files.append((file_path, "new"))

    has_changed = len(changed_files) > 0
    return has_changed, current_state, changed_files


def monitor_folder(folder_path, interval=10):
    """Отслеживает изменения в папке и логирует их"""
    logging.basicConfig(
        filename='folder_changes.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Monitoring: {folder_path}")

    previous_state = None

    while True:
        is_changed, new_state, changes = has_folder_changed(folder_path, previous_state)
        if is_changed:
            logging.info("There were changes::")
            for file, change_type in changes:
                logging.info(f"File {file} was {change_type}")
        else:
            logging.info("There were not any changes")

        previous_state = new_state

        time.sleep(interval)


folder_path = "/home/nikitaermakov/dev/synch_with_yandex_drive/test_dir"
monitor_folder(folder_path, interval=10)
