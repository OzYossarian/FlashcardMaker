from datetime import datetime
from pathlib import Path

from main.utils import project_root


def log(text: str, new_entry=False):
    if new_entry:
        now = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        log_text = f'\n\n{now}\n{text}'
    else:
        log_text = f'\n{text}'
    date = datetime.now().strftime('%Y_%m_%d')
    log_path = f'{project_root()}/logs/{date}.txt'
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as log_file:
        log_file.write(log_text)
