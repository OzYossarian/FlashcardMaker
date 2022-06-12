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
        # Give it a few seconds to open
        time.sleep(5)
    return already_open
