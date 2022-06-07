from typing import Dict, Any


class Phrase:
    def __init__(
            self, id, german, english, owner, share_date, database_date,
            flashcard_date, translation):
        self.id = id
        self.german = german
        self.english = english
        self.owner = owner
        self.share_date = share_date
        self.database_date = database_date
        self.flashcard_date = flashcard_date
        self.translation = translation

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        return cls(
            data.get('_id', None),
            data.get('german', None),
            data.get('english', None),
            data.get('owner', None),
            data.get('share_date', None),
            data.get('database_date', None),
            data.get('flashcard_date', None),
            data.get('translation', None))
