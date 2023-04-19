import hashlib
import os
import time
from json import JSONEncoder
from pathlib import Path
from typing import Any

import psutil


class RecursiveJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)


def project_root():
    return Path(__file__).parent.parent


def open_anki():
    # Open Anki if it isn't open already.
    processes = [process.name() for process in psutil.process_iter()]
    # Anki has different name depending on what version, OS, etc.
    already_open = any(['anki' in process.lower() for process in processes])
    if not already_open:
        # Apparently this is best done in a subprocess. But this design is
        # temporary so I don't give a fook. Is also Mac specific.
        os.system("open /Applications/Anki.app")
        # Give it quite a few seconds to open
        time.sleep(20)
    return already_open


def close_anki():
    # If Anki is open, close it.
    processes = [process.name() for process in psutil.process_iter()]
    # Anki has different names depending on what version, OS, etc.
    anki_processes = [process for process in processes if 'anki' in process.lower()]
    is_open = False
    anki_process = None
    if len(anki_processes) == 1:
        is_open = True
        anki_process = anki_processes.pop()
    elif len(anki_processes) > 1:
        raise AssertionError("Multiple Anki instances running!?")
    if is_open:
        # Wait a few seconds in case any other processes need finishing.
        time.sleep(20)
        # subprocess.Popen("osascript -e 'quit app \"Anki\"'")
        # os.system("osascript -e 'quit app \"Anki\"'")
        os.system(f'pkill "{anki_process}"')
        # exit_response = self.connector.request('guiExitAnki')


def anki_id(string: str):
    # Want a hash that persists across all Python sessions - so Python's
    # built-in 'hash' function won't do. Also want it to be in the range
    # [2**30, 2**31) as per the genanki GitHub.
    n = (2 ** 30)
    string = string.encode(encoding='UTF-8', errors='strict')
    hashed = int(hashlib.md5(string).hexdigest(), 16)
    id = (hashed % n) + (2 ** 30)
    return id
