from json import JSONEncoder
from pathlib import Path
from typing import Any


class RecursiveJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)

def project_root():
    return Path(__file__).parent
