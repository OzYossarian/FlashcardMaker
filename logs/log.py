from datetime import datetime


def log(text: str, new_entry=False):
    if new_entry:
        now = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        log_text = f'\n\n{now}\n{text}'
    else:
        log_text = f'\n{text}'
    with open('logs/log.txt', 'a') as log_file:
        log_file.write(log_text)
