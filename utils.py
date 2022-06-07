from json import JSONEncoder
from typing import Any


class RecursiveJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)
